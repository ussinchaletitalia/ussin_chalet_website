from pathlib import Path
from html.parser import HTMLParser
from urllib.request import Request, urlopen
from datetime import datetime, timezone
import json
import re


URL = "https://www.cervinia.it/en/impianti"

BASE = Path(__file__).resolve().parents[1]
OUTPUT = BASE / "data" / "cervinia-status.json"


class TextExtractor(HTMLParser):
    def __init__(self):
        super().__init__()
        self.parts = []

    def handle_data(self, data):
        text = data.strip()
        if text:
            self.parts.append(text)


req = Request(
    URL,
    headers={
        "User-Agent": (
            "Mozilla/5.0 (compatible; UssinChaletLiftStatus/1.0; "
            "+https://github.com/)"
        )
    }
)

with urlopen(req, timeout=30) as response:
    html = response.read().decode("utf-8", errors="ignore")


parser = TextExtractor()
parser.feed(html)

text = " ".join(parser.parts)
text = re.sub(r"\s+", " ", text)


# ------------------------------------------------------------
# LIFT COUNT
# Looks for:
# Ski lifts 12 di 19
# ------------------------------------------------------------

lift_match = re.search(
    r"Ski\s+lifts.*?(\d+)\s+di\s+(\d+)",
    text,
    flags=re.I
)

if not lift_match:
    raise RuntimeError("Could not find Cervinia ski lift count")

lifts_open = int(lift_match.group(1))
lifts_total = int(lift_match.group(2))


# ------------------------------------------------------------
# MATTERHORN ALPINE CROSSING
# ------------------------------------------------------------

crossing_match = re.search(
    r"Matterhorn\s+Alpine\s+Crossing\s+(open|closed)",
    text,
    flags=re.I
)

if crossing_match:
    crossing = crossing_match.group(1).lower()
else:
    crossing = "unknown"


# ------------------------------------------------------------
# PRESERVE TIMESTAMP IF NOTHING CHANGED
# ------------------------------------------------------------

old = {}

if OUTPUT.exists():
    try:
        old = json.loads(OUTPUT.read_text())
    except Exception:
        old = {}

same = (
    old.get("lifts_open") == lifts_open
    and old.get("lifts_total") == lifts_total
    and old.get("crossing") == crossing
)

if same:
    updated_at = old.get("updated_at")
else:
    updated_at = datetime.now(timezone.utc).isoformat()


data = {
    "lifts_open": lifts_open,
    "lifts_total": lifts_total,
    "crossing": crossing,
    "updated_at": updated_at
}

OUTPUT.parent.mkdir(exist_ok=True)

OUTPUT.write_text(
    json.dumps(data, indent=2) + "\n"
)

print(
    f"Cervinia: {lifts_open}/{lifts_total} lifts open | "
    f"Crossing: {crossing}"
)
