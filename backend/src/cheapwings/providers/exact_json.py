"""Capture exact MCP JSON numeric lexemes before SDK Any fields become binary floats.

Capture is ephemeral, bounded and never logged/persisted. The SDK still owns MCP
sessions/protocol; this observes HTTP JSON/SSE bytes without changing them.
"""
from cheapwings.domain.evidence import ProviderFailure
from cheapwings.providers.common import json_payload


class ExactCapture:
    def __init__(self):
        self.buffer = b''
        self.result = None

    def capture(self, data):
        try:
            obj = json_payload(data)
        except ValueError:
            return
        result = obj.get('result', {}) if isinstance(obj, dict) else {}
        content = result.get('structuredContent') if isinstance(result, dict) else None
        if isinstance(content, dict) and 'flights' in content:
            self.result = content

    def feed(self, data):
        self.buffer += data
        if len(self.buffer) > 4 * 1024 * 1024:
            raise ProviderFailure('partial_payload')
        while b'\n\n' in self.buffer:
            event, self.buffer = self.buffer.split(b'\n\n', 1)
            lines = [line[5:].lstrip() for line in event.splitlines() if line.startswith(b'data:')]
            if lines:
                self.capture(b'\n'.join(lines))


def exact_http_client(capture):
    import httpx2

    class ObservedStream(httpx2.AsyncByteStream):
        def __init__(self, stream):
            self.stream = stream
            self.tail = b''

        async def __aiter__(self):
            async for data in self.stream:
                # Normalize CRLF for parsing even when the CR/LF crosses chunks.
                normalized = (self.tail + data).replace(b'\r\n', b'\n')
                self.tail = b'\r' if normalized.endswith(b'\r') else b''
                capture.feed(normalized[:-1] if self.tail else normalized)
                yield data

        async def aclose(self):
            await self.stream.aclose()

    async def observe(response):
        if response.status_code == 429:
            from cheapwings.providers.rate_limit import retry_after

            raise ProviderFailure(
                'http_rate_limited', retry_after(response.headers.get('Retry-After'))
            )
        kind = response.headers.get('content-type', '')
        if 'application/json' in kind:
            capture.capture(await response.aread())
        elif 'text/event-stream' in kind:
            response.stream = ObservedStream(response.stream)

    return httpx2.AsyncClient(timeout=25, follow_redirects=False, event_hooks={'response': [observe]})
