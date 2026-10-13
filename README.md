# PDF download test

python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt

Chrome must be installed. Defaults serve the local sample and click #download-pdf. Override with:

$env:PDF_PAGE_URL = "https://example.com/docs"
$env:PDF_DOWNLOAD_SELECTOR = "#download-pdf"
$env:PDF_EXPECTED_TEXT = "tests/fixtures/expected.txt"

pytest

Selenium only opens the page and clicks the control so Chrome writes the PDF to disk. The built-in PDF viewer has no text Selenium can read, so that viewer stays closed. pypdf opens the saved file, and the test compares that text with the fixture.
