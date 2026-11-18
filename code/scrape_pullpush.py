"""
Reddit scraper via PullPush.io archive API
No authentication needed. Gets posts + comments.
Run: python3 scrape_pullpush.py
Output: raw_data/reddit_pullpush.csv
"""

import requests
import pandas as pd
import time
import os

OUTPUT_PATH = os.path.join(os.path.dirname(__file__), "raw_data", "reddit_pullpush.csv")
os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)

BASE = "https://api.pullpush.io/reddit/search"

# ── Search queries ────────────────────────────────────────────────────────────
SUBMISSION_QUERIES = [
    # Flo
    "flo app privacy", "flo health data", "flo app delete", "flo FTC",
    "flo period tracker data", "flo app facebook", "flo app sold data",
    "delete flo app", "flo premium cancel",
    # Clue
    "clue app privacy", "clue period tracker safe", "clue app data",
    "clue vs flo privacy", "clue GDPR",
    # Premom
    "premom privacy", "premom data china", "premom FTC",
    # Natural Cycles
    "natural cycles privacy", "natural cycles data safe",
    # Stardust
    "stardust app privacy", "stardust encryption lie",
    # General femtech privacy
    "period tracker privacy", "period app data selling",
    "femtech privacy", "fertility app privacy",
    "period tracker roe wade", "period app delete roe",
    "period tracker government", "health app data privacy",
    "menstrual app surveillance", "period app third party",
    "femtech data breach", "period tracker safe",
    "switch period tracker", "best private period tracker",
    "period tracker no data", "anonymous period tracker",
]

COMMENT_QUERIES = [
    "flo privacy data", "period tracker privacy",
    "femtech data", "clue app safe",
    "delete period tracker", "period app roe wade",
    "flo vs clue privacy", "natural cycles safe",
    "premom data sold", "stardust fake encryption",
    "period tracker government data", "femtech surveillance",
]

SUBREDDIT_SEARCHES = [
    # (subreddit, query)
    ("birthcontrol",          "privacy"),
    ("birthcontrol",          "flo app"),
    ("birthcontrol",          "clue app"),
    ("birthcontrol",          "data tracking"),
    ("TryingForABaby",        "premom privacy"),
    ("TryingForABaby",        "fertility app data"),
    ("PCOS",                  "flo app"),
    ("PCOS",                  "period tracker privacy"),
    ("privacy",               "flo health"),
    ("privacy",               "femtech"),
    ("privacy",               "period tracker"),
    ("TwoXChromosomes",       "period tracker delete"),
    ("TwoXChromosomes",       "femtech privacy"),
    ("TwoXChromosomes",       "flo app data"),
    ("AskWomen",              "period tracker safe"),
    ("AskWomen",              "flo vs clue"),
    ("legaladvice",           "flo health data"),
    ("privacy",               "menstrual data"),
    ("DataHoarder",           "femtech"),
    ("PrivacyGuides",         "period tracker"),
]

rows = []
seen_ids = set()

def fetch(endpoint, params, label):
    url = f"{BASE}/{endpoint}/"
    try:
        r = requests.get(url, params=params, timeout=20)
        if r.status_code == 200:
            items = r.json().get("data", [])
            print(f"  ✅ {len(items)} results")
            return items
        else:
            print(f"  ❌ HTTP {r.status_code}")
            return []
    except Exception as e:
        print(f"  ❌ Error: {e}")
        return []

def add_post(post, query="", subreddit_filter=""):
    pid = post.get("id", "")
    uid = f"post_{pid}"
    if uid in seen_ids or not pid:
        return
    seen_ids.add(uid)
    title = str(post.get("title", ""))
    body  = str(post.get("selftext", ""))
    if body in ("[removed]", "[deleted]"):
        body = ""
    text = f"{title} {body}".strip()
    if not text:
        return
    rows.append({
        "id":        uid,
        "source":    "reddit_pullpush",
        "type":      "post",
        "subreddit": post.get("subreddit", subreddit_filter),
        "date":      pd.to_datetime(post.get("created_utc", 0), unit="s").strftime("%Y-%m-%d"),
        "text":      text[:3000],
        "score":     post.get("score", 0),
        "query":     query,
        "url":       post.get("full_link", f"https://reddit.com/{pid}"),
    })

def add_comment(comment, query=""):
    cid = comment.get("id", "")
    uid = f"comment_{cid}"
    if uid in seen_ids or not cid:
        return
    seen_ids.add(uid)
    body = str(comment.get("body", ""))
    if body in ("[removed]", "[deleted]", ""):
        return
    rows.append({
        "id":        uid,
        "source":    "reddit_pullpush",
        "type":      "comment",
        "subreddit": comment.get("subreddit", ""),
        "date":      pd.to_datetime(comment.get("created_utc", 0), unit="s").strftime("%Y-%m-%d"),
        "text":      body[:3000],
        "score":     comment.get("score", 0),
        "query":     query,
        "url":       f"https://reddit.com/r/{comment.get('subreddit','')}/comments/{comment.get('link_id','').replace('t3_','')}",
    })

# ── 1. General submission searches ───────────────────────────────────────────
print(f"\n📦 PART 1: {len(SUBMISSION_QUERIES)} submission searches")
for i, q in enumerate(SUBMISSION_QUERIES):
    print(f"[{i+1}/{len(SUBMISSION_QUERIES)}] submissions: '{q}'")
    posts = fetch("submission", {"q": q, "size": 100, "sort": "desc", "sort_type": "score"}, q)
    for p in posts:
        add_post(p, query=q)
    time.sleep(1.2)

# ── 2. Subreddit-specific searches ───────────────────────────────────────────
print(f"\n📦 PART 2: {len(SUBREDDIT_SEARCHES)} subreddit-specific searches")
for i, (sub, q) in enumerate(SUBREDDIT_SEARCHES):
    print(f"[{i+1}/{len(SUBREDDIT_SEARCHES)}] r/{sub} — '{q}'")
    posts = fetch("submission", {"q": q, "subreddit": sub, "size": 100}, q)
    for p in posts:
        add_post(p, query=q, subreddit_filter=sub)
    time.sleep(1.2)

# ── 3. Comment searches ───────────────────────────────────────────────────────
print(f"\n📦 PART 3: {len(COMMENT_QUERIES)} comment searches")
for i, q in enumerate(COMMENT_QUERIES):
    print(f"[{i+1}/{len(COMMENT_QUERIES)}] comments: '{q}'")
    comments = fetch("comment", {"q": q, "size": 100, "sort": "desc", "sort_type": "score"}, q)
    for c in comments:
        add_comment(c, query=q)
    time.sleep(1.2)

# ── Save ──────────────────────────────────────────────────────────────────────
if rows:
    df = pd.DataFrame(rows)
    df.to_csv(OUTPUT_PATH, index=False, encoding="utf-8")
    print(f"\n✅ Saved {len(df):,} rows to {OUTPUT_PATH}")
    print(f"\nBreakdown:")
    print(f"  Posts:    {(df['type']=='post').sum():,}")
    print(f"  Comments: {(df['type']=='comment').sum():,}")
    print(f"\nBy subreddit (top 10):")
    print(df['subreddit'].value_counts().head(10).to_string())
    print(f"\nDate range: {df['date'].min()} → {df['date'].max()}")
else:
    print("\n❌ No data collected.")
