"""
Twitter FemTech — 1M Credit Comprehensive Collection
=====================================================
Budget:  999,750 credits  (~66,650 tweets @ 15 credits/tweet)
Apps:    Flo, Clue, Natural Cycles, Premom, Stardust, Apple Health
Period:  2016–2026  (monthly granularity for scandal periods)

Query phases (priority order):
  Phase 1 — App × Year, Top sort          (baseline coverage)
  Phase 2 — Scandal months, Top + Latest  (deep dive)
  Phase 3 — Topics × Year, Top            (thematic coverage)
  Phase 4 — App × Year, Latest            (chronological layer)
  Phase 5 — Hashtags × Year               (community signals)

Run:
    python twitter_mega.py

Output:
    twitter_femtech_FULL.csv  (merged with existing data)
"""

import requests
import pandas as pd
import time
import os
import calendar
from datetime import datetime

# ─── CONFIG ──────────────────────────────────────────────
API_KEY           = "YOUR_API_KEY"
BASE_URL          = "https://api.twitterapi.io/twitter/tweet/advanced_search"
HEADERS           = {"X-API-Key": API_KEY}

CREDITS_BUDGET    = 999_750
CREDITS_PER_TWEET = 15
EXISTING_FILE     = "twitter_femtech_FULL.csv"
SAVE_EVERY        = 300   # incremental save every N new tweets

# ─── APPS ────────────────────────────────────────────────
# If your 6th app is different, change "maya" entry below.
APPS = {
    "flo": {
        "q": '("flo health" OR "flo app" OR "flo period tracker")',
        "scandal_years": {2019, 2021, 2023, 2025},
        "label": "Flo",
    },
    "clue": {
        "q": '("clue app" OR "clue period" OR "#clueapp" OR "helloclue")',
        "scandal_years": {2020, 2021},
        "label": "Clue",
    },
    "natural_cycles": {
        "q": '"natural cycles"',
        "scandal_years": {2018, 2019},
        "label": "Natural Cycles",
    },
    "premom": {
        "q": 'premom',
        "scandal_years": {2022, 2023},
        "label": "Premom",
    },
    "stardust": {
        "q": '("stardust app" OR "stardust period")',
        "scandal_years": {2022},
        "label": "Stardust",
    },
    "apple_health": {
        # Apple Health cycle tracking — added iOS 13 (2019), major Dobbs concerns 2022
        "q": '("apple health" OR "apple cycle tracking" OR "iphone period") (period OR cycle OR menstrual OR reproductive)',
        "scandal_years": {2019, 2022, 2023},
        "label": "Apple Health",
    },
}

ALL_SCANDAL_YEARS = {2018, 2019, 2021, 2022, 2023, 2025, 2026}
YEARS = list(range(2016, 2027))  # 2016–2026 inclusive

# ─── RELEVANCE FILTER ────────────────────────────────────
# Strict: must contain a FemTech-specific term (not just "privacy")
FEMTECH_TERMS = [
    "flo health", "flo app", "flo period",
    "clue app", "clue period", "helloclue",
    "natural cycles",
    "premom",
    "stardust app", "stardust period",
    "apple cycle tracking", "apple health period", "iphone period track",
    "period app", "period tracker", "period track",
    "menstrual app", "menstrual data", "menstruation",
    "femtech", "fem tech",
    "reproductive health app", "fertility app", "fertility track",
    "cycle track", "ovulation track",
    "period data", "period privacy",
    "birth control app",
]

def is_relevant(text: str) -> bool:
    t = text.lower()
    return any(kw in t for kw in FEMTECH_TERMS)

