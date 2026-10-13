"""Open a page in Chrome and save the PDF it downloads."""

from collections.abc import Callable
from pathlib import Path

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.support import expected_conditions as expected
from selenium.webdriver.support.ui import WebDriverWait

CLICK_TIMEOUT_SECONDS = 15
DOWNLOAD_TIMEOUT_SECONDS = 30


def download_pdf(download_dir: Path, page_url: str, selector: str) -> Path:
    """Open the page, click the download control, and return the saved PDF."""
    download_dir.mkdir(parents=True, exist_ok=True)
    options = _chrome_options(download_dir)
    driver = webdriver.Chrome(options=options)
    try:
        _allow_downloads(driver, download_dir)
        driver.get(page_url)
        clickable = expected.element_to_be_clickable((By.CSS_SELECTOR, selector))
        WebDriverWait(driver, CLICK_TIMEOUT_SECONDS).until(clickable).click()
        return WebDriverWait(driver, DOWNLOAD_TIMEOUT_SECONDS).until(
            _saved_pdf(download_dir)
        )
    finally:
        driver.quit()


def _chrome_options(download_dir: Path) -> Options:
    """Point Chrome at the download directory and keep the PDF viewer closed."""
    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    # Chrome's PDF viewer has no DOM text, so the file must be saved to disk.
    options.add_experimental_option(
        "prefs",
        {
            "download.default_directory": str(download_dir.resolve()),
            "download.prompt_for_download": False,
            "download.directory_upgrade": True,
            "plugins.always_open_pdf_externally": True,
        },
    )
    return options


def _allow_downloads(driver: WebDriver, download_dir: Path) -> None:
    """Tell Chrome to write downloads into the pytest directory."""
    driver.execute_cdp_cmd(
        "Browser.setDownloadBehavior",
        {
            "behavior": "allow",
            "downloadPath": str(download_dir.resolve()),
            "eventsEnabled": True,
        },
    )


def _saved_pdf(download_dir: Path) -> Callable[[WebDriver], Path | bool]:
    """Wait until one PDF is present and its size has stopped changing."""
    previous_size: int | None = None

    def ready(_driver: WebDriver) -> Path | bool:
        nonlocal previous_size
        partials = list(download_dir.glob("*.crdownload"))
        pdfs = [
            path
            for path in download_dir.iterdir()
            if path.is_file() and path.suffix.lower() == ".pdf"
        ]
        if partials or len(pdfs) != 1:
            previous_size = None
            return False
        size = pdfs[0].stat().st_size
        if size <= 0:
            previous_size = None
            return False
        stable = previous_size == size
        previous_size = size
        return pdfs[0] if stable else False

    return ready
