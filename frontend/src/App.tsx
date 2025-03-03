// src/App.tsx
import "./App.css";
import { BrowserRouter, useLocation, Routes, Route } from "react-router-dom";
import { useEffect, useState, useCallback } from "react";
import { BeatLoader } from "react-spinners";
import { setupModal } from "@near-wallet-selector/modal-ui";
import { WalletSelector } from "@near-wallet-selector/core";
import { providers, utils } from "near-api-js";
import "@near-wallet-selector/modal-ui/styles.css";

const CONTRACT_ID = "5cd89bbc17a044dbdc3fb6a8ce24445e3831d4e32af2884e37308e47d4ab1beb";
const BOATLOAD_OF_GAS = utils.format.parseNearAmount("0.00000000003")!;

interface AppProps {
  selector: WalletSelector;
  currentUser?: string;
}

function App({ selector, currentUser }: AppProps): JSX.Element {
  const [user, setUser] = useState<string | null>(currentUser || null);
  const [result, setResult] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [activeMarkets, setActiveMarkets] = useState<any[]>([]);
  const [myBets, setMyBets] = useState<any[]>([]);
  const [marketInfo, setMarketInfo] = useState<any | null>(null);
  const [marketDescription, setMarketDescription] = useState<string>("");
  const [pendingBet, setPendingBet] = useState<{ marketId: number; outcome: string; deposit: string } | null>(null);
  const [pendingMarket, setPendingMarket] = useState<{ description: string; endTime: string } | null>(null);
  const location = window.location;


  useEffect(() => {
    const subscription = selector.store.observable.subscribe((state) => {
      const accounts = state.accounts;
      setUser(accounts.length > 0 ? accounts[0].accountId : null);
    });

    return () => subscription.unsubscribe();
  }, [selector]);

  useEffect(() => {
    const pathParts = decodeURIComponent(location.pathname).split("/");
    if (pathParts.length > 0) {
      const action = pathParts[0].toLowerCase();
      if (action === "bet" && pathParts.length === 4) {
        // URL structure: /bet/{marketId}/{outcome}/{deposit}
        const [_, marketId, outcomeStr, deposit] = pathParts;
        setPendingBet({ marketId: Number(marketId), outcome: outcomeStr, deposit: deposit });
      } else if (action === "create" && pathParts.length == 3) {
        // URL structure: /create/{description...}/{endTime}
        const [_, description, endTime] = pathParts;
        const descr = decodeURIComponent(description).replace(/_/g, " ");
        setPendingMarket({ description: descr, endTime });
      }
    }
  }, [location]);


  const handleSignInOut = async () => {
    if (!user) {
      const modal = setupModal(selector, { contractId: CONTRACT_ID });
      modal.show();
    } else {
      const wallet = await selector.wallet();
      await wallet.signOut();
      setUser(null);
    }
  };

  const getAllActiveMarkets = async () => {
    try {
      const wallet = await selector.wallet();
      const result = await wallet.signAndSendTransaction({
        signerId: user!,
        receiverId: CONTRACT_ID,
        actions: [
          {
            type: "FunctionCall",
            params: {
              methodName: "getAllMarkets",
              args: {},
              gas: BOATLOAD_OF_GAS,
              deposit: "0"
            }
          }
        ]
      });
      const successValue = (result as any).status?.SuccessValue;
      if (!successValue) {
        console.error("No success value returned from getActiveMarkets.");
        alert("No active markets returned.");
        return;
      }

      const resultString = Buffer.from(successValue, "base64").toString();
      const parsedMarkets = JSON.parse(resultString);
      const activeMarketsOnly = parsedMarkets.filter((m: any) => m.resolved === false);
      setActiveMarkets(activeMarketsOnly);
      setMyBets([]);
      setMarketInfo(null);
    } catch (error) {
      console.error("Error fetching markets:", error);
      alert("Error fetching active markets");
    }
  };

  const getMyCurrentBets = async () => {
    try {
      const wallet = await selector.wallet();
      const result = await wallet.signAndSendTransaction({
        signerId: user!,
        receiverId: CONTRACT_ID,
        actions: [
          {
            type: "FunctionCall",
            params: {
              methodName: "getAllMarkets",
              args: {},
              gas: BOATLOAD_OF_GAS,
              deposit: "0"
            }
          }
        ]
      });
      const successValue = (result as any).status?.SuccessValue;
      if (!successValue) {
        console.error("No success value returned from getActiveMarkets.");
        alert("No active markets returned.");
        return;
      }
      const resultString = Buffer.from(successValue, "base64").toString();
      const parsedMarkets = JSON.parse(resultString);
      const activeMarketsOnly = parsedMarkets.filter((m: any) => m.resolved === false);

      // Assume parsedMarkets is the array you obtained after decoding and parsing the SuccessValue.
      const activeUserBets = activeMarketsOnly.reduce((acc: any[], market: any) => {
        // Only consider active markets (where resolved is false) and where bets exist.
        if (!market.resolved && Array.isArray(market.bets) && market.bets.length > 0) {
          // Filter the bets in this market for the given user.
          const userBets = market.bets.filter((bet: any) => bet.user === user);
          console.log(userBets)
          if (userBets.length > 0) {
            acc.push({
              marketId: market.id,
              description: market.description,
              bets: userBets,
            });
          }
        }
        return acc;
      }, []);

      setMyBets(activeUserBets);
      setActiveMarkets([]);
      setMarketInfo(null);
    } catch (error) {
      console.error("Error fetching markets:", error);
      alert("Error fetching active markets");
    }
  };

  const getMarketInfo = async () => {
    try {
      const wallet = await selector.wallet();
      const result = await wallet.signAndSendTransaction({
        signerId: user!,
        receiverId: CONTRACT_ID,
        actions: [
          {
            type: "FunctionCall",
            params: {
              methodName: "getAllMarkets",
              args: {},
              gas: BOATLOAD_OF_GAS,
              deposit: "0",
            },
          },
        ],
      });
      const successValue = (result as any).status?.SuccessValue;
      if (!successValue) {
        console.error("No success value returned from getAllMarkets.");
        alert("No active markets returned.");
        return;
      }
      const resultString = Buffer.from(successValue, "base64").toString();
      const parsedMarkets = JSON.parse(resultString);
      const activeMarketsOnly = parsedMarkets.filter((m: any) => m.resolved === false);

      // Find the market that matches the provided description (case-insensitive)
      const market = activeMarketsOnly.find(
        (m: any) =>
          m.description.toLowerCase() === marketDescription.trim().toLowerCase()
      );
      if (!market) {
        alert("Market not found");
        setMarketInfo(null);
      } else {
        setMarketInfo(market);
        console.log(market)
      }
      // Optionally clear other states
      setActiveMarkets([]);
      setMyBets([]);
    } catch (error) {
      console.error("Error fetching market info:", error);
      alert("Error fetching market information");
    }
  };


  const createMarket = async () => {
    setLoading(true);
    if (!pendingMarket) {
      alert("No pending market to create. @BetBotX on X to create a market.");
      setLoading(false);
      return
    }
    try {
      console.log(pendingMarket)

      alert("Market created.");
      window.history.pushState({}, "", "/");
      setPendingMarket(null);
    } catch (error) {
      console.error("Error creating market:", error);
      alert("Error creating market");
    } finally {
      setLoading(false);
    }
  };

  const placeBet = async () => {
    setLoading(true);
    if (!pendingBet) {
      alert("No pending bet to place. @BetBotX on X to place a bet.");
      setLoading(false);
      return
    }
    try {
      const wallet = await selector.wallet();
      const result = await wallet.signAndSendTransaction({
        signerId: user!,
        receiverId: CONTRACT_ID,
        actions: [
          {
            type: "FunctionCall",
            params: {
              methodName: "placeBet",
              args: { marketId: Number(pendingBet.marketId), outcomeStr: pendingBet.outcome },
              gas: BOATLOAD_OF_GAS,
              deposit: utils.format.parseNearAmount(pendingBet.deposit)!
            }
          }
        ]
      });
      alert("Bet placed successfully");
      window.history.pushState({}, "", "/");
      setPendingBet(null);
    } catch (error) {
      console.error("Error placing bet:", error);
      alert("Error placing bet");
    } finally {
      setLoading(false);
    }
  };

  const getOutcomeText = (outcome: any): string => {
    // Assuming outcome === 0 means "Yes" and outcome !== 0 means "No"
    return outcome === 0 ? "Yes" : "No";
  };

  return (
    <BrowserRouter>
      <div className="navbar-container">
        <div className="nav-links">
          <h2>Bet Bot X</h2>
        </div>
        <div className="profile-section">
          {user && <h3>{user}</h3>}
          <button className="user-button" onClick={handleSignInOut}>
            {user ? "Sign Out" : "Login"}
          </button>
        </div>
      </div>
      {user && (
        <div className="container">
          <div className="action-buttons">
            <button onClick={createMarket} disabled={loading}>
              {loading ? <BeatLoader size={8} color="#fff" /> : "Create Market"}
            </button>
            <button onClick={placeBet} disabled={loading}>
              {loading ? <BeatLoader size={8} color="#fff" /> : "Place Bet"}
            </button>
            <button onClick={getAllActiveMarkets} disabled={loading}>
              {loading ? <BeatLoader size={8} color="#fff" /> : "Get Active Markets"}
            </button>
            <button onClick={getMyCurrentBets} disabled={loading}>
              {loading ? <BeatLoader size={8} color="#fff" /> : "Get My Bets"}
            </button>
            <button onClick={getMarketInfo} disabled={loading}>
              {loading ? <BeatLoader size={8} color="#fff" /> : "Get Specific Market Info"}
            </button>
            <input
              type="text"
              value={marketDescription}
              onChange={(e) => setMarketDescription(e.target.value)}
              placeholder="Enter Name for market info"
            />

            {/* Display results */}
            {activeMarkets.length > 0 && (
              <div className="result-container">
                <h3>Active Markets</h3>
                <div className="market-list">
                  {activeMarkets.map((market) => (
                    <div key={market.id} className="market-item">
                      <p>ID: {market.id}</p>
                      <p>Name: {market.description}</p>
                      <p>Ends: {new Date(market.endTime / 1000000).toLocaleString()}</p>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {myBets.length > 0 && (
              <div className="result-container">
                <h3>Your Bets</h3>
                <div className="bet-list">
                  {myBets.map((marketBet) => (
                    <div key={marketBet.marketId} className="market-bet">
                      <h4>
                        Market {marketBet.marketId}: {marketBet.description}
                      </h4>
                      {marketBet.bets.map((bet: any, index: number) => (
                        <div key={index} className="bet-item">
                          <p>Outcome: {getOutcomeText(bet.outcome)}</p>
                          <p>
                            Amount: {utils.format.formatNearAmount(bet.amount)} Ⓝ
                          </p>
                        </div>
                      ))}
                    </div>
                  ))}
                </div>
              </div>
            )}

            {marketInfo && (
              <div className="result-container">
                <h3>Market Information</h3>
                <div className="market-info">
                  <p>ID: {marketInfo.id}</p>
                  <p>Name: {marketInfo.description}</p>
                  <p>Total Yes: {utils.format.formatNearAmount(marketInfo.yesPool)} Ⓝ</p>
                  <p>Total No: {utils.format.formatNearAmount(marketInfo.noPool)} Ⓝ</p>
                  <p>Status: {marketInfo.isResolved ? "Resolved" : "Active"}</p>
                </div>
              </div>
            )}
          </div>
        </div>
      )}
    </BrowserRouter>
  );
}

export default App;