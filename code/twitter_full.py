"""
Twitter FemTech Privacy Dataset Collector
==========================================
Бюджет: 9,000 кредитов = ~600 твитов (15 кредитов/твит)
Цель: максимальное покрытие тем для тезиса

Запуск:
    pip install requests pandas
    python twitter_full.py

Результат: twitter_femtech_FULL.csv
"""

import requests
import pandas as pd
import time
from datetime import datetime

# ─── API KEY ─────────────────────────────────────────────
API_KEY = "YOUR_API_KEY"
# ─────────────────────────────────────────────────────────

BASE_URL = "https://api.twitterapi.io/twitter/tweet/advanced_search"
HEADERS  = {"X-API-Key": API_KEY}

CREDITS_BUDGET  = 9000
CREDITS_PER_TWEET = 15
MAX_TWEETS = CREDITS_BUDGET // CREDITS_PER_TWEET  # = 600

# ── Запросы: 12 тем × 2-3 страницы = ~560 твитов ────────
#
# Охватываем:
#  A) Конкретные приложения
#  B) Ключевые события (FTC, Dobbs, Premom-China)
#  C) Широкие темы (reproductive data, menstrual data)
#  D) Хэштеги (#femtech, #periodtracker)
#  E) User reactions & concerns
#
# queryType = "Top"    → самые вирусные твиты (лайки/RT)
# queryType = "Latest" → последние по времени
#
# (query, label, pages, queryType)
QUERIES = [
    # ── A: Конкретные приложения ──────────────────────────
    (
        '"flo app" OR "flo health" privacy data -is:retweet lang:en',
        "Flo — privacy",
        3, "Top"
    ),
    (
        '"clue app" OR "clue period" privacy data -is:retweet lang:en',
        "Clue — privacy",
        2, "Top"
    ),
    (
        '"natural cycles" data privacy -is:retweet lang:en',
        "Natural Cycles — privacy",
        2, "Top"
    ),
    (
        '"premom" data privacy -is:retweet lang:en',
        "Premom — privacy",
        2, "Top"
    ),
    (
        '"stardust app" OR "stardust period" privacy -is:retweet lang:en',
        "Stardust — privacy",
        1, "Top"
    ),

    # ── B: Ключевые события ───────────────────────────────
    (
        '"flo" FTC settlement data -is:retweet lang:en',
        "EVENT: Flo FTC 2021",
        3, "Top"
    ),
    (
        'dobbs "period app" OR "period tracker" data -is:retweet lang:en',
        "EVENT: Dobbs + period apps",
        3, "Top"
    ),
    (
        '"premom" china data -is:retweet lang:en',
        "EVENT: Premom China 2022",
        2, "Top"
    ),
    (
        'period tracker "data breach" OR "data leak" -is:retweet lang:en',
        "EVENT: Data breaches",
        2, "Top"
    ),

    # ── C: Широкие тематические запросы ──────────────────
    (
        '"reproductive data" privacy surveillance -is:retweet lang:en',
        "Reproductive data privacy",
        2, "Top"
    ),
    (
        '"menstrual data" privacy -is:retweet lang:en',
        "Menstrual data privacy",
        2, "Top"
    ),
    (
        '"period tracking" surveillance privacy -is:retweet lang:en',
        "Period tracking surveillance",
        2, "Latest"
    ),

    # ── D: Хэштеги ────────────────────────────────────────
    (
        '#femtech privacy data -is:retweet lang:en',
        "Hashtag: #femtech privacy",
        2, "Top"
    ),
    (
        '#periodtracker data privacy -is:retweet lang:en',
        "Hashtag: #periodtracker",
        2, "Latest"
    ),

    # ── E: User concerns & reactions ──────────────────────
    (
        '"period app" "selling data" OR "sharing data" -is:retweet lang:en',
        "Users: data selling concern",
        2, "Top"
    ),
    (
        'femtech "third party" data privacy -is:retweet lang:en',
        "FemTech third-party sharing",
        2, "Latest"
    ),
]

# ── Трекер бюджета ────────────────────────────────────────
class BudgetTracker:
    def __init__(self, budget):
        self.budget  = budget
        self.spent   = 0
        self.tweets  = 0

    def charge(self, n_tweets):
        cost = max(n_tweets * CREDITS_PER_TWEET, 15)  # минимум 15 кредитов
        self.spent  += cost
        self.tweets += n_tweets
        return cost

    def remaining(self):
        return self.budget - self.spent

    def status(self):
        pct = self.spent / self.budget * 100
        return (f"💳 Кредиты: {self.spent}/{self.budget} ({pct:.0f}%)  "
                f"| 🐦 Твитов: {self.tweets}  "
                f"| Остаток: {self.remaining()}")

