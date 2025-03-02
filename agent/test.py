import os
from dotenv import load_dotenv
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

# Ensure necessary environment variables are set
if not (CONTRACT_ID and ORACLE_ACCOUNT_ID and ORACLE_PRIVATE_KEY):
    raise ValueError("Missing one or more NEAR environment variables.")

# Set up NEAR RPC provider and account for view functions
provider = JsonProvider("https://rpc.testnet.near.org")
key_pair = KeyPair(ORACLE_PRIVATE_KEY)
signer = Signer(ORACLE_ACCOUNT_ID, key_pair)
near_account = Account(provider, signer)

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
    """
    try:
        res = near_account.view_function(CONTRACT_ID, "getAllMarkets", {})
        markets = res.get("result", [])
        print(f"Fetched {len(markets)} markets.")
        return markets
    except Exception as e:
        print("Error calling getAllMarkets:", e)
        return []


def reply_all_markets():
    """
    Print a list of active (unresolved) markets.
    """
    markets = get_all_markets()
    active_markets = [m for m in markets if not m.get("resolved", False)]

    if not active_markets:
        message = "No current active markets found."
    else:
        lines = []
        for m in active_markets:
            try:
                # Convert nanosecond epoch time (string) to int, then to seconds
                timestamp_seconds = int(m.get("endTime")) / 1e9

                # Convert to timezone-aware datetime object
                dt = datetime.fromtimestamp(timestamp_seconds, tz=timezone.utc)

                # Format datetime
                formatted_date = dt.strftime("%Y-%m-%d %H:%M:%S %Z")

                # Append formatted string to lines list
                lines.append(f"Name: {m.get('description')} - Id: {m.get('id')} - Endtime: {formatted_date}")
            except (ValueError, TypeError):
                lines.append(f"Name: {m.get('description')} - Id: {m.get('id')} - Endtime: Invalid Timestamp")

        message = "Active Markets:\n" + "\n".join(lines)

        # Ensure message does not exceed Twitter's 280-character limit
        if len(message) > 280:
            message = message[:277] + "..."

    print(message)


def reply_address_bets(address):
    """
    Print bets for a given address by scanning through active markets.
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

    print(message)


def reply_market_info(description):
    """
    Print information for a market matching the provided description.
    """
    markets = get_all_markets()
    active_markets = [m for m in markets if not m.get("resolved", False)]

    market = next((m for m in active_markets if m.get("description", "").lower() == description.lower()), None)

    if market:
        timestamp_seconds = int(market.get("endTime")) / 1e9
        dt = datetime.fromtimestamp(timestamp_seconds, tz=timezone.utc)
        formatted_date = dt.strftime("%Y-%m-%d %H:%M:%S.%f %Z")
        message = f"Market: {market.get('description')}\nEnds: {formatted_date}\nYes Pool: {market.get('yesPool')}\nNo Pool: {market.get('noPool')}"
    else:
        message = f"No active market found with description '{description}'."

    if len(message) > 280:
        message = message[:277] + "..."

    print(message)


def parse_endtime_to_ns(endtime_str: str) -> str:
    """
    Parses an end time string in "YYYY-MM-DD HH:MM:SS" format (assumed UTC)
    and returns the epoch time in nanoseconds as a string.
    """
    dt = datetime.strptime(endtime_str, "%Y-%m-%d %H:%M:%S")
    dt = dt.replace(tzinfo=timezone.utc)
    ns = int(dt.timestamp() * 1e9)
    return str(ns)

def test_functions():
    """
    Run all the testing functions.
    """
    stri = "@betbotx bet sport NBA New York Knicks %3C 10 1.4 yes"
    text = stri.strip()
    text = text.replace("@betbotx", "").strip()
    tokens = text.strip().split()

    if text.startswith("create"):
        end_date = tokens[-2]
        end_time = tokens[-1]
        endtime_str = f"{end_date} {end_time}"
        epoch = parse_endtime_to_ns(endtime_str)
        res = "_".join(tokens[1:-2])
        print("url" + "/create/" + res + "/" + epoch)

    if text.startswith("bet"):
        market = "_".join(tokens[1:-2])
        amt = tokens[-2]
        outcome = tokens[-1]
        if outcome == "yes":
            outcome = "0"
        else:
            outcome = "1"
        markets = get_all_markets()
        market = next((m for m in markets if m.get("description", "").lower() == market.lower()), None)
        if market:
            marketId = str(market.get("id"))
            print("url" + "/bet/" + marketId + "/" + outcome + "/" + amt)
        else:
            print("Market not found")


if __name__ == "__main__":
    test_functions()
