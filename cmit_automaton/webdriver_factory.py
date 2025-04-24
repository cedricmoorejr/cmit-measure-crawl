# -*- coding: utf-8 -*-


"""
Module
-------

Creates and Returns: a pre-configured Selenium WebDriver instance
for Chromium/Chrome.  Keeps all driver plumbing in one place so
scraper scripts can simply do:

    from webdriver_factory import get_driver
    driver = get_driver(headless=True)
"""
#────────── Base Python imports ──────────────────────────────────────────────────────────────────────────────
from pathlib import Path
import os
import logging
from typing import Optional, Union

#────────── Third-party library imports (from PyPI or other package sources) ─────────────────────────────────
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
import yaml

try:
    from webdriver_manager.chrome import ChromeDriverManager
    _HAS_WDM = True
except ModuleNotFoundError:
    _HAS_WDM = False


# Configuration helpers
# ---------------------------------------------------------------------------
def _load_settings() -> dict:
    """
    Loads project settings from settings.yaml, if it exists.
    """
    settings_path = Path("settings.yaml")
    if settings_path.exists():
        with settings_path.open("r") as f:
            return yaml.safe_load(f) or {}
    return {}


def _default_driver_path() -> Optional[Path]:
    """
    Return a Path to an existing chromedriver, or None if none found.
    Order of precedence:
    1.  CHROMEDRIVER_PATH env var
    2.  settings.yaml
    2.  fallback
    """
    # 1. Env var
    env_path = os.getenv("CHROMEDRIVER_PATH")
    if env_path and Path(env_path).exists():
        return Path(env_path)

    # 2. settings.yaml
    settings = _load_settings()
    settings_path = settings.get("chromedriver_path")
    if settings_path and Path(settings_path).exists():
        return Path(settings_path)

    # 3. Give up
    return None


def _build_options(headless: bool) -> Options:
    """
    Return a fully customised `Options` object.
    """
    opts = Options()

    if headless:
        opts.add_argument("--headless=new")  # new flag in Chrome ≥ 118
        opts.add_argument("--headless")      

    # Window & hardware
    opts.add_argument("--window-size=1920,1080")
    opts.add_argument("--disable-gpu")
    opts.add_argument("--no-sandbox")
    opts.add_argument("--disable-dev-shm-usage")

    # Performance / anti-detect
    opts.add_argument("--disable-background-networking")
    opts.add_argument("--disable-default-apps")
    opts.add_argument("--disable-logging")
    opts.add_argument("--disable-sync")
    opts.add_argument("--metrics-recording-only")
    opts.add_argument("--disable-component-update")
    opts.add_argument("--no-first-run")
    opts.add_argument("--disable-popup-blocking")
    opts.add_argument("--disable-extensions")
    opts.add_argument(
        "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/114.0.5735.199 Safari/537.36 Edge/114.0.1823.79"
    )

    # Reduce Selenium fingerprint
    opts.add_experimental_option("excludeSwitches", ["enable-automation"])
    opts.add_experimental_option("useAutomationExtension", False)

    return opts


# Public factory
# ---------------------------------------------------------------------------
def get_driver(*, headless: bool = True, driver_path: Optional[Union[str, os.PathLike]] = None) -> webdriver.Chrome:
    """
    Instantiate and return a configured `webdriver.Chrome`.

    If `driver_path` is not supplied and no executable is found,
    we fall back to Selenium Manager (selenium ≥ 4.6) or, if available,
    webdriver-manager for auto-download.
    """
    logging.getLogger("selenium").setLevel(logging.WARNING)
    options = _build_options(headless=headless)

    # Explicit argument wins
    if driver_path:
        service = Service(str(driver_path))
        return webdriver.Chrome(service=service, options=options)

    # Try default/local paths
    local_path = _default_driver_path()
    if local_path:
        service = Service(str(local_path))
        return webdriver.Chrome(service=service, options=options)

    # Selenium-manager (built into selenium ≥ 4.6)
    try:
        logging.info("No local chromedriver found — falling back to Selenium Manager.")
        return webdriver.Chrome(options=options)   # Service() with no exe path
    except Exception as sm_err:
        logging.warning(f"Selenium Manager failed: {sm_err}")

    # Webdriver-manager (optional dependency)
    if _HAS_WDM:
        logging.info("Attempting automatic download via webdriver-manager …")
        cdriver_path = ChromeDriverManager().install()
        service = Service(cdriver_path)
        return webdriver.Chrome(service=service, options=options)

    # 5) give up
    raise FileNotFoundError(
        "Unable to locate or download chromedriver.\n"
        "• Install it manually and set CHROMEDRIVER_PATH, or\n"
        "• `pip install webdriver-manager`, or\n"
        "• upgrade to selenium ≥ 4.6 so Selenium Manager can fetch it."
    )


# Context-manager for automatic teardown
# ---------------------------------------------------------------------------
class DriverContext:
    """
    Usage:
    ------
    with DriverContext(headless=True) as driver:
        driver.get("https://example.com")
        ...
    Automatically calls `driver.quit()` on exit.
    """

    def __init__(self, headless: bool = True, driver_path: Optional[Union[str, os.PathLike]] = None):
        self.headless = headless
        self.driver_path = driver_path
        self._driver: Optional[webdriver.Chrome] = None

    def __enter__(self) -> webdriver.Chrome:
        self._driver = get_driver(headless=self.headless, driver_path=self.driver_path)
        return self._driver

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self._driver:
            self._driver.quit()




__all__ = ["get_driver", "DriverContext"]
