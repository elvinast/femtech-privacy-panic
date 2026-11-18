"""
FetchLayer Reddit API — FemTech Privacy Collector
==================================================
Запуск:
    pip install requests pandas
    python fetchlayer_test.py

Результат: reddit_femtech_sample.csv
"""

import requests
import pandas as pd
import time
from datetime import datetime

FETCHLAYER_KEY = "ss-86b2ca2ec3781206594e130c9bd23801e43c34ffb0f7495ad9445f5b8e2a"
BASE_URL = "https://fetchlayer.dev/api/reddit"
HEADERS  = {
    "Authorization": f"Bearer {FETCHLAYER_KEY}",
    "Content-Type":  "application/json"
}

# ── Запросы ───────────────────────────────────────────────
# Формат: (endpoint, body, label)
# endpoint: "search" | "search-comments"
QUERIES = [
    # ── Посты в конкретных subreddits ──
    ("search", {
        "query": "flo app privacy data sharing",
        "subreddit": "birthcontrol",
        "sort": "top", "time": "all", "limit": 25
    }, "Posts: Flo privacy — r/birthcontrol"),

    ("search", {
        "query": "period tracker privacy data",
        "subreddit": "TryingForABaby",
        "sort": "top", "time": "all", "limit": 25
    }, "Posts: Period tracker privacy — r/TryingForABaby"),

    ("search", {
        "query": "femtech period app data",
        "subreddit": "privacy",
        "sort": "top", "time": "all", "limit": 25
    }, "Posts: FemTech — r/privacy"),

    ("search", {
        "query": "flo health clue app period tracker privacy",
        "subreddit": "PCOS",
        "sort": "top", "time": "all", "limit": 25
    }, "Posts: Period apps — r/PCOS"),

    ("search", {
        "query": "period app data privacy",
        "subreddit": "TwoXChromosomes",
        "sort": "top", "time": "all", "limit": 25
    }, "Posts: Period app privacy — r/TwoXChromosomes"),

    # ── Комментарии ──
    ("search-comments", {
        "query": "flo app privacy data",
        "subreddit": "birthcontrol",
        "sort": "top", "time": "all", "limit": 25
    }, "Comments: Flo — r/birthcontrol"),

    ("search-comments", {
        "query": "period tracker privacy sharing surveillance",
        "subreddit": "privacy",
        "sort": "top", "time": "all", "limit": 25
    }, "Comments: Period tracker — r/privacy"),

    ("search-comments", {
        "query": "natural cycles premom flo clue privacy",
        "sort": "top", "time": "all", "limit": 25
    }, "Comments: FemTech apps — global"),
]

# ── Строгий relevance filter ──────────────────────────────
# Требуем FemTech-специфичное слово (не просто "privacy" или "data")
FEMTECH_KEYWORDS = [
    "flo", "clue", "natural cycles", "premom", "stardust",
    "period app", "period tracker", "menstrual", "femtech",
    "reproductive health", "fertility app", "cycle tracking",
    "period data", "ovulation", "birth control app",
]

def is_relevant(text: str) -> bool:
    t = text.lower()
    return any(kw in t for kw in FEMTECH_KEYWORDS)


# ── Парсеры ───────────────────────────────────────────────
def parse_post(item, label):
    created = item.get("createdAt") or ""
    try:
        date = datetime.strptime(created, "%Y-%m-%dT%H:%M:%S.%fZ").strftime("%Y-%m-%d")
    except Exception:
        try:
            date = datetime.strptime(created, "%Y-%m-%dT%H:%M:%SZ").strftime("%Y-%m-%d")
        except Exception:
            date = created[:10] if len(created) >= 10 else ""

    return {
        "type":         "post",
        "label":        label,
        "subreddit":    item.get("subreddit", ""),
        "title":        item.get("title", ""),
        "text":         item.get("previewText", ""),
        "author":       item.get("author", ""),
        "score":        item.get("score") or 0,
        "num_comments": item.get("commentCount") or 0,
        "url":          "https://reddit.com" + item.get("permalink", "") if item.get("permalink") else item.get("url",""),
        "date":         date,
        "year":         date[:4] if date else "",
    }


