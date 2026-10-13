"""Compare a downloaded PDF with the expected text fixture."""

from pathlib import Path

from config import DOWNLOAD_SELECTOR, EXPECTED_TEXT_PATH
from page import download_pdf
from pdf_text import extract_pdf_text, normalize_text


def test_downloaded_pdf_matches_expected_text(tmp_path: Path, page_url: str) -> None:
    """Download the PDF and compare its text with the fixture."""
    saved = download_pdf(tmp_path, page_url, DOWNLOAD_SELECTOR)
    actual = normalize_text(extract_pdf_text(saved))
    expected = normalize_text(EXPECTED_TEXT_PATH.read_text(encoding="utf-8"))
    assert actual == expected, (
        "PDF text does not match the fixture.\n"
        f"--- expected ---\n{expected}\n"
        f"--- actual ---\n{actual}"
    )
