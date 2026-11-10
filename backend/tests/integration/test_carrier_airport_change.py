"""Synthetic payloads preserve the observed routing shape, never live quote claims."""

from copy import deepcopy
from dataclasses import replace
from datetime import date
from pathlib import Path

from test_worker import drain

from cheapwings.application.job_runner import JobRunner
from cheapwings.application.search_service import results_projection
from cheapwings.providers.common import json_payload
from cheapwings.providers.registry import Registration
from cheapwings.providers.skiplagged import SkiplaggedProvider
from cheapwings.providers.swoop import SwoopProvider
from cheapwings.storage.repository import Repository

FIXTURES = Path(__file__).parents[3] / "contracts/fixtures/provider"


def payload():
    original = json_payload((FIXTURES / "swoop_probe_20261109T123521Z.json").read_text())[
        "search_result"
    ]
    data = deepcopy(original)
    data["results"] = data["results"][:1]
    trip = data["results"][0]
    trip["selector"] = "SYNTHETIC-FIXTURE-NOT-A-REAL-FARE-airport-change"
    trip["price"] = 1000
    leg = trip["legs"][0]
    leg.update(origin="CGK", destination="CTS", date="2026-12-15")
    itin = leg["itinerary"]
    itin.update(
        departure_airport_code="CGK",
        arrival_airport_code="CTS",
        departure_date=[2026, 12, 15],
        arrival_date=[2026, 12, 15],
        departure_time=[6, 35],
        arrival_time=[20, 5],
        travel_time=690,
        stop_count=1,
        airline_names=["Japan Airlines"],
    )
    first, second = itin["segments"]
    first.update(
        airline="JL",
        airline_name="Japan Airlines",
        flight_number="720",
        operator="",
        departure_airport_code="CGK",
        arrival_airport_code="NRT",
        departure_date=[2026, 12, 15],
        arrival_date=[2026, 12, 15],
        departure_time=[6, 35],
        arrival_time=[16, 0],
    )
    second.update(
        airline="JL",
        airline_name="Japan Airlines",
        flight_number="529",
        operator="",
        departure_airport_code="HND",
        arrival_airport_code="CTS",
        departure_date=[2026, 12, 15],
        arrival_date=[2026, 12, 15],
        departure_time=[18, 30],
        arrival_time=[20, 5],
    )
    # Include a connected candidate to prove one surface connection doesn't roll back its siblings.
    connected = deepcopy(trip)
    connected["selector"] = "SYNTHETIC-FIXTURE-NOT-A-REAL-FARE-connected"
    connected["legs"][0]["itinerary"]["segments"][1]["departure_airport_code"] = "NRT"
    data["results"].append(connected)
    return data


def zones(code):
    return {"CGK": "Asia/Jakarta", "NRT": "Asia/Tokyo", "HND": "Asia/Tokyo", "CTS": "Asia/Tokyo"}[
        code
    ]


async def test_surface_change_and_carriers_survive_worker_storage_api(engine, query):
    async def search(_):
        return payload()

    provider = SwoopProvider(search_transport=search, zone_resolver=zones)
    registry = [Registration(provider, minimum_interval_seconds=0)]
    q = query.model_copy(
        update={
            "origins": ["CGK"],
            "destinations": ["CTS"],
            "departure_date_from": date(2026, 12, 15),
            "departure_date_through": date(2026, 12, 15),
        }
    )
    repo = Repository(engine)
    job = repo.create_job(q, registry, reprice_budget=0)
    await drain(JobRunner(repo, registry), repo, job.id)
    saved, work = repo.get_job(job.id)
    assert saved.status == "completed"
    assert work[0].status == "succeeded_results"
    assert work[0].result_count == 2
    assert work[0].last_error_code is None
    output = results_projection(repo, job.id, "lowest_advertised")
    assert len(output.itineraries) == 2
    changed = next(i for i in output.itineraries if i.airport_transfers)
    assert changed.carrier_names == ["Japan Airlines"]
    assert changed.segments[0].marketing_carrier_name == "Japan Airlines"
    assert changed.segments[1].flight_number == "529"
    assert changed.airport_transfers[0].from_airport == "NRT"
    assert changed.airport_transfers[0].to_airport == "HND"
    assert any("Airport change required: NRT → HND" in w for w in changed.offers[0].warnings)
    assert results_projection(repo, job.id, "best_checked").itineraries == []


async def test_skiplagged_names_stay_summary_metadata_without_invented_flights(engine, query):
    recorded = json_payload((FIXTURES / "skiplagged_probe_20261109T123430Z.json").read_text())[
        "search_structured_content"
    ]

    async def search(_):
        return recorded

    provider = SkiplaggedProvider(search)
    registry = [Registration(provider, minimum_interval_seconds=0)]
    q = query.model_copy(
        update={
            "destinations": ["DPS"],
            "departure_date_from": date(2026, 12, 16),
            "departure_date_through": date(2026, 12, 16),
        }
    )
    repo = Repository(engine)
    job = repo.create_job(q, registry)
    await drain(JobRunner(repo, registry), repo, job.id)
    output = results_projection(repo, job.id, "lowest_advertised")
    garuda = next(i for i in output.itineraries if "Garuda Indonesia" in i.carrier_names)
    assert garuda.identity_confidence == "insufficient_identity"
    assert garuda.segments == []
    assert garuda.airport_transfers == []


async def test_airport_change_never_claims_ground_cost_is_known_on_reprice(engine, query):
    from datetime import timedelta

    from test_p3 import CheckingFake

    from cheapwings.domain.itinerary import AirportTransfer
    from cheapwings.domain.offer import ComparisonStatus

    class AirportChangeProvider(CheckingFake):
        async def search(self, q):
            response = await super().search(q)
            first = replace(response.itineraries[0][0], destination="NRT")
            second = replace(
                first,
                ordinal=1,
                origin="HND",
                destination=q.destination,
                flight_number="200",
                depart_at=first.arrive_at + timedelta(hours=3),
                arrive_at=first.arrive_at + timedelta(hours=9),
            )
            return replace(
                response,
                itineraries=((first, second),),
                airport_transfers_by_itinerary_index=((AirportTransfer(0, "NRT", "HND"),),),
            )

        async def reprice(self, request):
            response = await super().reprice(request)
            return replace(
                response,
                offers=tuple(
                    replace(o, comparison_status=ComparisonStatus.ELIGIBLE_TOTAL_KNOWN)
                    for o in response.offers
                ),
            )

    reg = [Registration(AirportChangeProvider(), minimum_interval_seconds=0)]
    repo = Repository(engine)
    q = query.model_copy(
        update={"destinations": ["DPS"], "departure_date_through": query.departure_date_from}
    )
    job = repo.create_job(q, reg, reprice_budget=1)
    await drain(JobRunner(repo, reg), repo, job.id)
    data = results_projection(repo, job.id, "lowest_advertised")
    assert data.itineraries[0].airport_transfers
    assert all(o.comparison_status == "extra_cost_unknown" for o in data.itineraries[0].offers)
    assert all(o.price_status != "repriced_exact" for o in data.itineraries[0].offers)
    assert results_projection(repo, job.id, "best_checked").itineraries == []
