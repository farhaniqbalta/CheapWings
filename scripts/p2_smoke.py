"""Offline process acceptance: real Uvicorn + separate worker + SQLite, worker restart.

Run from repo root with .venv/bin/python scripts/p2_smoke.py. Uses fake only.
"""

import json
import os
import socket
import subprocess
import sys
import tempfile
import time
from pathlib import Path

import httpx
from alembic import command
from alembic.config import Config


def main():
    with tempfile.TemporaryDirectory(prefix="cheapwings-p2-") as directory:
        db_url = f"sqlite:///{directory}/smoke.db"
        config = Config("backend/alembic.ini")
        config.attributes["database_url"] = db_url
        command.upgrade(config, "head")
        with socket.socket() as sock:
            sock.bind(("127.0.0.1", 0))
            port = sock.getsockname()[1]
        env = dict(
            os.environ,
            DATABASE_URL=db_url,
            ENABLED_PROVIDERS="fake",
            API_BIND_HOST="127.0.0.1",
            CHEAPWINGS_OWNER_TOKEN="",
        )
        processes = []
        with open(Path(directory) / "process.log", "w+") as log:

            def launch(*args):
                process = subprocess.Popen(
                    [sys.executable, *args], env=env, stdout=log, stderr=log
                )
                processes.append(process)
                return process

            def poll(url, predicate):
                for _ in range(200):
                    try:
                        response = client.get(url)
                        response.raise_for_status()
                        data = response.json()
                        if predicate(data):
                            return data
                    except httpx.TransportError:
                        pass
                    time.sleep(0.05)
                log.seek(0)
                raise RuntimeError("Timed out\n" + log.read())

            try:
                launch(
                    "-m",
                    "uvicorn",
                    "cheapwings.main:app",
                    "--host",
                    "127.0.0.1",
                    "--port",
                    str(port),
                )
                with httpx.Client(
                    base_url=f"http://127.0.0.1:{port}", timeout=3
                ) as client:
                    poll("/api/v1/health", lambda d: d["status"] == "ok")
                    # Three route/date pairs leave pending work after the first success.
                    from datetime import date, timedelta

                    start = date.today() + timedelta(days=10)
                    response = client.post(
                        "/api/v1/searches",
                        json={
                            "origins": ["MEL"],
                            "destinations": ["DPS"],
                            "departure_date_from": str(start),
                            "departure_date_through": str(start + timedelta(days=2)),
                            "display_currency": "IDR",
                        },
                    )
                    response.raise_for_status()
                    url = response.json()["job_status_url"]
                    worker = launch("-m", "cheapwings.worker")
                    before = poll(
                        url, lambda d: d["succeeded_provider_work_items"] >= 1
                    )
                    worker.kill()
                    worker.wait(timeout=5)
                    launch("-m", "cheapwings.worker")
                    after = poll(url, lambda d: d["status"] == "completed")
                    results = client.get(url + "/results").json()
                    assert before["succeeded_provider_work_items"] < 3
                    assert after["covered_route_date_combinations"] == 3
                    assert all(c["attempts"] == 1 for c in after["coverage"])
                    assert len(results["itineraries"]) == 3
                    assert sum(len(i["offers"]) for i in results["itineraries"]) == 6
                    print(
                        json.dumps(
                            {
                                "status": after["status"],
                                "worker_restarted": True,
                                "completed_before_restart": before[
                                    "succeeded_provider_work_items"
                                ],
                                "covered_after_restart": 3,
                                "distinct_offers": 6,
                                "all_prices": "SYNTHETIC-FIXTURE-NOT-A-REAL-FARE",
                            }
                        )
                    )
            finally:
                for process in processes:
                    if process.poll() is None:
                        process.terminate()
                for process in processes:
                    try:
                        process.wait(timeout=5)
                    except subprocess.TimeoutExpired:
                        process.kill()
                        process.wait()


if __name__ == "__main__":
    main()
