import os
import sys
import time
import json
import re
import requests
from dotenv import load_dotenv
import tweepy
from near_api.providers import JsonProvider
from near_api.signer import KeyPair, Signer
from near_api.account import Account
from datetime import datetime, timezone

# Load environment variables from .env file
load_dotenv()

# NEAR contract settings (adjust variable names as needed)
CONTRACT_ID = os.getenv("CONTRACT_ID")
ORACLE_ACCOUNT_ID = os.getenv("ORACLE_ACCOUNT_ID")
ORACLE_PRIVATE_KEY = os.getenv("ORACLE_PRIVATE_KEY")
if not (CONTRACT_ID and ORACLE_ACCOUNT_ID and ORACLE_PRIVATE_KEY):
    raise ValueError("Missing one or more NEAR environment variables.")

# Set up NEAR RPC provider and account for view functions
provider = JsonProvider("https://rpc.testnet.near.org")
key_pair = KeyPair(ORACLE_PRIVATE_KEY)
signer = Signer(ORACLE_ACCOUNT_ID, key_pair)
near_account = Account(provider, signer)

# Twitter API credentials
TWITTER_BEARER_TOKEN = os.getenv("TWITTER_BEARER_TOKEN")
TWITTER_API_KEY = os.getenv("TWITTER_API_KEY")
TWITTER_API_SECRET = os.getenv("TWITTER_API_SECRET")
TWITTER_ACCESS_KEY = os.getenv("TWITTER_ACCESS_KEY")
TWITTER_ACCESS_SECRET = os.getenv("TWITTER_ACCESS_SECRET")
TWITTER_USER_ID = os.getenv("TWITTER_USER_ID")  # Your Twitter user ID
WEB_APP_BASE_URL = os.getenv("WEB_APP_BASE_URL")

def parse_endtime_to_ns(endtime_str: str) -> str:
    """
    Parses an end time string in "YYYY-MM-DD HH:MM:SS" format (assumed UTC)
    and returns the epoch time in nanoseconds as a string.
    """
    dt = datetime.strptime(endtime_str, "%Y-%m-%d %H:%M:%S")
    dt = dt.replace(tzinfo=timezone.utc)
    ns = int(dt.timestamp() * 1e9)
    return str(ns)

def get_all_markets():
    """
    Fetch all markets from the NEAR contract using the view_function.
    Expects the contract's "getAllMarkets" method to return a dict with a "result" key.
    """
    try:
        res = near_account.view_function(CONTRACT_ID, "getAllMarkets", {})
        markets = res.get("result", [])
    except Exception as e:
        print("Error calling getAllMarkets:", e)
        markets = []
    return markets


def reply_to_tweet(tweet_id, message):
    """
    Reply to the tweet with the provided message using the Tweepy client.
    """
    try:
        client = tweepy.Client(
            consumer_key=TWITTER_API_KEY,
            consumer_secret=TWITTER_API_SECRET,
            access_token=TWITTER_ACCESS_KEY,
            access_token_secret=TWITTER_ACCESS_SECRET
        )
        response = client.create_tweet(in_reply_to_tweet_id=tweet_id, text=message)
    except Exception as e:
        print("Error replying to tweet:", e)

def reply_all_markets(tweet_id):
    """
    Reply with a list of active (unresolved) markets.
    """
    markets = get_all_markets()
    active_markets = [m for m in markets if not m.get("resolved", False)]
    if not active_markets:
        message = "No current active markets found."
    else:
        lines = []
        for m in active_markets:
            timestamp_seconds = int(m.get("endTime")) / 1e9
            dt = datetime.fromtimestamp(timestamp_seconds, tz=timezone.utc)
            formatted_date = dt.strftime("%Y-%m-%d %H:%M:%S %Z")

            line = f"Name: {m.get('description')} - Endtime: {formatted_date}"
            lines.append(line)
        message = "Active Markets:\n" + "\n".join(lines)
        if len(message) > 280:
            message = message[:277] + "..."
    reply_to_tweet(tweet_id, message)

def reply_address_bets(tweet_id, address):
    """
    Reply with bets for a given address by scanning through active markets.
    """
    markets = get_all_markets()
    active_markets = [m for m in markets if not m.get("resolved", False)]

    lines = []
    for m in active_markets:
        print(m)
        bets = m.get("bets", [])
        user_bets = [bet for bet in bets if bet.get("user") == address]
        for bet in user_bets:
            if bet.get("outcome") == 0:
                outcome = "Yes"
            else:
                outcome = "No"
            lines.append(f"Market: {m.get('description')}, Outcome: {outcome}, Amount {bet.get('amount')}")

    if not lines:
        message = f"No bets found for address {address}."
    else:
        message = f"Bets for {address}:\n" + "\n".join(lines)
        if len(message) > 280:
            message = message[:277] + "..."
    reply_to_tweet(tweet_id, message)


