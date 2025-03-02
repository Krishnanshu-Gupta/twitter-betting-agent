import os
import time
import json
import subprocess
import requests
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Required environment variables:
# CONTRACT_ID: your deployed NEAR contract account (e.g., "1t2_hacks.testnet")
# ORACLE_ACCOUNT_ID: the NEAR account that the oracle uses to sign resolution transactions
# ODDS_API_KEY: your API key for the Odds API
CONTRACT_ID = os.getenv("CONTRACT_ID")
ORACLE_ACCOUNT_ID = os.getenv("ORACLE_ACCOUNT_ID")
ODDS_API_KEY = os.getenv("ODDS_API_KEY")

if not CONTRACT_ID or not ORACLE_ACCOUNT_ID or not ODDS_API_KEY:
    raise ValueError("Missing required environment variables.")

def get_all_markets():
    """Fetch all markets using the contract's getAllMarkets view function."""
    cmd = ["near", "view", CONTRACT_ID, "getAllMarkets", "{}"]
    result = subprocess.run(cmd, capture_output=True, text=True)
    try:
        markets = json.loads(result.stdout)
    except Exception as e:
        print("Error parsing getAllMarkets output:", e)
        print(result.stdout)
        markets = []
    return markets

def resolve_market_onchain(market_id, outcome_str):
    """Call the contract to resolve the market with the given outcome."""
    args = json.dumps({"marketId": market_id, "outcomeStr": outcome_str})
    cmd = [
        "near", "call", CONTRACT_ID, "resolveMarketWithOutcome", args,
        "--accountId", ORACLE_ACCOUNT_ID,
        "--depositYocto", "0",
        "--gas", "30000000000000"
    ]
    print(f"Resolving market {market_id} with outcome '{outcome_str}'")
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.stderr:
        print("Error resolving market:", result.stderr)
    else:
        print("Market resolved successfully:", result.stdout)

def fetch_sports_data(sport_id):
    """Fetch match data for the given sport_id from the Odds API."""
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
        # Split the description into parts
        parts = market["description"].split()
        if len(parts) < 4:
            print("Invalid sports market description:", market["description"])
            return "no"

        # The first part is "sport" and the second is the league.
        league = parts[1].upper()  # e.g., "NBA"

        # Identify the condition token (which can be "win", ">", or "<")
        conditions = {"win", ">", "<"}
        condition_index = None
        for i in range(2, len(parts)):
            if parts[i].lower() in conditions:
                condition_index = i
                break

        if condition_index is None:
            print("No valid condition found in sports market description:", market["description"])
            return "no"

        # The team name consists of all tokens between index 2 and the condition token.
        team_tokens = parts[2:condition_index]
        if not team_tokens:
            print("No team name found in sports market description:", market["description"])
            return "no"
        team = " ".join(team_tokens)

        condition = parts[condition_index].lower()
        threshold = None
        if condition == "win":
            # no threshold needed for a simple win market
            pass
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

        # Extract scores.
        scores = match_found.get("scores", [])
        if not scores or len(scores) < 2:
            print("No valid scores found in match")
            return "no"

        # Determine team's and opponent's score.
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

        # For margin-based conditions, first check that the team won.
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

def resolve_market_logic(market):
    desc = market["description"].lower()
    if desc.startswith("crypto"):
        # Crypto resolution logic goes here (omitted for brevity)
        print("Crypto resolution not implemented in this example.")
        return "no"
    elif desc.startswith("sport"):
        return resolve_sports_market(market)
    else:
        print("Unknown market type in description:", desc)
        return "no"

def process_expired_markets():
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
    print("Contract ID:", CONTRACT_ID)
    print("Oracle account ID:", ORACLE_ACCOUNT_ID)
    print("Odds API key:", ODDS_API_KEY)
    process_expired_markets()

if __name__ == "__main__":
    main()