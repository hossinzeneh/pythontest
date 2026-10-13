# PDF download test

python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt

Chrome must be installed. The test opens the embedded PDF page and clicks the viewer Download button. Override with:

$env:PDF_PAGE_URL = "https://eamena.org/embedded-pdf-test"
$env:PDF_DOWNLOAD_SELECTOR = "cr-icon-button#save[aria-label=Download]"
$env:PDF_EXPECTED_TEXT = "tests/fixtures/expected.txt"

pytest

Selenium only opens the page and clicks Download so Chrome writes the PDF to disk. That button sits in Chrome's PDF viewer, which has no text Selenium can read. pypdf opens the saved file, and the test compares that text with the fixture.
