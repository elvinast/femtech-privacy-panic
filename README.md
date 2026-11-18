# FemTech Privacy: The Say–Do Gap Dataset

Data and code accompanying the thesis **"The Privacy Panic: Measuring the Say–Do Gap in FemTech Privacy"** (E. Shamoi, University of Padova, 2026), and the associated research article (in preparation).

The project measures the gap between what period- and fertility-tracking apps **promise** in their privacy policies (the *SAY* side) and how much users **actually trust** them, inferred from the sentiment of their reviews and posts (the *DO* side), across five apps (Flo, Clue, Natural Cycles, Premom, Stardust) from 2016 to 2026.

## ⚠️ Important: how the data is shared

This repository follows platform terms of service and data-protection good practice:

- **App-store reviews** (Google Play, Apple App Store) are provided **in full** (text + rating + labels). They contain **no usernames** or author identifiers.
- **Tweets are NOT redistributed as text.** Per the X/Twitter Developer Agreement, only **tweet IDs** are published, together with the labels derived in this study. Use the IDs to re-download ("rehydrate") the original tweets through the X API (see `code/rehydrate_tweets.py`). Tweets that have since been deleted or made private will be unavailable — this is by design.
- **No personal data.** No author names, handles, emails, or other identifiers are included anywhere. Survey responses are fully anonymous (no timestamps, no identifiers).

## Repository structure

```
data/
  reviews_labeled.csv      50,768 app-store reviews: text, rating, app, sentiment, topic
  tweets_dehydrated.csv    14,554 tweet IDs + labels (no text/author) — rehydrate via X API
  workarounds.csv          308 user-suggested privacy workarounds (tweets shown as IDs)
  policy_scores.json       Per-app privacy-policy scores on 6 dimensions, with quotes
  say_do_gap.csv           SAY, DO, and the standardized Say–Do Gap per app
  topsis_ranking.csv       AHP–TOPSIS ranking of the five policies
  survey_responses.csv     101 anonymous survey responses (EN + IT)
figures/                   All thesis figures (PNG)
```

## Data dictionaries

**reviews_labeled.csv** — `data_source` (google_play/app_store), `app`, `date`, `rating` (1–5), `text`, `sentiment` (positive/negative/neutral), `topic` (BERTopic id, −1 = none), `topic_label`.

**tweets_dehydrated.csv** — `tweet_id`, `query` (collection query), `date`, `sentiment`, `topic`, `topic_label`, `likes`, `retweets`, `views`. *No tweet text is included* — rehydrate with the ID.

**workarounds.csv** — `source`, `app_or_query`, `date`, `text_or_tweetid` (review text, or `tweet_id:...` for tweets), `workaround` (switch/stop/minimize/manual/technical).

**policy_scores.json** — per app, six dimensions (data-collection clarity, third-party disclosure, user control, data retention, legal basis, plain language), each with a 0–10 score, a reason, and a supporting quote.

## Methods (brief)

Sentiment: GPT-4o-mini (temperature 0), validated against a RoBERTa baseline (Cohen's κ = 0.73). Topics: BERTopic (embeddings → UMAP → HDBSCAN → c-TF-IDF), 67 topics on the privacy subset. Policy scoring: GPT-4o-mini on six dimensions. Policy ranking: AHP–TOPSIS. Say–Do Gap: z(SAY) − z(DO).

## Rehydrating the tweets

The tweet text is not included; use the IDs in `tweets_dehydrated.csv` to re-download
the originals through the X API (`pip install tweepy pandas`):

```python
import tweepy, pandas as pd
client = tweepy.Client(bearer_token="YOUR_X_BEARER_TOKEN", wait_on_rate_limit=True)
ids = pd.read_csv("data/tweets_dehydrated.csv")["tweet_id"].astype(str).tolist()
rows = []
for i in range(0, len(ids), 100):              # 100 IDs per request
    for t in (client.get_tweets(ids[i:i+100], tweet_fields=["created_at"]).data or []):
        rows.append({"tweet_id": t.id, "text": t.text})
pd.DataFrame(rows).to_csv("tweets_rehydrated.csv", index=False)
```

Tweets that have since been deleted or made private will be unavailable — this is by design.

## Citation

If you use this dataset, please cite:

> Shamoi, E. (2026). *The Privacy Panic: Measuring the Say–Do Gap in FemTech Privacy.* University of Padova.

(A citation for the journal article will be added once published.)

## License

**Data and figures** (`data/`, `figures/`): [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/)

Tweet content remains subject to the X/Twitter Terms of Service and belongs to its respective authors; only IDs are shared here.
