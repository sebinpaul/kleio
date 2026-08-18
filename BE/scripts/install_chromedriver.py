#!/usr/bin/env python3
"""Install a chromedriver matching the installed Chrome. Build-time only.

undetected-chromedriver fetches drivers from the pre-115 endpoint, so it always
lands on ChromeDriver 114 and cannot drive a current Chrome. Baking a matching
driver into the image also keeps the worker off the network at startup.
"""

from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import urllib.request
import zipfile

PLATFORM = "linux64"
TARGET_DIR = os.environ.get("CHROMEDRIVER_DIR", "/opt/chromedriver")
LATEST_PER_BUILD = (
    "https://googlechromelabs.github.io/chrome-for-testing/"
    "latest-patch-versions-per-build-with-downloads.json"
)
LATEST_PER_MILESTONE = (
    "https://googlechromelabs.github.io/chrome-for-testing/"
    "latest-versions-per-milestone-with-downloads.json"
)


def chrome_version() -> str:
    binary = os.environ.get("CHROME_BIN") or "/usr/bin/google-chrome"
    output = subprocess.run(
        [binary, "--version"], capture_output=True, text=True, check=True
    ).stdout
    match = re.search(r"(\d+\.\d+\.\d+\.\d+)", output)
    if not match:
        raise RuntimeError(f"Could not parse Chrome version from {output!r}")
    return match.group(1)


def fetch_json(url: str) -> dict:
    with urllib.request.urlopen(url, timeout=60) as response:
        return json.loads(response.read().decode())


def pick_url(downloads: list) -> str | None:
    for item in downloads:
        if item.get("platform") == PLATFORM:
            return item["url"]
    return None


def driver_url(version: str) -> str:
    build = ".".join(version.split(".")[:3])
    milestone = version.split(".")[0]

    try:
        entry = fetch_json(LATEST_PER_BUILD).get("builds", {}).get(build, {})
        url = pick_url(entry.get("downloads", {}).get("chromedriver", []))
        if url:
            return url
    except Exception as exc:
        print(f"per-build lookup failed: {exc}", file=sys.stderr)

    # A brand new Chrome build may not have its own driver yet; the milestone
    # driver speaks the same protocol.
    entry = fetch_json(LATEST_PER_MILESTONE).get("milestones", {}).get(milestone, {})
    url = pick_url(entry.get("downloads", {}).get("chromedriver", []))
    if url:
        return url

    raise RuntimeError(f"No chromedriver download published for Chrome {version}")


def main() -> int:
    version = chrome_version()
    url = driver_url(version)
    print(f"Chrome {version} -> {url}")

    os.makedirs(TARGET_DIR, exist_ok=True)
    target = os.path.join(TARGET_DIR, "chromedriver")

    with tempfile.TemporaryDirectory() as tmp:
        archive = os.path.join(tmp, "chromedriver.zip")
        urllib.request.urlretrieve(url, archive)
        with zipfile.ZipFile(archive) as zf:
            member = next(
                name
                for name in zf.namelist()
                if name.endswith("/chromedriver") or name == "chromedriver"
            )
            zf.extract(member, tmp)
            shutil.move(os.path.join(tmp, member), target)

    os.chmod(target, 0o755)

    installed = subprocess.run(
        [target, "--version"], capture_output=True, text=True, check=True
    ).stdout.strip()
    print(f"Installed {installed}")

    if installed.split()[1].split(".")[0] != version.split(".")[0]:
        raise RuntimeError(
            f"Driver/browser major mismatch: {installed!r} vs Chrome {version}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