# ─── SCANDAL MONTH PERIODS ───────────────────────────────
# Each: (base_query, label, "YYYY-MM", "YYYY-MM", pages_per_month)
SCANDAL_MONTH_DEFS = [
    (
        '("flo health" OR "flo app") (FTC OR settlement OR privacy OR data)',
        "SCANDAL: Flo FTC 2021",
        "2021-01", "2021-08", 10
    ),
    (
        '("flo health" OR "flo app") (california OR "$56" OR lawsuit OR settlement)',
        "SCANDAL: Flo $56M CA 2025",
        "2025-01", "2025-09", 10
    ),
    (
        '"natural cycles" (privacy OR ICO OR data OR "facebook pixel" OR NHS)',
        "SCANDAL: Natural Cycles UK 2018",
        "2018-07", "2018-12", 10
    ),
    (
        '"natural cycles" (privacy OR FDA OR data OR investigation)',
        "SCANDAL: Natural Cycles 2019",
        "2019-01", "2019-06", 8
    ),
    (
        'premom (china OR data OR senate OR privacy OR sharing OR tracking)',
        "SCANDAL: Premom China 2022",
        "2022-01", "2022-12", 10
    ),
    (
        '(dobbs OR "roe" OR abortion) ("period app" OR "period tracker" OR "flo" OR femtech)',
        "SCANDAL: Dobbs + period apps",
        "2022-05", "2022-12", 10
    ),
    (
        '"period app" (delete OR surveillance OR "law enforcement" OR police OR tracking)',
        "SCANDAL: Period app fears post-Dobbs",
        "2022-06", "2023-03", 8
    ),
    (
        '("apple health" OR "apple cycle") (period OR menstrual) (privacy OR data OR surveillance)',
        "SCANDAL: Apple Health Dobbs 2022",
        "2022-05", "2022-12", 8
    ),
    (
        '"apple health" (period OR menstrual OR cycle) (icloud OR privacy OR data)',
        "Apple Health privacy concerns",
        "2019-09", "2021-12", 6
    ),
    (
        '(facebook OR meta) ("menstrual" OR "period" OR "reproductive") (data OR privacy)',
        "SCANDAL: Meta menstrual data 2025",
        "2025-01", "2025-09", 10
    ),
    (
        '(meta OR facebook) ("menstrual" OR "period" OR "reproductive" OR femtech) (data OR privacy OR guilty OR lawsuit OR fine)',
        "SCANDAL: Meta menstrual data 2026",
        "2026-01", "2026-07", 10
    ),
    (
        'femtech (meta OR facebook) (data OR privacy OR tracking OR ruling)',
        "SCANDAL: Meta FemTech ruling 2026",
        "2026-01", "2026-07", 8
    ),
    (
        '"flo health" (privacy OR data OR facebook OR google OR sharing)',
        "SCANDAL: Flo FTC lead-up 2019",
        "2019-01", "2020-12", 6
    ),
]

# ─── TOPIC QUERIES (Phase 3) ─────────────────────────────
TOPIC_QUERIES = [
    ('"reproductive data" privacy', "Topic: Reproductive data privacy"),
    ('"menstrual data" privacy', "Topic: Menstrual data privacy"),
    ('"period tracking" surveillance privacy', "Topic: Period tracking surveillance"),
    ('"period app" "third party" OR "third-party" data', "Topic: Third-party data sharing"),
    ('"period app" delete privacy', "Topic: Delete period data"),
    ('femtech "data breach" OR "data leak"', "Topic: FemTech data breach"),
    ('"period tracker" (sell OR selling OR sold) data', "Topic: Data selling"),
    ('femtech (regulation OR law OR congress OR GDPR OR HIPAA)', "Topic: FemTech regulation"),
]

# ─── HASHTAG QUERIES (Phase 5) ───────────────────────────
HASHTAG_QUERIES = [
    ('#femtech (privacy OR data OR tracking)', "Hashtag: #femtech privacy"),
    ('#periodtracker (privacy OR data OR surveillance)', "Hashtag: #periodtracker privacy"),
    ('#reproductivejustice ("period app" OR femtech OR data)', "Hashtag: #reproductivejustice + data"),
    ('#dataprotection (femtech OR "period app" OR menstrual)', "Hashtag: #dataprotection + femtech"),
]

