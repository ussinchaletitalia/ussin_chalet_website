"""Read the Cervinia lift board and write data/cervinia-status.json.

The counter on cervinia.it is injected by JavaScript after load, so a plain
HTTP fetch returns the placeholder "0 di 0". The page has to be rendered.
"""

from pathlib import Path
from datetime import datetime, timezone
import json
import re
import sys

from playwright.sync_api import sync_playwright

URL = "https://www.cervinia.it/en/impianti"
BASE = Path(__file__).resolve().parents[1]
OUTPUT = BASE / "data" / "cervinia-status.json"


def read_page() -> str:
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(locale="en-GB")
        page.goto(URL, wait_until="networkidle", timeout=60000)

        # The board hydrates after load; wait for a non-zero total if one is coming.
        try:
            page.wait_for_function(
                "() => /(\\d+)\\s*(?:di|of|\\/)\\s*([1-9]\\d*)/i.test(document.body.innerText)",
                timeout=20000,
            )
        except Exception:
            pass  # Out of season the total really is zero.

        text = page.inner_text("body")
        browser.close()

    return re.sub(r"\s+", " ", text)


text = read_page()

lift_match = re.search(r"Ski\s+lifts\D{0,40}?(\d+)\s*(?:di|of|/)\s*(\d+)", text, re.I)
if not lift_match:
    lift_match = re.search(r"(\d+)\s*(?:di|of|/)\s*(\d+)\s*(?:impianti|lifts)", text, re.I)

if not lift_match:
    sys.exit("Could not find the Cervinia lift count on the rendered page")

lifts_open = int(lift_match.group(1))
lifts_total = int(lift_match.group(2))

if lifts_open > lifts_total:
    sys.exit(f"Nonsensical lift count:
