"""
Rehydrate tweets from their IDs using the X/Twitter API v2.

Usage:
    export X_BEARER_TOKEN="your_bearer_token"
    python rehydrate_tweets.py ../data/tweets_dehydrated.csv tweets_rehydrated.csv

Requires: pip install tweepy pandas
Only you, with your own API access, can re-download the tweet text. Tweets that
have been deleted or made private will simply be missing from the output.
"""
import os
import sys
import time
import pandas as pd
import tweepy


def main(in_csv: str, out_csv: str) -> None:
    token = os.environ.get("X_BEARER_TOKEN")
    if not token:
        sys.exit("Set X_BEARER_TOKEN in your environment first.")

    client = tweepy.Client(bearer_token=token, wait_on_rate_limit=True)
    ids = pd.read_csv(in_csv)["tweet_id"].astype(str).tolist()

    rows = []
    for i in range(0, len(ids), 100):  # API allows 100 IDs per request
        batch = ids[i:i + 100]
        resp = client.get_tweets(
            batch,
            tweet_fields=["created_at", "public_metrics", "lang"],
        )
        for t in (resp.data or []):
            rows.append({"tweet_id": t.id, "text": t.text, "created_at": t.created_at})
        print(f"  rehydrated {min(i + 100, len(ids))}/{len(ids)}")
        time.sleep(1)

    pd.DataFrame(rows).to_csv(out_csv, index=False)
    print(f"Done: {len(rows)}/{len(ids)} tweets written to {out_csv} "
          f"({len(ids) - len(rows)} unavailable).")


if __name__ == "__main__":
    if len(sys.argv) != 3:
        sys.exit("Usage: python rehydrate_tweets.py <ids.csv> <output.csv>")
    main(sys.argv[1], sys.argv[2])
