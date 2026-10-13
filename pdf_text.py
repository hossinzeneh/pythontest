"""Read text from a downloaded PDF."""

from pathlib import Path

from pypdf import PdfReader


def extract_pdf_text(path: Path) -> str:
    """Return the text pypdf reads from the PDF."""
    reader = PdfReader(path)
    return "\n".join(page.extract_text() or "" for page in reader.pages)


def normalize_text(text: str) -> str:
    """Strip, collapse whitespace, and use the same newlines on both sides."""
    unified = text.replace("\r\n", "\n").replace("\r", "\n")
    lines = [" ".join(line.split()) for line in unified.split("\n")]
    return "\n".join(line for line in lines if line).strip()
