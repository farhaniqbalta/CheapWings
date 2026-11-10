"""Offline verification of response-span timing and the cross-session HTTP gate."""

import asyncio
import importlib
from contextlib import ExitStack

import pytest
from p48_throughput import CURRENT, Experiment


@pytest.mark.parametrize("module_name", ["httpx", "httpx2"])
@pytest.mark.asyncio
async def test_response_timing_preserves_stream_bytes(tmp_path, module_name):
    module = importlib.import_module(module_name)

    class Stream(module.AsyncByteStream):
        async def __aiter__(self):
            yield b"abc"
            await asyncio.sleep(0.01)
            yield b"def"

    async def respond(request):
        return module.Response(200, stream=Stream())

    experiment = Experiment(tmp_path / "unused.jsonl")
    row = {"provider": "skiplagged", "http": []}
    token = CURRENT.set(row)
    try:
        with ExitStack() as stack:
            experiment.instrument(stack)
            async with (
                module.AsyncClient(transport=module.MockTransport(respond)) as client,
                client.stream(
                    "POST",
                    "https://provider.invalid/mcp",
                    json={"method": "tools/call"},
                ) as response,
            ):
                assert "body_end" not in row["http"][0]
                assert await response.aread() == b"abcdef"
                timing = row["http"][0]
                assert timing["start"] <= timing["headers_at"] <= timing["body_end"]
                assert timing["body_complete"] is True
    finally:
        CURRENT.reset(token)


@pytest.mark.asyncio
async def test_octotrip_three_sessions_share_one_http_gate(tmp_path):
    import httpx

    async def respond(request):
        return httpx.Response(200, content=b"ok")

    experiment = Experiment(tmp_path / "unused.jsonl")
    rows = [{"provider": "octotrip", "http": []} for _ in range(3)]

    async def session(row):
        token = CURRENT.set(row)
        try:
            async with httpx.AsyncClient(
                transport=httpx.MockTransport(respond)
            ) as client:
                await client.post(
                    "https://provider.invalid/mcp", json={"method": "initialize"}
                )
        finally:
            CURRENT.reset(token)

    with ExitStack() as stack:
        experiment.instrument(stack)
        await asyncio.gather(*(session(row) for row in rows))
    starts = sorted(row["http"][0]["start"] for row in rows)
    assert starts[1] - starts[0] >= 1.10
    assert starts[2] - starts[1] >= 1.10
