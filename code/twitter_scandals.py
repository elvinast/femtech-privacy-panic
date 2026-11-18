"""
Twitter — Targeted Scandal Queries
====================================
Бюджет: ~3,700 кредитов = ~246 твитов
Фокус: конкретные скандалы по датам

Запуск:
    python twitter_scandals.py

Добавляет данные к twitter_femtech_FULL.csv (или создаёт новый файл)
"""

import requests
import pandas as pd
import time, os

API_KEY  = "YOUR_API_KEY"
BASE_URL = "https://api.twitterapi.io/twitter/tweet/advanced_search"
HEADERS  = {"X-API-Key": API_KEY}

CREDITS_BUDGET    = 3700
CREDITS_PER_TWEET = 15

# ── Скандалы и ключевые события ──────────────────────────
#
# Хронология:
#  2018  Natural Cycles — UK ICO (Facebook pixel)
#  2019  Maya/MIA — Privacy International (Facebook SDK)
#  2021  Flo FTC settlement (shared data w/ Facebook & Google)
#  2022  Premom — Senate investigation (Umeng, JPush China)
#  2022  Dobbs v. Jackson — period apps scrutiny
#  2025  Flo — $56M California class action settlement
#  2025  Meta — found guilty collecting menstrual data
#
# (query, label, pages, queryType)

SCANDAL_QUERIES = [
    (
        '"flo health" FTC privacy -is:retweet lang:en',
        "SCANDAL: Flo FTC (2021)",
        3, "Latest"
    ),
    (
        '"flo health" settlement lawsuit data -is:retweet lang:en',
        "SCANDAL: Flo $56M CA (2025)",
        3, "Latest"
    ),
    (
        'premom app data privacy -is:retweet lang:en',
        "SCANDAL: Premom privacy",
        2, "Latest"
    ),
    (
        'dobbs "period tracker" OR "period app" OR "flo app" -is:retweet lang:en',
        "SCANDAL: Dobbs + period apps (2022)",
        3, "Latest"
    ),
    (
        '"natural cycles" app privacy -is:retweet lang:en',
        "SCANDAL: Natural Cycles privacy",
        2, "Latest"
    ),
    (
        'facebook menstrual data privacy -is:retweet lang:en',
        "SCANDAL: Meta menstrual data",
        2, "Latest"
    ),
    (
        '"stardust app" OR "stardust period" privacy -is:retweet lang:en',
        "SCANDAL: Stardust",
        1, "Latest"
    ),
]

# ── Relevance filter ──────────────────────────────────────
RELEVANT_KEYWORDS = [
    "flo", "clue", "natural cycles", "premom", "stardust",
    "period", "menstrual", "femtech", "reproductive", "fertility",
    "privacy", "data", "tracking", "health app", "cycle"
]

def is_relevant(text: str) -> bool:
    t = text.lower()
    return any(kw in t for kw in RELEVANT_KEYWORDS)

# ── Budget tracker ────────────────────────────────────────
class Budget:
    def __init__(self, b):
        self.budget = b
        self.spent  = 0
        self.total  = 0

    def charge(self, n):
        c = max(n * CREDITS_PER_TWEET, 15)
        self.spent += c
        self.total += n
        return c

    def ok(self, min_credits=300):
        return (self.budget - self.spent) >= min_credits

    def bar(self):
        pct = self.spent / self.budget * 100
        return f"💳 {self.spent}/{self.budget} ({pct:.0f}%) | 🐦 {self.total} твитов"

# ── Fetch ─────────────────────────────────────────────────
def fetch_page(query, cursor="", qtype="Top"):
    r = requests.get(BASE_URL, headers=HEADERS, params={
        "query": query, "queryType": qtype, "cursor": cursor
    }, timeout=15)
    r.raise_for_status()
    return r.json()

def parse(t, label, qtype):
    a = t.get("author", {})
    return {
        "source": "twitter", "label": label, "query_type": qtype,
        "tweet_id": t.get("id",""), "text": t.get("text",""),
        "created_at": t.get("createdAt",""), "lang": t.get("lang",""),
        "likes": t.get("likeCount",0), "retweets": t.get("retweetCount",0),
        "replies": t.get("replyCount",0), "quotes": t.get("quoteCount",0),
        "views": t.get("viewCount",0), "bookmarks": t.get("bookmarkCount",0),
        "is_reply": t.get("isReply",False),
        "author_name": a.get("name",""), "author_user": a.get("userName",""),
        "author_followers": a.get("followers",0),
        "author_verified": a.get("isBlueVerified",False),
        "url": t.get("url",""),
    }