# ─── BUDGET ──────────────────────────────────────────────
class Budget:
    def __init__(self, b):
        self.budget = b
        self.spent  = 0
        self.tweets = 0

    def charge(self, n):
        cost = max(n * CREDITS_PER_TWEET, 15)
        self.spent  += cost
        self.tweets += n

    def remaining(self):
        return self.budget - self.spent

    def ok(self, min_credits=300):
        return self.remaining() >= min_credits

    def bar(self):
        pct = self.spent / self.budget * 100
        rem_tweets = self.remaining() // CREDITS_PER_TWEET
        return (f"💳 {self.spent:,}/{self.budget:,} ({pct:.1f}%) "
                f"| 🐦 {self.tweets:,} collected "
                f"| ~{rem_tweets:,} credits left")

# ─── FETCH ───────────────────────────────────────────────
def fetch_page(query, cursor="", qtype="Top"):
    r = requests.get(BASE_URL, headers=HEADERS, params={
        "query": query, "queryType": qtype, "cursor": cursor,
    }, timeout=20)
    r.raise_for_status()
    return r.json()

def parse_tweet(t, label, qtype):
    a = t.get("author", {})
    created = t.get("createdAt", "")
    try:
        date = datetime.strptime(created, "%a %b %d %H:%M:%S +0000 %Y").strftime("%Y-%m-%d")
    except Exception:
        date = ""
    return {
        "source":           "twitter",
        "label":            label,
        "query_type":       qtype,
        "tweet_id":         str(t.get("id", "")),
        "text":             t.get("text", ""),
        "created_at":       created,
        "date":             date,
        "year":             date[:4]  if date else "",
        "month":            date[:7]  if date else "",
        "lang":             t.get("lang", ""),
        "likes":            t.get("likeCount", 0),
        "retweets":         t.get("retweetCount", 0),
        "replies":          t.get("replyCount", 0),
        "quotes":           t.get("quoteCount", 0),
        "views":            t.get("viewCount", 0),
        "bookmarks":        t.get("bookmarkCount", 0),
        "is_reply":         t.get("isReply", False),
        "author_name":      a.get("name", ""),
        "author_user":      a.get("userName", ""),
        "author_followers": a.get("followers", 0),
        "author_verified":  a.get("isBlueVerified", False),
        "url":              t.get("url", ""),
    }

# ─── COLLECT ONE QUERY ───────────────────────────────────
def collect(query, label, max_pages, qtype, budget, seen_ids, buffer,
            strict_filter=True):
    """
    Run up to max_pages for one query. Returns count of new tweets added.
    strict_filter=False: skip relevance check (for app-specific queries where
    the query string already guarantees topic relevance).
    """
    cursor = ""
    page   = 0
    added  = 0

    while page < max_pages and budget.ok(15):
        try:
            data     = fetch_page(query, cursor, qtype)
            tweets   = data.get("tweets", [])
            has_next = data.get("has_next_page", False)
            cursor   = data.get("next_cursor", "")

            new = irrel = dup = 0
            for t in tweets:
                tid = str(t.get("id", ""))
                if tid in seen_ids:
                    dup += 1
                    continue
                if strict_filter and not is_relevant(t.get("text", "")):
                    irrel += 1
                    continue
                seen_ids.add(tid)
                buffer.append(parse_tweet(t, label, qtype))
                new += 1
                added += 1

            budget.charge(len(tweets))
            print(f"    p{page+1}: +{new} new  "
                  f"(skip {irrel} irrel, {dup} dup) | {budget.bar()}")

            if not has_next or not tweets:
                break
            page += 1
            time.sleep(1.5)

        except requests.HTTPError as e:
            if "429" in str(e):
                print("    ⚠ Rate limit — waiting 15s...")
                time.sleep(15)
                continue
            print(f"    ✗ HTTP error: {e}")
            break
        except Exception as e:
            print(f"    ✗ Error: {e}")
            break

    return added

