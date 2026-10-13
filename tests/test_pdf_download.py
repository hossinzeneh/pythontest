"""Compare a downloaded PDF with the expected text fixture."""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from config import DOWNLOAD_SELECTOR, EXPECTED_TEXT_PATH, PAGE_URL
from page import download_pdf
from pdf_text import extract_pdf_text, normalize_text


def test_downloaded_pdf_matches_expected_text(tmp_path: Path) -> None:
    """Download the PDF and compare its text with the fixture."""
    saved = download_pdf(tmp_path, PAGE_URL, DOWNLOAD_SELECTOR)
    actual = normalize_text(extract_pdf_text(saved))
    expected = normalize_text(EXPECTED_TEXT_PATH.read_text(encoding="utf-8"))
    assert actual == expected, (
        "PDF text does not match the fixture.\n"
        f"--- expected ---\n{expected}\n"
        f"--- actual ---\n{actual}"
    )


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__]))
