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
import json
import urllib.request
import zipfile
import shutil
import tempfile

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

_SETTINGS_FILE = Path("settings.yaml")


# Custom quoted string
class QuotedString(str):
    pass

def quoted_str_representer(dumper, data):
    return dumper.represent_scalar('tag:yaml.org,2002:str', data, style='"')

yaml.add_representer(QuotedString, quoted_str_representer)



# Configuration helpers
# ---------------------------------------------------------------------------
# def _latest_stable_driver() -> str:
#     """
#     Return the latest 'Stable' chromedriver version string
#     from Google's last-known-good-versions JSON.
#     """
#     url = (
#         "https://googlechromelabs.github.io/chrome-for-testing/"
#         "last-known-good-versions.json"
#     )
#     with urllib.request.urlopen(url, timeout=10) as resp:
#         meta = json.load(resp)
#     return meta["channels"]["Stable"]["version"]

def _download_stable_from_lkgd() -> Path:
    """
    Download the latest Stable chromedriver for Windows (64-bit if possible)
    using Google's last-known-good-versions-with-downloads.json.

    Returns
    -------
    Path : full path to the extracted chromedriver.exe
    """
    LKGD_URL = (
        "https://googlechromelabs.github.io/chrome-for-testing/"
        "last-known-good-versions-with-downloads.json"
    )

    # 1) fetch JSON
    with urllib.request.urlopen(LKGD_URL, timeout=10) as resp:
        data = json.load(resp)

    stable = data["channels"]["Stable"]
    version = stable["version"]

    # 2) pick win64 or win32 download URL
    dl_list = stable["downloads"]["chromedriver"]
    win_url = None
    for plat in ("win64", "win32"):
        match = next((d for d in dl_list if d["platform"] == plat), None)
        if match:
            win_url = match["url"]
            break
    if not win_url:
        raise RuntimeError("No Windows chromedriver link found in LKGD JSON")

    # 3) download to temp file
    tmp_dir = Path(tempfile.mkdtemp(prefix="chromedriver_lkgd_"))
    zip_path = tmp_dir / "driver.zip"
    urllib.request.urlretrieve(win_url, zip_path)

    # 4) extract chromedriver to cache folder
    cache_dir = Path.home() / ".cache" / "chromedriver" / version
    cache_dir.mkdir(parents=True, exist_ok=True)

    with zipfile.ZipFile(zip_path) as zf:
        # archive contains e.g. chromedriver.exe and LICENSE.chromedriver
        for member in zf.namelist():
            if member.endswith("chromedriver.exe"):
                zf.extract(member, cache_dir)
                extracted = cache_dir / member
                final_path = cache_dir / "chromedriver.exe"
                shutil.move(extracted, final_path)
                break

    shutil.rmtree(tmp_dir, ignore_errors=True)
    return final_path

def _load_settings() -> dict:
    """
    Loads project settings from settings.yaml, if it exists.
    """
    if _settings := (_SETTINGS_FILE.read_text() if _SETTINGS_FILE.exists() else ""):
        return yaml.safe_load(_settings) or {}
    return {}

def _write_settings(settings: dict) -> None:
    """
    Writes the given settings dictionary to settings.yaml in YAML format.
    """
    # _SETTINGS_FILE.write_text(
    #     yaml.safe_dump(settings, sort_keys=False, default_flow_style=False)
    # )
    # Write back to YAML file with explicit quoting
    with open(_SETTINGS_FILE, 'w') as file:
        yaml.dump(settings, file, sort_keys=False, default_flow_style=False)    

def _update_yaml_if_needed(new_path: Union[str, Path]) -> None:
    """
    Persist *new_path* to settings.yaml if it's different.
    """
    new_path = str(new_path)
    cfg = _load_settings()
    if cfg.get("chromedriver_path") != new_path:
        cfg["chromedriver_path"] = new_path
        
        # Normalize path to POSIX style (forward slashes)
        normalized_path = Path(cfg["chromedriver_path"]).as_posix()

        # Explicitly wrap in custom quoted type
        cfg['chromedriver_path'] = QuotedString(normalized_path)        
        
        _write_settings(cfg)
        logging.info("Updated settings.yaml with new chromedriver path.")

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

    # 1 ─ explicit argument
    if driver_path:
        drv = webdriver.Chrome(service=Service(str(driver_path)), options=options)
        _update_yaml_if_needed(driver_path)
        return drv

    # 2 ─ settings.yaml
    settings_path = _load_settings().get("chromedriver_path")
    if settings_path:
        p = Path(settings_path)
        if p.is_file():
            return webdriver.Chrome(service=Service(p), options=options)
        else:
            logging.warning("chromedriver_path in settings.yaml is not a file: %s", p)

    # 3 ─ env var
    env_path = os.getenv("CHROMEDRIVER_PATH")
    if env_path and Path(env_path).exists():
        return webdriver.Chrome(service=Service(env_path), options=options)

    # 4 ─ Selenium Manager (built into selenium >=4.6)
    try:
        driver = webdriver.Chrome(options=options)        # auto-resolves driver
        _update_yaml_if_needed(driver.service.path)
        return driver
    except Exception as sm_err:
        logging.warning("Selenium Manager failed: %s", sm_err)

    # 5 ─ webdriver-manager as last resort
    if _HAS_WDM:
        try:
            logging.info("Downloading chromedriver via webdriver-manager …")
            wd_path = ChromeDriverManager().install()
        except ValueError as e:
            logging.warning("Exact driver unavailable (%s). Falling back to LKGD JSON …", e)
            try:
                wd_path = _download_stable_from_lkgd()
                if wd_path:
                    wd_path = str(wd_path)                
                logging.info("Downloaded Stable chromedriver → %s", wd_path)
            except Exception as lkgd_err:
                logging.warning("LKGD download failed: %s", lkgd_err)
                wd_path = None

        if wd_path:
            _update_yaml_if_needed(wd_path)
            return webdriver.Chrome(service=Service(str(wd_path)), options=options)   

    # 6) give up
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