# ─── SAVE ────────────────────────────────────────────────
def save_buffer(buffer):
    """Merge buffer into EXISTING_FILE and clear buffer."""
    if not buffer:
        return 0
    df_new = pd.DataFrame(buffer)
    if os.path.exists(EXISTING_FILE):
        df_old = pd.read_csv(EXISTING_FILE, dtype={"tweet_id": str})
        df_all = pd.concat([df_old, df_new], ignore_index=True)
        df_all = df_all.drop_duplicates(subset=["tweet_id"])
    else:
        df_all = df_new
    df_all.to_csv(EXISTING_FILE, index=False)
    total = len(df_all)
    print(f"  💾 Saved → {EXISTING_FILE}  (total: {total:,} tweets)")
    buffer.clear()
    return total

# ─── BUILD QUERY LIST ────────────────────────────────────
def build_queries():
    """
    Returns list of (query_str, label, max_pages, qtype, phase, strict_filter)
    sorted by phase (lower = higher priority).

    strict_filter=False for app-named queries: the query already guarantees
    topic relevance, so we keep every tweet → maximises yield.
    strict_filter=True for broad topic/hashtag queries: need the check.
    """
    q = []

    # ── Phase 1: App × Year, Top  (no relevance filter) ─
    for app in APPS.values():
        for year in YEARS:
            is_scandal = (year in app["scandal_years"] or year in ALL_SCANDAL_YEARS)
            pages = 8 if is_scandal else 4
            query = (
                f'{app["q"]} (privacy OR data OR tracking OR sharing) '
                f'since:{year}-01-01 until:{year}-12-31 -is:retweet lang:en'
            )
            q.append((query, f'{app["label"]} {year} [Top]', pages, "Top", 1, False))

    # ── Phase 2: Scandal months, Top + Latest  (no filter) ─
    for q_base, label, start_ym, end_ym, pages in SCANDAL_MONTH_DEFS:
        sy, sm = int(start_ym[:4]), int(start_ym[5:])
        ey, em = int(end_ym[:4]),   int(end_ym[5:])
        y, m = sy, sm
        while (y, m) <= (ey, em):
            _, ld  = calendar.monthrange(y, m)
            df     = f"since:{y}-{m:02d}-01 until:{y}-{m:02d}-{ld:02d}"
            full_q = f"{q_base} {df} -is:retweet lang:en"
            tag    = f"{label} [{y}-{m:02d}]"
            q.append((full_q, tag + " [Top]",    pages, "Top",    2, False))
            q.append((full_q, tag + " [Latest]", pages, "Latest", 2, False))
            m += 1
            if m > 12:
                m, y = 1, y + 1

    # ── Phase 3: Topics × Year, Top  (strict filter) ────
    for q_base, label in TOPIC_QUERIES:
        for year in YEARS:
            is_scandal = year in ALL_SCANDAL_YEARS
            pages  = 5 if is_scandal else 3
            full_q = f'{q_base} since:{year}-01-01 until:{year}-12-31 -is:retweet lang:en'
            q.append((full_q, f"{label} {year}", pages, "Top", 3, True))

    # ── Phase 4: App × Year, Latest  (no filter) ────────
    for app in APPS.values():
        for year in YEARS:
            is_scandal = (year in app["scandal_years"] or year in ALL_SCANDAL_YEARS)
            pages = 6 if is_scandal else 3
            query = (
                f'{app["q"]} (privacy OR data OR tracking OR sharing) '
                f'since:{year}-01-01 until:{year}-12-31 -is:retweet lang:en'
            )
            q.append((query, f'{app["label"]} {year} [Latest]', pages, "Latest", 4, False))

    # ── Phase 5: Hashtags × Year  (strict filter) ───────
    for q_base, label in HASHTAG_QUERIES:
        for year in YEARS:
            is_scandal = year in ALL_SCANDAL_YEARS
            pages  = 4 if is_scandal else 2
            full_q = f'{q_base} since:{year}-01-01 until:{year}-12-31 -is:retweet lang:en'
            q.append((full_q, f"{label} {year}", pages, "Top", 5, True))

    q.sort(key=lambda x: x[4])
    return q