# ── Функции ───────────────────────────────────────────────
def fetch_page(query, cursor="", query_type="Latest"):
    params = {
        "query":     query,
        "queryType": query_type,
        "cursor":    cursor,
    }
    r = requests.get(BASE_URL, headers=HEADERS, params=params, timeout=15)
    r.raise_for_status()
    return r.json()


def parse_tweet(t, label, query_type):
    author = t.get("author", {})
    return {
        "source":            "twitter",
        "label":             label,
        "query_type":        query_type,
        "tweet_id":          t.get("id", ""),
        "text":              t.get("text", ""),
        "created_at":        t.get("createdAt", ""),
        "lang":              t.get("lang", ""),
        "likes":             t.get("likeCount", 0),
        "retweets":          t.get("retweetCount", 0),
        "replies":           t.get("replyCount", 0),
        "quotes":            t.get("quoteCount", 0),
        "views":             t.get("viewCount", 0),
        "bookmarks":         t.get("bookmarkCount", 0),
        "is_reply":          t.get("isReply", False),
        "author_name":       author.get("name", ""),
        "author_user":       author.get("userName", ""),
        "author_followers":  author.get("followers", 0),
        "author_verified":   author.get("isBlueVerified", False),
        "url":               t.get("url", ""),
    }

# ── Main ──────────────────────────────────────────────────
print("=" * 65)
print("  Twitter FemTech Privacy Dataset — Full Collection")
print(f"  Бюджет: {CREDITS_BUDGET} кредитов (~{MAX_TWEETS} твитов)")
print("=" * 65)

budget  = BudgetTracker(CREDITS_BUDGET)
all_tweets = []
seen_ids   = set()

for query, label, max_pages, q_type in QUERIES:

    # Проверка бюджета перед запросом
    if budget.remaining() < 300:  # минимум на 1 запрос
        print(f"\n⚠ Бюджет почти исчерпан. Останавливаюсь.")
        break

    print(f"\n→ [{q_type}] {label}")
    cursor = ""
    page   = 0

    time.sleep(3)  # пауза между темами

    while page < max_pages:

        if budget.remaining() < 15:
            print("  ⚠ Бюджет исчерпан!")
            break

        try:
            data     = fetch_page(query, cursor, q_type)
            tweets   = data.get("tweets", [])
            has_next = data.get("has_next_page", False)
            cursor   = data.get("next_cursor", "")

            new = 0
            for t in tweets:
                if t["id"] not in seen_ids:
                    seen_ids.add(t["id"])
                    all_tweets.append(parse_tweet(t, label, q_type))
                    new += 1

            cost = budget.charge(len(tweets))
            print(f"  стр.{page+1}: {new} новых | -{cost} кредитов | {budget.status()}")

            if not has_next:
                break

            page += 1
            time.sleep(2)

        except requests.HTTPError as e:
            if "429" in str(e):
                print(f"  ⚠ Rate limit — жду 20 сек...")
                time.sleep(20)
                continue
            print(f"  ✗ HTTP ошибка: {e}")
            break
        except Exception as e:
            print(f"  ✗ Ошибка: {e}")
            break

# ── Сохранить ─────────────────────────────────────────────
df = pd.DataFrame(all_tweets)

if df.empty:
    print("\n❌ Нет данных. Проверь API ключ.")
    exit(1)

df["date"] = pd.to_datetime(
    df["created_at"], format="%a %b %d %H:%M:%S +0000 %Y", errors="coerce"
).dt.strftime("%Y-%m-%d")

df["year"]  = df["date"].str[:4]
df["month"] = df["date"].str[:7]

# Сортируем по лайкам
df = df.sort_values("likes", ascending=False).reset_index(drop=True)

out = "twitter_femtech_FULL.csv"
df.to_csv(out, index=False)

# ── Итоги ─────────────────────────────────────────────────
print("\n" + "=" * 65)
print(f"  ✅ ИТОГО: {len(df)} уникальных твитов")
print(f"  💳 Потрачено: {budget.spent}/{budget.budget} кредитов")
print(f"  💾 Сохранено в: {out}")
print("=" * 65)

print("\n📊 По темам:")
summary = df.groupby("label").agg(
    твитов=("tweet_id","count"),
    avg_likes=("likes","mean"),
    avg_rt=("retweets","mean")
).sort_values("твитов", ascending=False)
print(summary.to_string())

print(f"\n📅 Период: {df['date'].min()} → {df['date'].max()}")

print("\n🔥 Топ-10 твитов по лайкам:")
top = df.head(10)[["label","text","likes","retweets","views","date"]]
for i, row in top.iterrows():
    print(f"\n  #{i+1} ❤️{row['likes']} 🔁{row['retweets']} 👁{row['views']} ({row['date']})")
    print(f"  [{row['label']}]")
    print(f"  {str(row['text'])[:130]}...")

print(f"\n📈 По годам:")
print(df.groupby("year")["tweet_id"].count().sort_index().to_string())
