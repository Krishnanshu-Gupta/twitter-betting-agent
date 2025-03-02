import os
import time
import json
import requests
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Required environment variables
CONTRACT_ID = os.getenv("CONTRACT_ID")
ORACLE_ACCOUNT_ID = os.getenv("ORACLE_ACCOUNT_ID")
ODDS_API_KEY = os.getenv("ODDS_API_KEY")
ORACLE_PRIVATE_KEY = os.getenv("ORACLE_PRIVATE_KEY")

if not (CONTRACT_ID and ORACLE_ACCOUNT_ID and ODDS_API_KEY and ORACLE_PRIVATE_KEY):
    raise ValueError("Missing one or more required environment variables.")

# Import near_api classes
from near_api.providers import JsonProvider
from near_api.signer import KeyPair, Signer
from near_api.account import Account

# Set up NEAR RPC provider (using testnet endpoint)
provider = JsonProvider("https://rpc.testnet.near.org")

# Create a key pair and signer for the oracle account
key_pair = KeyPair(ORACLE_PRIVATE_KEY)
signer = Signer(ORACLE_ACCOUNT_ID, key_pair)

# Create an account object for interacting with the contract
oracle_account = Account(provider, signer)

def get_all_markets():
    """
    Fetch all markets using the contract's getAllMarkets view function.
    The near_api call returns a dictionary that includes a "result" key,
    which contains the list of markets.
    """
    try:
        res = oracle_account.view_function(CONTRACT_ID, "getAllMarkets", {})
        # Extract the list of markets from the "result" key
        markets = res.get("result", [])
    except Exception as e:
        print("Error calling getAllMarkets:", e)
        markets = []
    return markets

def resolve_market_onchain(market_id, outcome_str):
    """
    Call the contract to resolve the market with the given outcome.
    Uses the function_call method from near_api.
    """
    args = {"marketId": market_id, "outcomeStr": outcome_str}
    try:
        result = oracle_account.function_call(
            CONTRACT_ID,
            "resolveMarketWithOutcome",
            args,
            gas=30000000000000,
            amount=0
        )
        print(f"Market {market_id} resolved with outcome '{outcome_str}':", result)
    except Exception as e:
        print(f"Error resolving market {market_id}:", e)

def fetch_sports_data(sport_id):
    """
    Fetch match data for the given sport_id from the Odds API.
    """
    url = f"https://api.the-odds-api.com/v4/sports/{sport_id}/scores/?daysFrom=1&apiKey={ODDS_API_KEY}"
    try:
        response = requests.get(url)
        data = response.json()
        return data
    except Exception as e:
        print("Error fetching Odds API data:", e)
        return []

def resolve_sports_market(market):
    """
    Resolve a sports market.
    Expected market description formats:
       "sport NBA Lakers win"         -> check if Lakers won
       "sport NBA Lakers > 10"          -> check if Lakers won by more than 10 points
       "sport NBA New York Knicks < 10" -> check if Knicks won by less than 10 points
    """
    try:
        parts = market["description"].split()
        if len(parts) < 4:
            print("Invalid sports market description:", market["description"])
            return "no"

        # The first part is "sport" and the second is the league.
        league = parts[1].upper()

        # Identify the condition token ("win", ">", or "<")
        conditions = {"win", ">", "<"}
        condition_index = None
        for i in range(2, len(parts)):
            if parts[i].lower() in conditions:
                condition_index = i
                break

        if condition_index is None:
            print("No valid condition found in sports market description:", market["description"])
            return "no"

        # The team name is all tokens between index 2 and the condition token.
        team_tokens = parts[2:condition_index]
        if not team_tokens:
            print("No team name found in sports market description:", market["description"])
            return "no"
        team = " ".join(team_tokens)

        condition = parts[condition_index].lower()
        threshold = None
        if condition == "win":
            pass  # no threshold needed
        elif condition in {">", "<"}:
            if len(parts) <= condition_index + 1:
                print("Missing threshold in sports market description")
                return "no"
            try:
                threshold = float(parts[condition_index + 1])
            except:
                print("Invalid threshold value in sports market description")
                return "no"
        else:
            print("Unsupported condition in sports market description:", condition)
            return "no"

        # Map league to Odds API sport ID.
        sport_mapping = {
            "NBA": "basketball_nba",
            "MLS": "soccer_usa_mls",
            "MLB": "baseball_mlb",
            "EFL": "soccer_england_efl_cup",
            "EPL": "soccer_epl"
        }
        sport_id = sport_mapping.get(league)
        if not sport_id:
            print("League not supported:", league)
            return "no"

        data = fetch_sports_data(sport_id)
        if not data:
            print("No data returned from Odds API.")
            return "no"

        # Filter for completed matches involving the team.
        match_found = None
        for match in data:
            if not match.get("completed", False):
                continue
            home_team = match.get("home_team", "")
            away_team = match.get("away_team", "")
            if team.lower() in home_team.lower() or team.lower() in away_team.lower():
                match_found = match
                break

        if not match_found:
            print("No completed match found for team", team)
            return "no"

        scores = match_found.get("scores", [])
        if not scores or len(scores) < 2:
            print("No valid scores found in match")
            return "no"

        team_score = None
        opponent_score = None
        home_team = match_found.get("home_team", "")
        away_team = match_found.get("away_team", "")
        for score_entry in scores:
            name = score_entry.get("name", "")
            try:
                score_val = int(score_entry.get("score", "0"))
            except:
                score_val = 0
            if team.lower() in name.lower():
                team_score = score_val
            else:
                opponent_score = score_val

        if team_score is None or opponent_score is None:
            print("Could not determine scores for team", team)
            return "no"

        print(f"Match: {home_team} vs {away_team}. {team} score: {team_score}, Opponent score: {opponent_score}")

        if condition == "win":
            return "yes" if team_score > opponent_score else "no"
        elif condition == ">":
            if team_score <= opponent_score:
                return "no"
            margin = team_score - opponent_score
            return "yes" if margin > threshold else "no"
        elif condition == "<":
            if team_score <= opponent_score:
                return "no"
            margin = team_score - opponent_score
            return "yes" if margin < threshold else "no"
        else:
            return "no"
    except Exception as e:
        print("Error in resolve_sports_market:", e)
        return "no"

