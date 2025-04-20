# BetBotX

**Social betting on Twitter—wager on sports & crypto with blockchain‐secured markets, real‑time resolution, and transparent payouts.**

---

## Table of Contents

1. [Overview](#overview)  
2. [Features](#features)
3. [What It Does?](#what-it-does)
4. [How I Built It?](#how-i-built-it)
5. [Architecture](#architecture)  
6. [Bot Commands](#bot-commands)  
7. [Prerequisites](#prerequisites)  
8. [Setup & Installation](#setup--installation)  
   - [1. Smart Contract](#1-smart-contract)  
   - [2. Twitter Bot](#2-twitter-bot)  
   - [3. Off‑Chain Oracle Service](#3-off‑chain-oracle-service)  
   - [4. Web Dashboard](#4-web-dashboard)  
9. [Running Locally](#running-locally)  
10. [Deployment Guide](#deployment-guide)  
11. [Troubleshooting](#troubleshooting)  
12. [Contributing](#contributing)  
13. [License](#license)  

---

## Overview

BetBotX is a decentralized betting platform that lets you create and join wagering markets for sports and cryptocurrencies—all via simple Twitter commands. Behind the scenes, smart contracts on NEAR manage bets and automated payouts, while an off‑chain oracle fetches real‑world data (Odds API, CoinGecko) to settle markets.

---

## Features

- **Tweet‑Native Markets:** Create betting markets directly from Twitter mentions, and place wagers, view markets, and more.
- **On‑Chain Security:** All bets and payouts are handled via NEAR smart contracts.  
- **Automated Resolution:** An off‑chain oracle service pulls real‑time sports/crypto data to resolve markets.  
- **User Dashboard:** React web app displays active markets, odds, and pools, with NEAR Wallet integration.  
- **Extensible:** Support for sports (NBA, MLS, MLB, EFL Cup, EPL) and crypto; more markets coming soon.

---

## What It Does

BetBotX brings decentralized betting directly to your Twitter timeline:

- **Create Markets**  
  Instantly launch a new market on sports, crypto, or any upcoming event by tweeting a single command. Seamlessly hand off to our web app for NEAR Wallet authentication and secure market creation.

- **Place Bets**  
  Stake NEAR tokens on your predictions via tweet commands. Behind the scenes, the web app handles transaction signing so you can wager from anywhere without leaving Twitter.

- **View Market Data**  
  - `@betbotx markets` shows all active markets.  
  - `@betbotx market <market>` displays full details (description, pools, odds).  
  - `@betbotx bets <address>` lists every bet placed by a NEAR account.  

- **Automated Resolution & Payouts**  
  Our off‑chain oracle polls real‑world data—sports scores via The Odds API and crypto prices via CoinGecko—then calls the smart contract to settle bets and distribute winnings transparently on NEAR.

- **Real‑Time Web Dashboard**  
  A React‑based dashboard visualizes every market’s status, odds, and pool sizes. It also powers the wallet‑connect and transaction‑sign flow for both market creation and bet placement.

---

## How I Built It

1. **NEAR Smart Contract (TypeScript / near‑sdk‑js)**  
   - Designed on‑chain data structures for markets and bets.  
   - Implemented `createMarket`, `placeBet`, and `resolveMarketWithOutcome` with automatic escrow and payout logic.  
   - Added read‑only views (`getAllMarkets`, `getMarket`) for easy data queries.

2. **Twitter Agent (Python / Tweepy)**  
   - Listens for mentions every 15 minutes (free‑tier limits).  
   - Parses create/bet/view commands and invokes NEAR CLI calls.  
   - Replies on Twitter with confirmations or error messages, keeping users in the loop.

3. **Off‑Chain Oracle Service (Python)**  
   - Scheduled worker polls expired, unresolved markets.  
   - Fetches live data from The Odds API for sports and CoinGecko for crypto.  
   - Determines “yes”/“no” outcomes and triggers on‑chain resolution via NEAR CLI.

4. **Web Dashboard (React)**  
   - Displays live market listings, odds calculations, and pool breakdowns.  
   - Integrates NEAR Wallet for user authentication and transaction signing.  
   - Accepts URL callbacks from Twitter mentions to complete create/​bet flows in‑browser.

---

## Architecture

```text
+-------------+    Tweets/DMs     +-------------+    NEAR RPC    +----------------+
|  Twitter    | --------------→   |  Twitter    | --------------→|  NEAR Contract |
|   Bot       |   create/bet cmd  |   Agent     |  ←-------------|  (Prediction    |
+-------------+                   +-------------+   tx calls     |   Market)      |
       ↓                                                    ↑    +----------------+
  Command URLs                                             |         ↑
       ↓                                                    |         |
+-------------+    HTTP    +-----------------+              |         |
|  Web App    |←-----------|  Off‑Chain      |              |         |
|  (React)    |  triggers  |  Oracle Service |--------------+         |
+-------------+            +-----------------+     view fn’s          |
       ↑                                                             |
       |                                                             |
       +-------------------------------------------------------------+
                              Near Wallet  
```

---

## Bot Commands

### Create Market
```
@betbotx create <type> <league> <identifier> <condition> <UTC time>
```
- **type**: `sport` or `crypto`  
- **league**: e.g. `NBA`, `MLS`, `MLB`, `EFL Cup`, `EPL`  
- **identifier**: team name (for sports) or asset (for crypto)  
- **condition**: `win` or a comparison like `> 10`  
- **UTC time**: `YYYY-MM-DD HH:MM:SS`  

**Examples:**
```
@betbotx create sport NBA Lakers win 2025-03-01 12:00:00
@betbotx create sport NBA Lakers > 10 2025-03-01 12:00:00
@betbotx create crypto ethereum > 2600 2025-03-05 12:00:00
```

### Place Bet
```
@betbotx bet <market> <amount> <outcome>
```
- **market**: full market descriptor (same as creation)  
- **amount**: amount in NEAR  
- **outcome**: `yes` or `no`  

**Example:**
```
@betbotx bet sport MLS LA Galaxy > 1 1.4 yes
```

### Other Commands
- `@betbotx markets` → List all active markets  
- `@betbotx bets <address>` → Show bets by account  
- `@betbotx market <market>` → Show details for a specific market  

---

## Prerequisites

- **Node.js ≥ 16**  
- **npm or yarn**  
- **Python 3.8+**  
- **NEAR CLI** (installed & logged in)  
- **Docker** (for containerization)  
- **Twitter Developer Account** (API keys + tokens)  
- **Google Cloud / Heroku / VPS** (for hosting bot & oracle)  

---

## Setup & Installation

### 1. Smart Contract

```bash
# Clone repo
git clone https://github.com/yourusername/betbotx.git
cd betbotx/contract

# Install dependencies & build
npm install
npm run build

# Deploy to NEAR testnet
near deploy \
  --accountId <YOUR_CONTRACT>.testnet \
  --wasmFile build/main.wasm
```

### 2. Twitter Bot

```bash
cd ../twitter-bot

# Python deps
pip install -r requirements.txt

# Create .env
cat > .env <<EOF
TWITTER_BEARER_TOKEN=...
TWITTER_API_KEY=...
TWITTER_API_KEY_SECRET=...
TWITTER_ACCESS_TOKEN=...
TWITTER_ACCESS_TOKEN_SECRET=...
TWITTER_BOT_HANDLE=betbotx
NEAR_BOT_ACCOUNT_ID=<YOUR_BOT>.testnet
NEAR_BOT_PRIVATE_KEY="ed25519:..."
CONTRACT_ID=<YOUR_CONTRACT>.testnet
EOF

# Run locally
python twitter_bot.py
```

### 3. Off‑Chain Oracle Service

```bash
cd ../oracle-service

# Python deps
pip install -r requirements.txt

# .env
cat > .env <<EOF
CONTRACT_ID=<YOUR_CONTRACT>.testnet
ORACLE_ACCOUNT_ID=<ORACLE_ACCOUNT>.testnet
ODDS_API_KEY=your_odds_api_key
EOF

# Run locally
python oracle_service.py
```

### 4. Web Dashboard

```bash
cd ../web-dashboard

# Install & run
npm install
npm run dev
```

Configure environment in `next.config.js` or host on Vercel/Netlify with:

```
NEAR_ENV=testnet
NEXT_PUBLIC_CONTRACT_ID=<YOUR_CONTRACT>.testnet
```

---

## Running Locally

1. **Deploy** contract to NEAR testnet.  
2. **Start** Twitter bot: `python twitter_bot.py`.  
3. **Start** Oracle: `python oracle_service.py`.  
4. **Launch** Web: `npm run dev` in `web-dashboard`.  
5. **Test** commands from another Twitter account and watch results update on-chain and in the dashboard.

---

## Deployment Guide

- **Smart Contract:** NEAR CLI → testnet/mainnet  
- **Twitter Bot:** Docker → Google Cloud Run / Heroku (with Scheduler for polling)  
- **Oracle Service:** Docker → Cloud Run (HTTP‑triggered or continuous)  
- **Web App:** Vercel / Netlify  

---

## Troubleshooting

- **“Contract not found”** → Verify `CONTRACT_ID` and NEAR CLI credentials.  
- **Twitter rate limits** → Poll mentions every 15 min; batch replies.  
- **Oracle errors** → Check your `ODDS_API_KEY` and network connectivity.  
- **Wallet not connecting** → Ensure correct NEAR environment config in web app.

---

## Contributing

1. Fork the repo  
2. Create a branch (`git checkout -b feat/xyz`)  
3. Commit your changes (`git commit -m "feat: add xyz"`)  
4. Push (`git push origin feat/xyz`) & open a Pull Request  

---

## License

This project is licensed under the MIT License.  
```
