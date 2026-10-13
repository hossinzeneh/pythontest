"""Page URL, download selector, and expected-text path. No secrets."""

import os
from pathlib import Path

PAGE_URL: str = os.environ.get("PDF_PAGE_URL", "")
DOWNLOAD_SELECTOR: str = os.environ.get("PDF_DOWNLOAD_SELECTOR", "#download-pdf")
EXPECTED_TEXT_PATH: Path = Path(
    os.environ.get("PDF_EXPECTED_TEXT", "tests/fixtures/expected.txt")
)
