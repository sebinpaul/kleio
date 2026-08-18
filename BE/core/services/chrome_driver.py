"""Shared Chrome / undetected-chromedriver factory for the scraping services.

Left to itself, undetected-chromedriver downloads a chromedriver at runtime and
patches one shared binary under XDG_DATA_HOME. Two services starting at once
then unlink/rename/execute the same file, and the download endpoint it uses
tops out at Chrome 114. Both problems disappear when every service patches its
own copy of a prebuilt driver (CHROMEDRIVER_PATH) that matches the browser.
"""

from __future__ import annotations

import logging
import os
import re
import shutil
import subprocess
import threading
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)

# Driver creation is serialised: undetected-chromedriver patches the driver
# binary in place, and Chrome startup itself is not thread safe here.
_CREATE_LOCK = threading.Lock()

_CHROME_CANDIDATES = (
    "/usr/bin/google-chrome",
    "/usr/bin/google-chrome-stable",
    "/usr/bin/chromium",
    "/usr/bin/chromium-browser",
    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
)

_USER_AGENT = (
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"
)


def chrome_binary_path() -> Optional[str]:
    explicit = os.getenv("CHROME_BIN") or os.getenv("CHROME_PATH")
    if explicit:
        return explicit
    for candidate in _CHROME_CANDIDATES:
        if os.path.exists(candidate):
            return candidate
    return None


def chrome_major_version() -> Optional[int]:
    binary = chrome_binary_path()
    if not binary:
        return None
    try:
        result = subprocess.run(
            [binary, "--version"], capture_output=True, text=True, timeout=15
        )
    except Exception:
        logger.debug("Could not read Chrome version from %s", binary, exc_info=True)
        return None
    if result.returncode != 0:
        return None
    match = re.search(r"(\d+)", result.stdout or result.stderr or "")
    return int(match.group(1)) if match else None


def _driver_cache_dir() -> str:
    base = os.getenv("CHROMEDRIVER_CACHE_DIR")
    if base:
        return base
    data_home = os.getenv("XDG_DATA_HOME") or os.path.expanduser("~/.local/share")
    return os.path.join(data_home, "kleio-drivers")


def _staged_driver(profile: str, chrome_version: Optional[int]) -> Optional[str]:
    """Give each service its own copy of the prebuilt driver to patch."""
    source = os.getenv("CHROMEDRIVER_PATH")
    if not source or not os.path.exists(source):
        return None

    # Keying on the browser version means a driver left over from an older
    # image is never reused against a newer Chrome.
    suffix = chrome_version if chrome_version is not None else "unknown"
    target = os.path.join(_driver_cache_dir(), f"chromedriver-{profile}-{suffix}")
    if os.path.exists(target):
        return target

    try:
        os.makedirs(_driver_cache_dir(), exist_ok=True)
        # Copy then rename so a reader never sees a half-written binary.
        staging = f"{target}.{os.getpid()}.tmp"
        shutil.copy2(source, staging)
        os.chmod(staging, 0o755)
        os.replace(staging, target)
        logger.info("Staged chromedriver for %s at %s", profile, target)
        return target
    except Exception:
        logger.warning(
            "Could not stage a chromedriver copy for %s; "
            "falling back to undetected-chromedriver's own download",
            profile,
            exc_info=True,
        )
        return None


def create_driver(
    profile: str,
    *,
    headless: bool = True,
    user_data_dir: Optional[str] = None,
    page_load_timeout: int = 30,
):
    """Create an undetected-chromedriver Chrome for a named service profile."""
    import undetected_chromedriver as uc

    options = uc.ChromeOptions()
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--disable-infobars")
    options.add_argument("--disable-extensions")
    options.add_argument("--window-size=1920,1080")
    options.add_argument(f"--user-agent={_USER_AGENT}")

    # Headless and the profile dir are passed as kwargs, not arguments:
    # undetected-chromedriver rewrites options.arguments in place and drops
    # entries when it strips a --headless flag it finds there.
    kwargs: Dict[str, Any] = {"options": options, "headless": headless}
    if user_data_dir:
        os.makedirs(user_data_dir, exist_ok=True)
        kwargs["user_data_dir"] = user_data_dir

    browser_path = chrome_binary_path()
    if browser_path:
        kwargs["browser_executable_path"] = browser_path

    chrome_version = chrome_major_version()
    if chrome_version:
        kwargs["version_main"] = chrome_version

    with _CREATE_LOCK:
        driver_path = _staged_driver(profile, chrome_version)
        if driver_path:
            kwargs["driver_executable_path"] = driver_path
        driver = uc.Chrome(**kwargs)

    driver.set_page_load_timeout(page_load_timeout)
    return driver
