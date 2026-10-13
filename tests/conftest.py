"""Serve the local sample page when no URL is configured."""

import threading
from collections.abc import Iterator
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

import pytest

from config import PAGE_URL

FIXTURES_DIR = Path(__file__).parent / "fixtures"


class _QuietHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, directory=str(FIXTURES_DIR), **kwargs)

    def log_message(self, format: str, *args) -> None:
        return


@pytest.fixture
def page_url() -> Iterator[str]:
    """Yield the configured page, or a local sample page when no URL is set."""
    if PAGE_URL:
        yield PAGE_URL
        return

    server = ThreadingHTTPServer(("127.0.0.1", 0), _QuietHandler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    host, port = server.server_address
    try:
        yield f"http://{host}:{port}/page.html"
    finally:
        server.shutdown()
        thread.join(timeout=5)
