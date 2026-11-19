# FemTech Privacy: The Say–Do Gap Dataset

Data and code accompanying the thesis **"The Privacy Panic: Measuring the Say–Do Gap in FemTech Privacy"** (E. Shamoi, University of Padova, 2026).

The project measures the gap between what period- and fertility-tracking apps **promise** in their privacy policies (the *SAY* side) and how much users **actually trust** them, inferred from the sentiment of their reviews and posts (the *DO* side), across five apps (Flo, Clue, Natural Cycles, Premom, Stardust) from 2016 to 2026.

## Important: how the data is shared


- **App-store reviews** (Google Play, Apple App Store) are provided **in full** (text + rating + labels). They contain **no usernames** or author identifiers.
- **Tweets** are provided with their text and the labels derived in this study, **without any author information** — no names, handles, follower counts, or profile links. Each row keeps its `tweet_id` so the original can be located if needed.
- **No personal data.** No author names, handles, emails, or other identifiers are included anywhere. Survey responses are fully anonymous (no timestamps, no identifiers).

## Repository structure

```
data/
  reviews_labeled.csv      50,768 app-store reviews: text, rating, app, sentiment, topic
  tweets_labeled.csv       14,554 tweets: text + labels, no author information
  workarounds.csv          308 user-suggested privacy workarounds
  policy_scores.json       Per-app privacy-policy scores on 6 dimensions, with quotes
  say_do_gap.csv           SAY, DO, and the standardized Say–Do Gap per app
  topsis_ranking.csv       AHP–TOPSIS ranking of the five policies
  survey_responses.csv     101 anonymous survey responses (EN + IT)
figures/                   All thesis figures (PNG)
```

## Data dictionaries

**reviews_labeled.csv** — `data_source` (google_play/app_store), `app`, `date`, `rating` (1–5), `text`, `sentiment` (positive/negative/neutral), `topic` (BERTopic id, −1 = none), `topic_label`.

**tweets_labeled.csv** — `tweet_id`, `query` (collection query), `query_type`, `source`, `created_at`, `date`, `year`, `month`, `lang`, `is_reply`, `text`, `sentiment`, `topic`, `topic_label`, `likes`, `retweets`, `replies`, `quotes`, `views`, `bookmarks`. Full tweet text is included; **no author information** (name, handle, follower count, verified status, or profile link) is present.

**workarounds.csv** — `source`, `app_or_query`, `date`, `text_or_tweetid` (review text, or `tweet_id:...` for tweets), `workaround` (switch/stop/minimize/manual/technical).

**policy_scores.json** — per app, six dimensions (data-collection clarity, third-party disclosure, user control, data retention, legal basis, plain language), each with a 0–10 score, a reason, and a supporting quote.

## Methods (brief)

Sentiment: GPT-4o-mini (temperature 0), validated against a RoBERTa baseline (Cohen's κ = 0.73). Topics: BERTopic (embeddings → UMAP → HDBSCAN → c-TF-IDF), 67 topics on the privacy subset. Policy scoring: GPT-4o-mini on six dimensions. Policy ranking: AHP–TOPSIS. Say–Do Gap: z(SAY) − z(DO).


## License

**Data and figures** (`data/`, `figures/`): [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/)

Tweet content remains subject to the X/Twitter Terms of Service and belongs to its respective authors; only IDs are shared here.
