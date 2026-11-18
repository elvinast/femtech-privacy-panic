"""
Reddit Data Collector — FemTech Privacy Thesis
================================================
Вариант 1: Без API ключей (JSON endpoint) — запускай сразу!
Вариант 2: С PRAW (больше данных) — см. reddit_praw.py

Запуск:
    pip install requests pandas
    python reddit_test.py

Результат: reddit_sample.csv
"""

import requests
import pandas as pd
import time
import json
from datetime import datetime

HEADERS = {
    "User-Agent": "research-thesis-femtech/1.0 (academic study)"
}

# ── Subreddits и запросы ──────────────────────────────────
SEARCHES = [
    # (subreddit, query, описание)
    ("birthcontrol",   "flo app privacy",           "Flo + privacy в r/birthcontrol"),
    ("birthcontrol",   "period tracker data",        "данные трекеров в r/birthcontrol"),
    ("birthcontrol",   "clue app privacy",           "Clue + privacy"),
    ("TryingForABaby", "flo privacy data",           "Flo в r/TryingForABaby"),
    ("TryingForABaby", "period tracker sharing",     "sharing данных"),
    ("PCOS",           "period app privacy",         "privacy в r/PCOS"),
    ("privacy",        "flo period tracker",         "Flo в r/privacy"),
    ("privacy",        "femtech data",               "femtech в r/privacy"),
    ("privacy",        "period app data leak",       "утечки данных"),
    ("ClueApp",        "data privacy",               "privacy в r/ClueApp"),
]

LIMIT = 25  # постов на запрос (max 100)

def fetch_posts(subreddit, query, limit=LIMIT):
    """Скачать посты через Reddit JSON API (без ключей)."""
    url = (
        f"https://www.reddit.com/r/{subreddit}/search.json"
        f"?q={query.replace(' ', '+')}"
        f"&limit={limit}"
        f"&restrict_sr=1"
        f"&sort=relevance"
        f"&t=all"
    )
    try:
        r = requests.get(url, headers=HEADERS, timeout=15)
        if r.status_code == 200:
            posts = r.json().get("data", {}).get("children", [])
            return [p["data"] for p in posts]
        elif r.status_code == 429:
            print(f"  ⚠ Rate limited — жду 30 сек...")
            time.sleep(30)
            return fetch_posts(subreddit, query, limit)
        else:
            print(f"  ✗ HTTP {r.status_code}")
            return []
    except Exception as e:
        print(f"  ✗ Error: {e}")
        return []

def extract_fields(post, query_label):
    """Извлечь нужные поля из поста."""
    return {
        "source":       "reddit",
        "subreddit":    post.get("subreddit", ""),
        "query":        query_label,
        "post_id":      post.get("id", ""),
        "title":        post.get("title", ""),
        "text":         post.get("selftext", ""),
        "score":        post.get("score", 0),
        "num_comments": post.get("num_comments", 0),
        "upvote_ratio": post.get("upvote_ratio", 0),
        "created_utc":  datetime.utcfromtimestamp(post.get("created_utc", 0)).strftime("%Y-%m-%d"),
        "url":          "https://reddit.com" + post.get("permalink", ""),
        "flair":        post.get("link_flair_text", ""),
        "is_original_content": post.get("is_original_content", False),
    }

# ── Основной цикл ─────────────────────────────────────────
print("=" * 60)
print("Reddit FemTech Privacy Scraper — Test Run")
print("=" * 60)

all_posts = []
seen_ids = set()

for subreddit, query, label in SEARCHES:
    print(f"\n→ r/{subreddit} | '{query}'")
    posts = fetch_posts(subreddit, query)

    new = 0
    for p in posts:
        if p["id"] not in seen_ids:
            seen_ids.add(p["id"])
            all_posts.append(extract_fields(p, label))
            new += 1

    print(f"  ✓ {new} новых постов (дубликаты пропущены)")
    time.sleep(2)  # вежливая пауза между запросами

# ── Сохранить ─────────────────────────────────────────────
df = pd.DataFrame(all_posts)
out = "reddit_sample.csv"
df.to_csv(out, index=False)

print("\n" + "=" * 60)
print(f"ИТОГО: {len(df)} уникальных постов")
print(f"Сохранено в: {out}")
print("=" * 60)

# ── Быстрая статистика ────────────────────────────────────
print("\n📊 Распределение по subreddits:")
print(df.groupby("subreddit")["post_id"].count().sort_values(ascending=False).to_string())

print(f"\n📅 Даты: {df['created_utc'].min()} → {df['created_utc'].max()}")
print(f"👍 Средний score: {df['score'].mean():.0f}")
print(f"💬 Средние комменты: {df['num_comments'].mean():.0f}")

print("\n🔍 Топ-5 постов по score:")
top = df.nlargest(5, "score")[["subreddit","title","score","num_comments","created_utc"]]
for _, row in top.iterrows():
    print(f"  [{row['subreddit']}] 👍{row['score']} 💬{row['num_comments']} ({row['created_utc']})")
    print(f"  {row['title'][:80]}")
    print()

print(f"\n✅ Готово! Открой reddit_sample.csv чтобы посмотреть данные.")
