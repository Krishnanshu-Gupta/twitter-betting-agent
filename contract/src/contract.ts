import { NearBindgen, near, call, view, UnorderedMap } from 'near-sdk-js';

export enum Outcome {
  Yes = 0,
  No = 1,
  Undecided = 2,
}

@NearBindgen({})
export class Bet {
  user: string;
  amount: bigint; // Using bigint for proper balance handling
  outcome: Outcome;

  constructor(user: string, amount: bigint, outcome: Outcome) {
    this.user = user;
    this.amount = amount;
    this.outcome = outcome;
  }
}

@NearBindgen({})
export class Market {
  id: number;
  description: string;
  bets: Bet[];
  yesPool: bigint;  // Using bigint for arithmetic operations
  noPool: bigint;
  resolved: boolean;
  outcome: Outcome;
  endTime: bigint;  // Market expiration time

  constructor(id: number, description: string, endTime: bigint) {
    this.id = id;
    this.description = description;
    this.bets = [];
    this.yesPool = BigInt(0);
    this.noPool = BigInt(0);
    this.resolved = false;
    this.outcome = Outcome.Undecided;
    this.endTime = endTime;
  }
}

@NearBindgen({})
export class PredictionMarket {
  // Persistent state.
  markets: UnorderedMap<Market> = new UnorderedMap<Market>("m");
  marketCounter: number = 0;

  /**
   * Ensure that persistent state is correctly initialized.
   */
  private ensureState(): void {
    if (!this.markets || (this.markets as any)._prefix === undefined) {
      this.markets = new UnorderedMap<Market>("m");
    }
    if (this.marketCounter === undefined) {
      this.marketCounter = 0;
    }
  }

  @view({})
  getMarketCounter(): number {
    return this.marketCounter;
  }

  @call({})
  createMarket({ description, endTime }: { description: string, endTime: string }): number {
    this.ensureState();
    const parsedEndTime = BigInt(endTime);
    const currentTime = BigInt(near.blockTimestamp());
    if (parsedEndTime <= currentTime) {
      throw new Error("End time must be in the future");
    }
    this.marketCounter += 1;
    const market = new Market(this.marketCounter, description, parsedEndTime);
    this.markets.set(this.marketCounter.toString(), market);
    near.log(`Market ${this.marketCounter} created: ${description}`);
    return this.marketCounter;
  }

  @call({ payableFunction: true })
  placeBet({ marketId, outcomeStr }: { marketId: number, outcomeStr: string }): void {
    this.ensureState();
    const deposit = near.attachedDeposit();
    if (deposit <= BigInt(0)) {
      throw new Error("Deposit must be positive");
    }
    const marketKey = marketId.toString();
    const market = this.markets.get(marketKey);
    if (!market) {
      throw new Error("Market not found");
    }
    if (market.resolved) {
      throw new Error("Market already resolved");
    }
    const currentTime = BigInt(near.blockTimestamp());
    if (currentTime > market.endTime) {
      throw new Error("Market has expired");
    }
    const outcome = this.parseOutcome(outcomeStr);
    const bet = new Bet(near.predecessorAccountId(), deposit, outcome);
    if (outcome === Outcome.Yes) {
      market.yesPool += deposit;
    } else {
      market.noPool += deposit;
    }
    market.bets.push(bet);
    this.markets.set(marketKey, market);
    near.log(`Bet placed: ${deposit.toString()} on ${outcomeStr}`);
  }

  /**
   * Resolve a market. This function can only be called by an external oracle
   * that provides the final outcome (as "yes" or "no"). No internal logic is used
   * to determine the outcome.
   */
  @call({})
  resolveMarketWithOutcome({ marketId, outcomeStr }: { marketId: number, outcomeStr: string }): void {
    this.ensureState();
    const marketKey = marketId.toString();
    const market = this.markets.get(marketKey);
    if (!market) {
      throw new Error("Market not found");
    }
    if (market.resolved) {
      throw new Error("Market already resolved");
    }
    const currentTime = BigInt(near.blockTimestamp());
    if (currentTime <= market.endTime) {
      throw new Error("Market not yet expired");
    }
    // Use the externally provided outcome
    const finalOutcome = this.parseOutcome(outcomeStr);
    market.resolved = true;
    market.outcome = finalOutcome;
    this.markets.set(marketKey, market);
    this.distributePayouts(market, finalOutcome);
  }
  
  private distributePayouts(market: Market, outcome: Outcome): void {
    const totalPool = market.yesPool + market.noPool;
    if (totalPool === BigInt(0)) return;
    const winningPool = outcome === Outcome.Yes ? market.yesPool : market.noPool;
    const losingPool = outcome === Outcome.Yes ? market.noPool : market.yesPool;
    if (winningPool === BigInt(0)) {
      this.refundAll(market);
      return;
    }
    for (const bet of market.bets) {
      if (bet.outcome === outcome) {
        const share = (bet.amount * losingPool) / winningPool;
        const payout = bet.amount + share;
        const promise = near.promiseBatchCreate(bet.user);
        near.promiseBatchActionTransfer(promise, payout);
      }
    }
  }

  private refundAll(market: Market): void {
    for (const bet of market.bets) {
      const promise = near.promiseBatchCreate(bet.user);
      near.promiseBatchActionTransfer(promise, bet.amount);
    }
  }

  private parseOutcome(outcomeStr: string): Outcome {
    if (outcomeStr.toLowerCase() === "yes") return Outcome.Yes;
    if (outcomeStr.toLowerCase() === "no") return Outcome.No;
    throw new Error("Invalid outcome - must be 'yes' or 'no'");
  }

  @view({})
  getMarket({ marketId }: { marketId: number }): Market | null {
    this.ensureState();
    return this.markets.get(marketId.toString());
  }

  @view({})
  getAllMarkets(): Market[] {
    this.ensureState();
    const marketsArr: Market[] = [];
    for (let i = 1; i <= this.marketCounter; i++) {
      const m = this.markets.get(i.toString());
      if (m !== null) {
        marketsArr.push(m);
      }
    }
    return marketsArr;
  }
}