# ─── MAIN ────────────────────────────────────────────────
def main():
    print("=" * 68)
    print("  Twitter FemTech — 1M Credit Comprehensive Collection")
    print(f"  Budget: {CREDITS_BUDGET:,} credits  "
          f"(~{CREDITS_BUDGET // CREDITS_PER_TWEET:,} tweets)")
    print("=" * 68)

    budget   = Budget(CREDITS_BUDGET)
    buffer   = []
    seen_ids = set()
    save_ctr = 0

    # Load existing IDs to avoid duplicates
    if os.path.exists(EXISTING_FILE):
        existing = pd.read_csv(EXISTING_FILE, dtype={"tweet_id": str})
        seen_ids = set(existing["tweet_id"].tolist())
        print(f"  ℹ  Loaded {len(seen_ids):,} existing tweet IDs (will skip dupes)")

    queries = build_queries()
    print(f"  📋 Query segments planned: {len(queries):,}")
    print(f"  📄 Max pages if fully run:  "
          f"~{sum(q[2] for q in queries):,} "
          f"(~{sum(q[2] for q in queries) * 300:,} credits)\n")

    current_phase = 0
    phase_labels  = {
        1: "App × Year  [Top]  — no filter",
        2: "Scandal months  [Top + Latest]  — no filter",
        3: "Topics × Year  [Top]  — strict filter",
        4: "App × Year  [Latest]  — no filter",
        5: "Hashtags × Year  — strict filter",
    }

    for query_str, label, max_pages, qtype, phase, strict in queries:

        if not budget.ok(300):
            print("\n⚠  Budget exhausted. Stopping.")
            break

        if phase != current_phase:
            current_phase = phase
            print(f"\n{'='*68}")
            print(f"  PHASE {phase}: {phase_labels.get(phase,'')} "
                  f"| remaining: {budget.remaining():,} credits")
            print(f"{'='*68}")

        print(f"\n→ [{qtype}] {label}")
        added = collect(query_str, label, max_pages, qtype,
                        budget, seen_ids, buffer, strict_filter=strict)
        save_ctr += added

        if save_ctr >= SAVE_EVERY:
            save_buffer(buffer)
            save_ctr = 0

        time.sleep(2)

    # Final save
    save_buffer(buffer)

    # ── Summary ──────────────────────────────────────────
    print("\n" + "=" * 68)
    if os.path.exists(EXISTING_FILE):
        df = pd.read_csv(EXISTING_FILE, dtype={"tweet_id": str})
        print(f"  ✅  TOTAL in file:    {len(df):,} tweets")
        print(f"  💳  Credits spent:    {budget.spent:,} / {budget.budget:,}")
        print(f"  💰  Credits unused:   {budget.remaining():,}")
        print("=" * 68)

        print("\n📊 By app/topic (top 20):")
        label_counts = df["label"].str.extract(r'^([^[]+)')[0].str.strip()
        label_counts = label_counts.str.replace(r'\s+\d{4}$', '', regex=True)
        print(label_counts.value_counts().head(20).to_string())

        print("\n📅 By year:")
        yr = df[df["year"].notna() & (df["year"] != "")]
        if len(yr):
            print(yr.groupby("year")["tweet_id"].count().sort_index().to_string())

        print("\n📅 By month (scandal periods):")
        scandal_months = df[df["month"].isin([
            "2018-07","2018-08","2018-09","2018-10","2018-11","2018-12",
            "2021-01","2021-02","2021-03","2021-04","2021-05","2021-06",
            "2022-05","2022-06","2022-07","2022-08","2022-09","2022-10",
            "2025-01","2025-02","2025-03","2025-04","2025-05","2025-06",
        ])]
        if len(scandal_months):
            print(scandal_months.groupby("month")["tweet_id"].count().sort_index().to_string())

        print("\n🔥 Top 10 tweets by likes:")
        for _, row in df.nlargest(10, "likes").iterrows():
            print(f"\n  ❤️ {int(row.get('likes',0)):,}  "
                  f"🔁 {int(row.get('retweets',0)):,}  "
                  f"({row.get('date','?')})")
            print(f"  [{row.get('label','')}]")
            print(f"  {str(row.get('text',''))[:120]}...")

if __name__ == "__main__":
    main()
