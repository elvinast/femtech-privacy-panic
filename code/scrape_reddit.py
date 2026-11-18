"""
Reddit scraper for FemTech Privacy Thesis
Uses Reddit's public JSON API — no API key needed.
Run: python3 scrape_reddit.py
Output: thesis/raw_data/reddit_femtech.csv
"""

import requests
import time
import csv
import os
import json
from datetime import datetime

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) FemTechResearch/1.0"
}

OUTPUT_PATH = os.path.join(os.path.dirname(__file__), "raw_data", "reddit_femtech.csv")

# ── What to search ────────────────────────────────────────────────────────────
SEARCHES = [
    # (subreddit, search_query)
    ("birthcontrol",        "flo app privacy"),
    ("birthcontrol",        "clue app privacy"),
    ("birthcontrol",        "natural cycles data"),
    ("birthcontrol",        "period tracker privacy"),
    ("TryingForABaby",      "premom data privacy"),
    ("TryingForABaby",      "flo app data"),
    ("TryingForABaby",      "fertility app privacy"),
    ("PCOS",                "flo app"),
    ("PCOS",                "clue app privacy"),
    ("privacy",             "flo health data"),
    ("privacy",             "femtech period tracker"),
    ("privacy",             "clue period app"),
    ("privacy",             "natural cycles"),
    ("privacy",             "period app data selling"),
    ("TwoXChromosomes",     "period tracker privacy"),
    ("TwoXChromosomes",     "flo app delete"),
    ("TwoXChromosomes",     "femtech roe wade"),
    ("AskWomen",            "period tracker privacy"),
    ("AskWomen",            "flo app data"),
    ("Flo_app",             "privacy"),
    ("Flo_app",             "data"),
    ("Flo_app",             "delete"),
    ("NaturalFamilyPlanning", "natural cycles privacy"),
    ("menstruation",        "privacy tracker"),
]

def fetch_posts(subreddit, query, limit=100):
    url = f"https://www.reddit.com/r/{subreddit}/search.json"
    params = {"q": query, "sort": "relevance", "limit": limit, "t": "all", "restrict_sr": "1"}
    try:
        r = requests.get(url, headers=HEADERS, params=params, timeout=15)
        if r.status_code != 200:
            print(f"  ⚠ {subreddit} '{query}' → HTTP {r.status_code}")
            return []
        data = r.json()
        posts = data.get("data", {}).get("children", [])
        return [p["data"] for p in posts]
    except Exception as e:
        print(f"  ✗ Error: {e}")
        return []

def fetch_comments(post_id, subreddit, limit=50):
    url = f"https://www.reddit.com/r/{subreddit}/comments/{post_id}.json"
    params = {"limit": limit, "depth": 2}
    try:
        r = requests.get(url, headers=HEADERS, params=params, timeout=15)
        if r.status_code != 200:
            return []
        data = r.json()
        if len(data) < 2:
            return []
        comments = []
        for item in data[1]["data"]["children"]:
            if item["kind"] == "t1":
                c = item["data"]
                if c.get("body") and c["body"] != "[deleted]" and c["body"] != "[removed]":
                    comments.append(c)
        return comments
    except Exception as e:
        return []

def is_privacy_relevant(text):
    """Quick filter — keep only privacy-relevant content."""
    keywords = [
        "privacy", "data", "sell", "sold", "share", "sharing", "track", "tracking",
        "delete", "deleted", "switch", "switched", "ftc", "gdpr", "encrypt",
        "facebook", "meta", "third party", "third-party", "roe", "wade",
        "location", "health data", "personal data", "flo", "premom", "stardust",
        "clue", "natural cycles", "safe", "trust", "concern", "hack", "breach",
        "surveillance", "government", "law enforcement", "subpoena"
    ]
    text_lower = text.lower()
    return any(kw in text_lower for kw in keywords)

def main():
    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)

    rows = []
    seen_ids = set()

    print(f"\n🔍 Starting Reddit scrape — {len(SEARCHES)} searches\n")

    for i, (sub, query) in enumerate(SEARCHES):
        print(f"[{i+1}/{len(SEARCHES)}] r/{sub} — '{query}'")
        posts = fetch_posts(sub, query, limit=100)
        print(f"  → {len(posts)} posts found")

        for post in posts:
            pid = post.get("id", "")
            if pid in seen_ids:
                continue
            seen_ids.add(pid)

            title = post.get("title", "")
            body  = post.get("selftext", "")
            full_text = f"{title} {body}".strip()

            if not is_privacy_relevant(full_text):
                continue

            created = datetime.utcfromtimestamp(post.get("created_utc", 0))
            rows.append({
                "id":           f"reddit_post_{pid}",
                "source":       "reddit",
                "subreddit":    sub,
                "type":         "post",
                "date":         created.strftime("%Y-%m-%d"),
                "text":         full_text[:2000],
                "score":        post.get("score", 0),
                "num_comments": post.get("num_comments", 0),
                "url":          f"https://reddit.com{post.get('permalink','')}",
                "query":        query,
            })

            # Fetch comments for high-engagement posts
            if post.get("num_comments", 0) >= 5:
                comments = fetch_comments(pid, sub)
                for c in comments:
                    cid = c.get("id", "")
                    if f"reddit_comment_{cid}" in seen_ids:
                        continue
                    seen_ids.add(f"reddit_comment_{cid}")
                    cbody = c.get("body", "")
                    if not is_privacy_relevant(cbody):
                        continue
                    c_created = datetime.utcfromtimestamp(c.get("created_utc", 0))
                    rows.append({
                        "id":           f"reddit_comment_{cid}",
                        "source":       "reddit",
                        "subreddit":    sub,
                        "type":         "comment",
                        "date":         c_created.strftime("%Y-%m-%d"),
                        "text":         cbody[:2000],
                        "score":        c.get("score", 0),
                        "num_comments": 0,
                        "url":          f"https://reddit.com{c.get('permalink','')}",
                        "query":        query,
                    })
                time.sleep(0.5)  # be polite between comment fetches

        time.sleep(1.5)  # rate limit between searches

    # Save
    if not rows:
        print("\n⚠ No rows collected — check your internet connection.")
        return

    fieldnames = ["id","source","subreddit","type","date","text","score","num_comments","url","query"]
    with open(OUTPUT_PATH, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    print(f"\n✅ Done! Saved {len(rows):,} privacy-relevant rows to:")
    print(f"   {OUTPUT_PATH}")
    print(f"\nBreakdown by type:")
    posts_n    = sum(1 for r in rows if r["type"] == "post")
    comments_n = sum(1 for r in rows if r["type"] == "comment")
    print(f"   Posts:    {posts_n:,}")
    print(f"   Comments: {comments_n:,}")
    print(f"\nBreakdown by subreddit:")
    subs = {}
    for r in rows:
        subs[r["subreddit"]] = subs.get(r["subreddit"], 0) + 1
    for s, n in sorted(subs.items(), key=lambda x: -x[1]):
        print(f"   r/{s:<25} {n:>4}")

if __name__ == "__main__":
    main()