def reply_market_info(tweet_id, description):
    """
    Reply with information for a market matching the provided description (case-insensitive).
    """
    markets = get_all_markets()
    active_markets = [m for m in markets if not m.get("resolved", False)]
    market = None
    for m in active_markets:
        if m.get("description", "").lower() == description.lower():
            market = m
            break
    if market:
        timestamp_seconds = int(market.get("endTime")) / 1e9
        dt = datetime.fromtimestamp(timestamp_seconds, tz=timezone.utc)
        formatted_date = dt.strftime("%Y-%m-%d %H:%M:%S.%f %Z")
        yesPool = int(market.get("yesPool")) / 1e24
        noPool = int(market.get("noPool")) / 1e24
        message = f"Market: {market.get('description')}\nEnds: {formatted_date}\nYes Pool: {yesPool}\nNo Pool: {noPool}"
    else:
        message = f"No active market found with description '{description}'."

    if len(message) > 280:
        message = message[:277] + "..."
    reply_to_tweet(tweet_id, message)

def process_mentions():
    """
    Fetch recent mentions and process commands:
      - /markets: Reply with all current markets.
      - /bets_ADDRESS: Reply with bets for the given address.
      - /market_DESCRIPTION: Reply with market info for a market with the given description.
    """
    client = tweepy.Client(
        consumer_key=TWITTER_API_KEY,
        consumer_secret=TWITTER_API_SECRET,
        access_token=TWITTER_ACCESS_KEY,
        access_token_secret=TWITTER_ACCESS_SECRET
    )
    client2 = tweepy.Client(TWITTER_BEARER_TOKEN)
    if not TWITTER_USER_ID:
        print("TWITTER_USER_ID not set.")
        return

    response = client2.get_users_mentions(TWITTER_USER_ID, max_results=10)
    if not response.data:
        print("No new mentions found.")
        return

    tweets = sorted(
        response.data,
        key=lambda t: datetime.strptime(t.created_at, "%a %b %d %H:%M:%S %z %Y") if t.created_at else datetime.min
    )

    """
    Parse tweet text and extract command details.
    Expected format examples:
    - "@betbotx create sport NBA New York Knics win 2024-03-01 12:00:00"
    - "@betbotx create sport NBA New York Knics > 10 2024-03-01 12:00:00"
    - "@betbotx bet sport MLS LA Galaxy > 1 1.4 yes"
    - "@betbotx markets"
    - "@betbotx bets <address>"
    - "@betbotx market sport NBA New York Knics win"
    """
    for tweet in tweets:
        text = tweet.text.strip()
        text = text.replace("@betbotx", "").strip()
        tokens = text.strip().split()

        if text.startswith("create"):
            end_date = tokens[-2]
            end_time = tokens[-1]
            endtime_str = f"{end_date} {end_time}"
            epoch = parse_endtime_to_ns(endtime_str)
            res = "_".join(tokens[1:-2])
            reply_to_tweet(tweet.id, "Visit: " + WEB_APP_BASE_URL + "/create/" + res + "/" + epoch)
        elif text.startswith("bet"):
            market = " ".join(tokens[1:-2])
            amt = tokens[-2]
            outcome = tokens[-1]
            markets = get_all_markets()
            market = next((m for m in markets if m.get("description", "").lower() == market.lower()), None)

            if market:
                marketId = str(market.get("id"))
                reply_to_tweet(tweet.id, "Visit: " + WEB_APP_BASE_URL + "/bet/" + marketId + "/" + outcome + "/" + amt)
            else:
                reply_to_tweet(tweet.id, "Market not found")
        elif text.startswith("markets"):
            reply_all_markets(tweet.id)
        elif text.startswith("bets"):
            print(tokens[1])
            reply_address_bets(tweet.id, tokens[1])
        elif text.startswith("market"):
            reply_market_info(tweet.id, " ".join(tokens[1:]))
        else:
            reply_to_tweet(tweet.id, "Invalid command")

def main():
    process_mentions()

if __name__ == "__main__":
    # Run one iteration (GitHub Actions can schedule this every 15 minutes)
    main()