def parse_comment(item, label):
    created = item.get("createdAt") or ""
    try:
        date = datetime.strptime(created, "%Y-%m-%dT%H:%M:%S.%fZ").strftime("%Y-%m-%d")
    except Exception:
        try:
            date = datetime.strptime(created, "%Y-%m-%dT%H:%M:%SZ").strftime("%Y-%m-%d")
        except Exception:
            date = created[:10] if len(created) >= 10 else ""

    return {
        "type":         "comment",
        "label":        label,
        "subreddit":    item.get("subreddit", ""),
        "title":        item.get("postTitle", ""),
        "text":         item.get("body", "") or item.get("previewText", ""),
        "author":       item.get("author", ""),
        "score":        item.get("score") or 0,
        "num_comments": 0,
        "url":          "https://reddit.com" + item.get("permalink", "") if item.get("permalink") else "",
        "date":         date,
        "year":         date[:4] if date else "",
    }


# ── Запрос к API ──────────────────────────────────────────
def call_api(endpoint, body):
    r = requests.post(f"{BASE_URL}/{endpoint}", headers=HEADERS, json=body, timeout=20)
    r.raise_for_status()
    data = r.json()
    return data.get("items", []), data.get("itemCount", 0)


# ── Main ──────────────────────────────────────────────────
print("=" * 62)
print("  FetchLayer Reddit API — FemTech Privacy Collector")
print("=" * 62)

all_rows = []
seen_ids = set()

for endpoint, body, label in QUERIES:
    print(f"\n→ {label}")
    try:
        items, total = call_api(endpoint, body)
        new = skipped = 0

        for item in items:
            uid = item.get("permalink") or item.get("shortlink") or item.get("url") or str(id(item))
            text_full = " ".join(filter(None, [
                item.get("title",""),
                item.get("previewText",""),
                item.get("body",""),
            ]))

            if uid in seen_ids:
                continue
            if not is_relevant(text_full):
                skipped += 1
                continue

            seen_ids.add(uid)
            if endpoint == "search":
                all_rows.append(parse_post(item, label))
            else:
                all_rows.append(parse_comment(item, label))
            new += 1

        print(f"  ✓ {new} релевантных / {total} всего (пропущено {skipped} нерелевантных)")
        time.sleep(1.5)

    except requests.HTTPError as e:
        print(f"  ✗ HTTP {e.response.status_code}: {e.response.text[:200]}")
    except Exception as e:
        print(f"  ✗ {e}")


# ── Сохранить ─────────────────────────────────────────────
if not all_rows:
    print("\n❌ Нет данных.")
    exit(1)

df = pd.DataFrame(all_rows)
out = "reddit_femtech_sample.csv"
df.to_csv(out, index=False)

print("\n" + "=" * 62)
print(f"  ✅  ИТОГО: {len(df)} записей "
      f"({df[df.type=='post'].shape[0]} постов, {df[df.type=='comment'].shape[0]} комментариев)")
print(f"  💾  Сохранено: {out}")
print("=" * 62)

print("\n📊 По subreddit:")
print(df.groupby("subreddit")["type"].count().sort_values(ascending=False).to_string())

if df["year"].notna().any():
    print("\n📅 По годам:")
    print(df[df.year != ""].groupby("year")["type"].count().sort_index().to_string())

print("\n🔍 Топ-5 постов по score:")
for _, row in df[df.type=="post"].nlargest(5,"score").iterrows():
    print(f"  [{row['subreddit']}] 👍{row['score']} ({row['date']})")
    print(f"  {str(row['title'])[:90]}")

print("\n🔍 Топ-5 комментариев по score:")
for _, row in df[df.type=="comment"].nlargest(5,"score").iterrows():
    print(f"  [{row['subreddit']}] 👍{row['score']} ({row['date']})")
    print(f"  {str(row['text'])[:90]}...")