# ── Main ──────────────────────────────────────────────────
print("=" * 65)
print("  Twitter — Scandal-Focused Collection")
print(f"  Бюджет: {CREDITS_BUDGET} кредитов (~{CREDITS_BUDGET//CREDITS_PER_TWEET} твитов)")
print("=" * 65)

budget     = Budget(CREDITS_BUDGET)
new_tweets = []
seen_ids   = set()

# Загрузить уже собранные id чтобы не дублировать
existing_file = "twitter_femtech_FULL.csv"
if os.path.exists(existing_file):
    existing = pd.read_csv(existing_file)
    seen_ids = set(existing["tweet_id"].astype(str).tolist())
    print(f"  ℹ Загружено {len(seen_ids)} существующих твитов (дубликаты пропустим)\n")

for query, label, max_pages, qtype in SCANDAL_QUERIES:

    if not budget.ok():
        print("\n⚠ Бюджет исчерпан. Останавливаюсь.")
        break

    print(f"\n→ {label}")
    cursor = ""
    page   = 0
    time.sleep(1.5)  # пауза между запросами (сокращена с 3 сек)

    while page < max_pages:
        if not budget.ok(15):
            break
        try:
            data     = fetch_page(query, cursor, qtype)
            tweets   = data.get("tweets", [])
            has_next = data.get("has_next_page", False)
            cursor   = data.get("next_cursor", "")

            new = 0
            skipped = 0
            for t in tweets:
                tid = str(t.get("id",""))
                text = t.get("text","")
                if tid not in seen_ids and is_relevant(text):
                    seen_ids.add(tid)
                    new_tweets.append(parse(t, label, qtype))
                    new += 1
                elif tid not in seen_ids:
                    skipped += 1

            cost = budget.charge(len(tweets))
            print(f"  стр.{page+1}: {new} новых, {skipped} нерелевантных | -{cost} | {budget.bar()}")

            if not has_next:
                break
            page += 1
            time.sleep(1)  # пауза между страницами (сокращена с 2 сек)

        except requests.HTTPError as e:
            if "429" in str(e):
                print(f"  ⚠ Rate limit — жду 10 сек...")
                time.sleep(10)
                continue
            print(f"  ✗ {e}")
            break
        except Exception as e:
            print(f"  ✗ {e}")
            break

# ── Сохранить ─────────────────────────────────────────────
if not new_tweets:
    print("\n⚠ Новых твитов не найдено.")
else:
    df_new = pd.DataFrame(new_tweets)
    df_new["date"] = pd.to_datetime(
        df_new["created_at"],
        format="%a %b %d %H:%M:%S +0000 %Y", errors="coerce"
    ).dt.strftime("%Y-%m-%d")
    df_new["year"]  = df_new["date"].str[:4]
    df_new["month"] = df_new["date"].str[:7]

    # Объединить с существующим файлом
    if os.path.exists(existing_file):
        df_old = pd.read_csv(existing_file)
        df_all = pd.concat([df_old, df_new], ignore_index=True)
    else:
        df_all = df_new

    df_all = df_all.sort_values("likes", ascending=False).reset_index(drop=True)
    df_all.to_csv(existing_file, index=False)

    print("\n" + "=" * 65)
    print(f"  ✅ Новых твитов: {len(df_new)}")
    print(f"  📦 Всего в файле: {len(df_all)}")
    print(f"  💳 Потрачено: {budget.spent}/{budget.budget} кредитов")
    print(f"  💾 Обновлён: {existing_file}")
    print("=" * 65)

    print("\n📊 Новые твиты по скандалам:")
    print(df_new.groupby("label").agg(
        твитов=("tweet_id","count"),
        avg_likes=("likes","mean")
    ).sort_values("твитов", ascending=False).to_string())

    print("\n🔥 Топ-5 новых твитов:")
    for i, row in df_new.nlargest(5,"likes").iterrows():
        print(f"\n  ❤️{row['likes']} 🔁{row['retweets']} ({row.get('date','?')})")
        print(f"  [{row['label']}]")
        print(f"  {str(row['text'])[:130]}...")

    print(f"\n📈 Итоговое распределение по годам:")
    print(df_all.groupby(df_all["year"].astype(str))["tweet_id"].count().sort_index().to_string())
