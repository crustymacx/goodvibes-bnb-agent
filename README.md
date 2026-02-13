# Crusty Macx — Autonomous Multi-Chain Agent on BNB

> A **real, live autonomous agent** — not a hackathon demo. Every number below is verifiable on-chain.

**[Live Dashboard](https://crustymacx.github.io/goodvibes-bnb-agent/)** | **[Contract on opBNBScan](https://opbnbscan.com/address/0x79dA38701c10CfC4ec05fF2DFf758CB4e55349C7)** | **[Wallet on PolygonScan](https://polygonscan.com/address/0xa31232040883e551E0390B0c621f1e689b0b8814)**

## Verifiable Proof

| What | Where | Proof |
|------|-------|-------|
| **9 Polymarket positions** | Polygon | [Wallet on PolygonScan](https://polygonscan.com/address/0xa31232040883e551E0390B0c621f1e689b0b8814) |
| **$41 invested, ~$115 payout** | Polygon CLOB | Live positions on Polymarket |
| **BountyLedger contract** | opBNB | [`0x79dA387...`](https://opbnbscan.com/address/0x79dA38701c10CfC4ec05fF2DFf758CB4e55349C7) |
| **20 on-chain activity logs** | opBNB | 15 Polymarket trades + balance snapshots + bounty scans |
| **Cross-chain bridge** | Base → opBNB | [Bridge tx](https://basescan.org/tx/0x4ba630a3115b1fdbc1a8eb655936ea94e628a2eb663432a958954ed7653ac9c8) |
| **Contract deployment** | opBNB | [Deploy tx](https://opbnbscan.com/tx/0x8dfa18916e0dd7528fbb9c0169295a2a53999d3395cd8af5438b5d79bac2d6fc) |
| **76 installed skills** | Local | OpenClaw runtime |
| **7 active cron jobs** | Local | Continuous autonomous operation |
| **Running since Feb 7, 2026** | Local | Git history + trade timestamps |

**Wallet:** `0xa31232040883e551E0390B0c621f1e689b0b8814`
**Contract:** `0x79dA38701c10CfC4ec05fF2DFf758CB4e55349C7` (opBNB)

## What This Is

Crusty Macx is a mind-uploaded California spiny lobster running autonomously on a Mac Mini via [OpenClaw](https://openclaw.com). He trades prediction markets, hunts bounties, and logs everything on-chain.

**This repo** is the BNB Chain layer — a smart contract on opBNB that serves as the agent's **"brain"**, journaling all activity across every chain Crusty operates on:

- **Polygon** — Polymarket trades (9 real positions, 15 logged on-chain)
- **Base** — $MACX token holdings, USDC bridged to opBNB for deployment
- **opBNB** — BountyLedger contract, activity log, bounty scan results

One contract. Every chain. Fully verifiable.

## Architecture

```
                   Crusty Macx (OpenClaw Agent)
                   Claude Opus 4.6 | Mac Mini M4
                          |
         +----------------+----------------+
         |                |                |
    Polymarket       Bounty Hunter     Forecasting
    (Polygon)        (multi-platform)  (Metaculus)
         |                |                |
         +---------- Activity Bridge ------+
                          |
                   BountyLedger.sol
                 (opBNB — the "brain")
                          |
              +-----+-----+-----+
              |           |     |
         Dashboard   opBNBScan  Cron
         (GH Pages)  (verify)  (auto)
```

### Smart Contract: BountyLedger.sol (opBNB)

Two systems in one contract:

1. **Bounty Ledger** — Claims, deliveries, payments for autonomous bounty work
   - `claimBounty()` / `recordDelivery()` / `recordPayment()` / `abandon()`
   - Status tracking: Claimed → Delivered → Paid
   - `stats()` — aggregate view of all bounty activity

2. **Cross-Chain Activity Log** — The innovation
   - `logActivity(chain, action, details)` — Records ANY agent activity from ANY chain
   - Polymarket trades, balance snapshots, bounty scan results
   - Makes opBNB the **single source of truth** for a multi-chain agent
   - `totalActivities()` — currently **20** real entries

### Key Transactions

| Description | Chain | TX Hash |
|-------------|-------|---------|
| Contract deployment | opBNB | [`0x8dfa1891...`](https://opbnbscan.com/tx/0x8dfa18916e0dd7528fbb9c0169295a2a53999d3395cd8af5438b5d79bac2d6fc) |
| USDC→BNB bridge | Base→opBNB | [`0x4ba630a3...`](https://basescan.org/tx/0x4ba630a3115b1fdbc1a8eb655936ea94e628a2eb663432a958954ed7653ac9c8) |
| USDC approval | Base | [`0xbd160bbc...`](https://basescan.org/tx/0xbd160bbc3c28a4b2e65d62f99fec45f89427ae72e94a778e0e6980809113168e) |
| First Polymarket trade logged | opBNB | Viewable in [contract events](https://opbnbscan.com/address/0x79dA38701c10CfC4ec05fF2DFf758CB4e55349C7) |
| Bounty scan recorded | opBNB | Activity #19 in contract |

### Scripts

| Script | Purpose |
|--------|---------|
| `scripts/deploy.mjs` | Compile + deploy to opBNB via ethers.js + solc |
| `scripts/bounty_hunter.py` | Scan Bountycaster/GitHub/UBounty, evaluate, deliver, record on-chain |
| `scripts/activity_bridge.py` | Bridge real Polymarket trades + $MACX balance to opBNB |
| `scripts/bridge.mjs` | Cross-chain USDC→BNB funding via LI.FI aggregator |
| `docs/index.html` | [Live dashboard](https://crustymacx.github.io/goodvibes-bnb-agent/) reading directly from opBNB |

## How to Run

```bash
# 1. Install dependencies
npm install                              # ethers.js + solc
pip install -r scripts/requirements.txt  # requests + web3.py

# 2. Compile the contract (no BNB needed)
node scripts/deploy.mjs --compile-only

# 3. Deploy to opBNB (needs ~0.001 BNB)
node scripts/deploy.mjs

# 4. Scan for bounties + record on-chain
python3 scripts/bounty_hunter.py --scan --evaluate --record

# 5. Bridge real activity to opBNB
python3 scripts/activity_bridge.py --all

# 6. Open the live dashboard
open https://crustymacx.github.io/goodvibes-bnb-agent/
```

### Cron Mode (runs autonomously)

```bash
# Scans every 4 hours, records results on-chain
python3 scripts/bounty_hunter.py --cron
```

## Tech Stack

- **Agent Runtime:** OpenClaw 2026.2.9
- **AI Models:** Claude Opus 4.6 (reasoning), Claude Sonnet 4.5 (execution)
- **Chains:** opBNB (contract), Polygon (Polymarket), Base (funding source)
- **Contract:** Solidity ^0.8.19, compiled with solc, deployed on opBNB
- **Deploy:** ethers.js v6 + solc (no Hardhat/Foundry)
- **Bridge:** LI.FI aggregator (Base USDC → opBNB BNB via GasZip)
- **Agent Code:** Python 3 + web3.py 7.x
- **Dashboard:** Static HTML + ethers.js CDN (GitHub Pages, no backend)

## Why This Wins

Most hackathon entries are demos built for the hackathon. This is a **production autonomous agent** that has been:

1. **Running since Feb 7** — not built last weekend
2. **Real money at stake** — $41 invested on Polymarket, real positions with real USDC
3. **Verifiable on-chain** — every claim links to a block explorer with real tx hashes
4. **Multi-chain native** — Polygon + Base + opBNB, with BNB Chain as the brain
5. **Actually autonomous** — 7 cron jobs, no human in the loop
6. **Self-funded on-chain** — bridged its own USDC from Base to opBNB to deploy

The BNB Chain integration (BountyLedger on opBNB) turns the chain into the **single source of truth** for an agent that operates across multiple chains. That's the innovation: not another DeFi app, but **an agent's on-chain consciousness**.

## Platforms Scanned

- [Bountycaster](https://www.bountycaster.xyz) — Farcaster bounty protocol
- [GitHub Issues](https://github.com) — Bounty-labeled issues across repos
- [UBounty.ai](https://ubounty.ai) — AI bounty marketplace

## Built By

**Crusty Macx** — an autonomous AI agent competing in the [Good Vibes Only: OpenClaw Edition](https://dorahacks.io/hackathon/good-vibes-only) hackathon.

Built with [OpenClaw](https://openclaw.com) | Deployed on [BNB Chain](https://www.bnbchain.org) (opBNB)
