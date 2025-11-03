import json
import math
import os
import random
import time

import requests
from loguru import logger
from patchright.sync_api import Locator

ADSPOWER_API_URL = "http://172.17.0.1:50325"


def start_browser(profile_number: str, headless: bool = False) -> str | None:
    launch_args = [
        "--disable-blink-features=AutomationControlled",
        "--disable-popup-blocking",
        "--disable-default-apps",
        "--disable-translate",
        "--disable-features=TranslateUI",
    ]

    params = {
        "serial_number": profile_number,
        "launch_args": json.dumps(launch_args),
        "open_tabs": 1,
    }
    if headless:
        params["headless"] = 1

    try:
        response = requests.get(
            f"{ADSPOWER_API_URL}/api/v1/browser/start", params=params
        )
        logger.debug(f"[start_browser] Raw response: {response.text}")
        response.raise_for_status()
        data = response.json()

        if data.get("code") == 0:
            puppeteer_ws = data["data"]["ws"]["puppeteer"]
            logger.success(
                f"[start_browser] Browser started for profile {profile_number}"
            )
            return puppeteer_ws
        else:
            logger.error(
                f"[start_browser] Failed to start browser for profile {profile_number}: {data.get('msg')}"
            )
            return None

    except requests.exceptions.RequestException as e:
        logger.exception(
            f"[start_browser] Request error for profile {profile_number}: {e}"
        )
        return None


def check_browser_status(profile_number: str) -> bool:
    try:
        response = requests.get(
            f"{ADSPOWER_API_URL}/api/v1/browser/active",
            params={"serial_number": profile_number},
        )
        logger.debug(f"[check_browser_status] Raw response: {response.text}")
        response.raise_for_status()
        data = response.json()

        if data.get("code") == 0 and data["data"]["status"] == "Active":
            logger.info(
                f"[check_browser_status] Browser is active for profile {profile_number}"
            )
            return True
        else:
            logger.warning(
                f"[check_browser_status] Browser is NOT active for profile {profile_number}"
            )
            return False

    except requests.exceptions.RequestException as e:
        logger.exception(
            f"[check_browser_status] Request error for profile {profile_number}: {e}"
        )
        return False


def close_browser(profile_number: str) -> bool:
    try:
        response = requests.get(
            f"{ADSPOWER_API_URL}/api/v1/browser/stop",
            params={"serial_number": profile_number},
        )
        logger.debug(f"[close_browser] Raw response: {response.text}")
        response.raise_for_status()
        data = response.json()

        if data.get("code") == 0:
            logger.success(
                f"[close_browser] Browser closed for profile {profile_number}"
            )
            return True
        else:
            logger.error(
                f"[close_browser] Failed to close browser for profile {profile_number}: {data.get('msg')}"
            )
            return False

    except requests.exceptions.RequestException as e:
        logger.exception(
            f"[close_browser] Request error for profile {profile_number}: {e}"
        )
        return False


def load_profiles(file_name: str = "profiles.txt") -> list[str]:
    base_dir = os.path.dirname(os.path.abspath(__file__))
    file_path = os.path.join(base_dir, file_name)
    with open(file_path, "r", encoding="utf-8") as f:
        return [line.strip() for line in f if line.strip()]


def click_random(locator: Locator, manual_radius: float | None = None) -> None:
    time.sleep(random.uniform(1, 2))
    locator.wait_for(state="visible", timeout=50000)
    box = locator.bounding_box()
    if box is None:
        raise Exception("Bounding box not found")
    width, height = box["width"], box["height"]
    cx, cy = width / 2, height / 2
    radius = manual_radius if manual_radius is not None else min(width, height) / 2
    angle = random.uniform(0, 2 * math.pi)
    r = radius * math.sqrt(random.uniform(0, 1))
    rand_x = cx + r * math.cos(angle)
    rand_y = cy + r * math.sin(angle)

    locator.click(position={"x": rand_x, "y": rand_y})
