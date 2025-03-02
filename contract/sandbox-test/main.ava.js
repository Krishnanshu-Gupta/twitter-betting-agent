import anyTest from 'ava';
import { Worker } from 'near-workspaces';
import { setDefaultResultOrder } from 'dns';
setDefaultResultOrder('ipv4first');

/**
 * @typedef {import('near-workspaces').Account} Account
 * @typedef {import('ava').TestFn<{worker: Worker, accounts: Record<string, Account>}>} TestContext
 */
const test = anyTest;

test.beforeEach(async t => {
  // Initialize sandboxed NEAR environment.
  const worker = t.context.worker = await Worker.init();

  // Create a contract subaccount and deploy the WASM file.
  const root = worker.rootAccount;
  const contract = await root.createSubAccount('contract');
  await contract.deploy(process.argv[2]);

  // Create additional test accounts.
  const alice = await root.createSubAccount('alice');
  const bob = await root.createSubAccount('bob');

  t.context.accounts = { root, contract, alice, bob };
});

test.afterEach.always(async t => {
  await t.context.worker.tearDown().catch(err => console.log('Failed to stop sandbox:', err));
});

test('createMarket creates a new market', async t => {
  const { contract } = t.context.accounts;
  const description = 'Test market';
  // Compute a future endTime: current time (in ns) plus 100 seconds.
  const now = BigInt(Date.now()) * BigInt(1_000_000);
  const futureTime = (now + BigInt(100_000_000_000)).toString();

  const marketId = await contract.call('createMarket', { description, endTime: futureTime });
  t.true(typeof marketId === 'number');

  const market = await contract.view('getMarket', { marketId });
  t.is(market.description, description);
  t.is(market.resolved, false);
  t.is(market.bets.length, 0);
});

test('placeBet adds a bet and updates the pool', async t => {
  const { contract, alice } = t.context.accounts;
  const description = 'Alice market';
  const now = BigInt(Date.now()) * BigInt(1_000_000);
  const futureTime = (now + BigInt(100_000_000_000)).toString();

  const marketId = await contract.call('createMarket', { description, endTime: futureTime });

  // Alice places a bet of 1 NEAR (in yoctoNEAR) on "yes".
  const deposit = '1000000000000000000000000'; // 1 NEAR
  await alice.call(
    contract,
    'placeBet',
    { marketId, outcomeStr: 'yes' },
    { attachedDeposit: deposit }
  );

  const market = await contract.view('getMarket', { marketId });
  t.is(market.bets.length, 1);
  t.is(market.yesPool, deposit);
});

test('resolveMarket distributes payouts correctly', async t => {
  const { contract, alice, bob, } = t.context.accounts;
  const description = 'Resolution test market';
  const now = BigInt(Date.now()) * BigInt(1_000_000);
  // Set market endTime to 100 seconds in the future.
  const futureTime = (now + BigInt(100_000_000_000)).toString();
  const marketId = await contract.call('createMarket', { description, endTime: futureTime });

  // Alice bets 2 NEAR on "yes" and Bob bets 1 NEAR on "no".
  const depositAlice = '2000000000000000000000000'; // 2 NEAR
  const depositBob   = '1000000000000000000000000'; // 1 NEAR
  await alice.call(
    contract,
    'placeBet',
    { marketId, outcomeStr: 'yes' },
    { attachedDeposit: depositAlice }
  );
  await bob.call(
    contract,
    'placeBet',
    { marketId, outcomeStr: 'no' },
    { attachedDeposit: depositBob }
  );

  // Record initial balances.
  const aliceBalanceBefore = BigInt(await alice.balance());
  const bobBalanceBefore = BigInt(await bob.balance());

  // Advance the block timestamp so the market has expired.
  // Convert the futureTime string to a number and add 1.
  const futureTimestamp = Number(BigInt(futureTime)) + 1;
  await t.context.worker.setBlockTimestamp(futureTimestamp);

  // Resolve the market.
  await contract.call('resolveMarket', { marketId });

  // With our placeholder oracle, the final outcome is Outcome.Yes.
  // Expected payout for Alice: 2 NEAR + (2/2)*1 NEAR = 3 NEAR.
  const expectedPayout = BigInt('3000000000000000000000000');
  const aliceBalanceAfter = BigInt(await alice.balance());
  t.true(aliceBalanceAfter - aliceBalanceBefore >= expectedPayout);

  // Bob, who bet on "no", should see a decrease in balance.
  const bobBalanceAfter = BigInt(await bob.balance());
  t.true(bobBalanceAfter < bobBalanceBefore);

  const marketAfter = await contract.view('getMarket', { marketId });
  t.true(marketAfter.resolved);
  t.is(marketAfter.outcome, 0); // Outcome.Yes is represented as 0.
});