def fetch_crypto_price(asset):
    """
    Fetch the current price of the asset (e.g. "ETH") using CoinGecko API.
    CoinGecko uses lowercase IDs, so ensure you pass the asset in lowercase.
    """
    url = f"https://api.coingecko.com/api/v3/simple/price?ids={asset.lower()}&vs_currencies=usd"
    try:
        response = requests.get(url)
        data = response.json()
        price = data[asset.lower()]["usd"]
        return price
    except Exception as e:
        print("Error fetching crypto price:", e)
        return None

def resolve_crypto_market(market):
    """
    Parse market description of the form: "crypto ETH > 80000"
    and determine outcome by comparing the current price.
    """
    try:
        # Split description into parts.
        # Expecting format: "crypto ETH > 80000"
        parts = market["description"].split()
        if len(parts) < 4:
            print("Description format invalid for crypto market:", market["description"])
            return "no"
        asset = parts[1]      # e.g., "ETH"
        operator = parts[2]   # e.g., ">"
        threshold = float(parts[3])
        current_price = fetch_crypto_price(asset)
        if current_price is None:
            return "no"
        print(f"Crypto market: {asset} current price = {current_price}, threshold = {threshold}")
        if operator == ">":
            return "yes" if current_price > threshold else "no"
        elif operator == "<":
            return "yes" if current_price < threshold else "no"
        elif operator == "=":
            # For equality, you might want to allow a small delta.
            delta = 0.01 * threshold
            return "yes" if abs(current_price - threshold) < delta else "no"
        else:
            print("Unknown operator in crypto market:", operator)
            return "no"
    except Exception as e:
        print("Error resolving crypto market:", e)
        return "no"

def resolve_market_logic(market):
    """
    Determine the resolution outcome for a market.
    For crypto markets (not implemented) returns "no".
    For sport markets, calls resolve_sports_market.
    """
    desc = market["description"].lower()
    if desc.startswith("crypto"):
        print("Crypto resolution not implemented in this example.")
        return resolve_crypto_market(market)
    elif desc.startswith("sport"):
        return resolve_sports_market(market)
    else:
        print("Unknown market type in description:", desc)
        return "no"

def process_expired_markets():
    """
    Fetch all markets and, for any unresolved market whose endTime has passed,
    determine the outcome and resolve it onchain.
    """
    markets = get_all_markets()
    now_ns = int(time.time() * 1e9)
    for market in markets:
        if not market.get("resolved", False):
            market_end = int(market.get("endTime", "0"))
            if now_ns > market_end:
                print(f"Market {market['id']} expired. Description: {market['description']}")
                outcome = resolve_market_logic(market)
                print(f"Determined outcome for market {market['id']}: {outcome}")
                resolve_market_onchain(market["id"], outcome)

def main():
    print("Polling contract for expired, unresolved markets...")
    process_expired_markets()

if __name__ == "__main__":
    main()
