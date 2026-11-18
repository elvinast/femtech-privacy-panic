"""
Fetches privacy policy texts for all 5 femtech apps.
Run: python3 fetch_policies.py
Output: raw_data/privacy_policies.json
"""

import requests
from bs4 import BeautifulSoup
import json, time, os

OUTPUT = os.path.join(os.path.dirname(__file__), "raw_data", "privacy_policies.json")
os.makedirs(os.path.dirname(OUTPUT), exist_ok=True)

HEADERS = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"}

URLS = {
    "Flo":           "https://flo.health/legal/privacy-policy",
    "Clue":          "https://helloclue.com/articles/about-clue/clue-privacy-policy",
    "Premom":        "https://premom.com/privacy-policy/",
    "NaturalCycles": "https://www.naturalcycles.com/en/privacy",
    "Stardust":      "https://stardust.app/privacy",
}

policies = {}

for app, url in URLS.items():
    print(f"\nFetching {app}...")
    try:
        r = requests.get(url, headers=HEADERS, timeout=20)
        soup = BeautifulSoup(r.text, "html.parser")

        # Remove nav, footer, scripts
        for tag in soup(["nav", "footer", "script", "style", "header", "button"]):
            tag.decompose()

        # Get main text
        main = soup.find("main") or soup.find("article") or soup.find("body")
        text = main.get_text(separator="\n", strip=True) if main else soup.get_text()

        # Clean up blank lines
        lines = [l.strip() for l in text.splitlines() if l.strip()]
        clean = "\n".join(lines)

        policies[app] = clean
        print(f"  ✅ {len(clean):,} chars")
        time.sleep(1)

    except Exception as e:
        print(f"  ❌ Error: {e}")
        policies[app] = ""

with open(OUTPUT, "w", encoding="utf-8") as f:
    json.dump(policies, f, ensure_ascii=False, indent=2)

print(f"\n✅ Saved to {OUTPUT}")
for app, text in policies.items():
    status = f"{len(text):,} chars" if text else "EMPTY — paste manually"
    print(f"  {app}: {status}")
