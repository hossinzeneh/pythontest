"""Open a page in Chrome and save the PDF it downloads."""

import json
import urllib.error
import urllib.request
from collections.abc import Callable
from pathlib import Path

import websocket
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.support import expected_conditions as expected
from selenium.webdriver.support.ui import WebDriverWait

CLICK_TIMEOUT_SECONDS = 20
DOWNLOAD_TIMEOUT_SECONDS = 60
PDF_VIEWER_PATH = "mhjfbmdgcfjbbpaeojofohoefgiehjai/index.html"


def download_pdf(download_dir: Path, page_url: str, selector: str) -> Path:
    """Open the page, click Download, and return the saved PDF."""
    download_dir.mkdir(parents=True, exist_ok=True)
    driver = _start_chrome(download_dir)
    try:
        driver.get(page_url)
        WebDriverWait(driver, CLICK_TIMEOUT_SECONDS).until(
            expected.presence_of_element_located((By.CSS_SELECTOR, "iframe[src$='.pdf']"))
        )
        WebDriverWait(driver, CLICK_TIMEOUT_SECONDS).until(
            lambda browser: _click_download_button(browser, selector)
        )
        return WebDriverWait(driver, DOWNLOAD_TIMEOUT_SECONDS).until(
            _pdf_is_saved(download_dir)
        )
    finally:
        driver.quit()


def _start_chrome(download_dir: Path) -> WebDriver:
    """Start Chrome and save downloads into download_dir."""
    folder = str(download_dir.resolve())
    options = Options()
    options.add_argument("--remote-allow-origins=*")
    options.add_argument("--window-size=1400,1200")
    options.add_experimental_option(
        "prefs",
        {
            "download.default_directory": folder,
            "download.prompt_for_download": False,
            "download.directory_upgrade": True,
            # The Download button is inside the PDF viewer, so leave the viewer open and only click it.
            "plugins.always_open_pdf_externally": False,
        },
    )
    driver = webdriver.Chrome(options=options)
    driver.execute_cdp_cmd(
        "Browser.setDownloadBehavior",
        {"behavior": "allow", "downloadPath": folder, "eventsEnabled": True},
    )
    return driver


def _click_download_button(driver: WebDriver, selector: str) -> bool:
    """Click Download in the embedded viewer. A normal find cannot see that shadow root."""
    try:
        address = driver.capabilities["goog:chromeOptions"]["debuggerAddress"]
        with urllib.request.urlopen(f"http://{address}/json", timeout=5) as response:
            targets = json.load(response)
        viewer = next(item for item in targets if PDF_VIEWER_PATH in item.get("url", ""))
        socket = websocket.create_connection(
            viewer["webSocketDebuggerUrl"],
            timeout=10,
            suppress_origin=True,
        )
        try:
            socket.send(
                json.dumps(
                    {
                        "id": 1,
                        "method": "Runtime.evaluate",
                        "params": {
                            "expression": _click_script(selector),
                            "returnByValue": True,
                        },
                    }
                )
            )
            payload = json.loads(socket.recv())
        finally:
            socket.close()
    except (
        StopIteration,
        OSError,
        KeyError,
        json.JSONDecodeError,
        websocket.WebSocketException,
        urllib.error.URLError,
    ):
        return False

    value = payload.get("result", {}).get("result", {}).get("value")
    return value == "clicked"


def _click_script(selector: str) -> str:
    """Return a script that walks open shadow roots and clicks selector."""
    selector_js = json.dumps(selector)
    return f"""(() => {{
      function find(root) {{
        if (!root || !root.querySelector) return null;
        const direct = root.querySelector({selector_js});
        if (direct) return direct;
        for (const el of root.querySelectorAll("*")) {{
          if (el.shadowRoot) {{
            const found = find(el.shadowRoot);
            if (found) return found;
          }}
        }}
        return null;
      }}
      const button = find(document);
      if (!button) return "missing";
      button.click();
      return "clicked";
    }})()"""


def _pdf_is_saved(download_dir: Path) -> Callable[[WebDriver], Path | bool]:
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
