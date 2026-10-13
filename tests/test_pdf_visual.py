"""Check the appearance of the downloaded PDF, not its text and not the embedded frame."""

import os
import sys
from pathlib import Path

import pypdfium2 as pdfium
import pytest
from PIL import Image, ImageChops
from playwright.sync_api import Page

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from config import PAGE_URL

RENDER_SCALE = 1
SNAPSHOTS = Path(__file__).with_name("test_pdf_visual.py-snapshots")
DIFFERENCE = SNAPSHOTS / "eamena-diff.png"


def test_downloaded_pdf_matches_baseline(page: Page, tmp_path: Path, pytestconfig) -> None:
    """Download the file from the page, render the saved copy, and compare it with the baseline image."""
    page.goto(PAGE_URL)
    pdf_url = page.locator("iframe[src$='.pdf']").get_attribute("src")
    assert pdf_url
    with page.expect_download() as download_info:
        page.evaluate(
            """(url) => {
              const link = document.createElement("a");
              link.href = url;
              link.download = "";
              document.body.appendChild(link);
              link.click();
            }""",
            pdf_url,
        )
    download = download_info.value
    saved = tmp_path / download.suggested_filename
    download.save_as(saved)
    _expect_image(
        _render_pdf(saved),
        "eamena-pdf.png",
        # About 2 percent of pixels may differ from antialiasing.
        max_diff_pixel_ratio=0.02,
        update=bool(pytestconfig.getoption("--update-snapshots")),
    )


def _render_pdf(path: Path) -> Image.Image:
    """Draw the saved PDF. Opening it in this browser would download it again."""
    document = pdfium.PdfDocument(path)
    pages = [document[index].render(scale=RENDER_SCALE).to_pil().convert("RGB") for index in range(len(document))]
    document.close()
    width = max(image.width for image in pages)
    height = sum(image.height for image in pages)
    canvas = Image.new("RGB", (width, height), "white")
    top = 0
    for image in pages:
        canvas.paste(image, (0, top))
        top += image.height
    return canvas


def _expect_image(current: Image.Image, name: str, max_diff_pixel_ratio: float, update: bool) -> None:
    """Save the picture when asked, otherwise compare it with the baseline."""
    SNAPSHOTS.mkdir(exist_ok=True)
    baseline = SNAPSHOTS / name
    if update:
        current.save(baseline)
        return
    assert baseline.exists(), f"No baseline at {baseline}. Run with --update-snapshots."
    expected = Image.open(baseline).convert("RGB")
    assert current.size == expected.size, (
        f"Image size {current.size} does not match the baseline {expected.size}."
    )
    difference = ImageChops.difference(current, expected).convert("L")
    changed = sum(difference.histogram()[1:])
    ratio = changed / (current.size[0] * current.size[1])
    _save_difference(expected, current, difference)
    assert ratio <= max_diff_pixel_ratio, (
        f"Image differs from the baseline on {ratio:.1%} of pixels. See {DIFFERENCE}."
    )


def _save_difference(expected: Image.Image, current: Image.Image, difference: Image.Image) -> None:
    """Write baseline, this run, and red changed pixels, then open that picture."""
    marked = current.copy()
    mask = difference.point(lambda value: 255 if value else 0)
    marked.paste(Image.new("RGB", current.size, (255, 0, 0)), mask=mask)
    panels = [_fit_width(image, 700) for image in (expected, current, marked)]
    gap = 12
    sheet = Image.new("RGB", (sum(panel.width for panel in panels) + gap * 2, panels[0].height), "white")
    left = 0
    for panel in panels:
        sheet.paste(panel, (left, 0))
        left += panel.width + gap
    DIFFERENCE.parent.mkdir(exist_ok=True)
    sheet.save(DIFFERENCE)
    if os.name == "nt":
        os.startfile(DIFFERENCE)  # noqa: S606


def _fit_width(image: Image.Image, width: int) -> Image.Image:
    """Shrink a tall poster so the comparison picture fits on screen."""
    height = max(1, int(image.height * (width / image.width)))
    return image.resize((width, height), Image.Resampling.LANCZOS)


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "--headed"]))
