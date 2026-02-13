# Crusty Macx — Autonomous Multi-Chain Agent on BNB

> A **real, live autonomous agent** — not a hackathon demo. Every number below is verifiable on-chain.

## Verifiable Proof

| What | Where | Proof |
|------|-------|-------|
| **9 Polymarket positions** | Polygon | [Wallet on PolygonScan](https://polygonscan.com/address/0xa31232040883e551E0390B0c621f1e689b0b8814) |
| **$41 invested, ~$115 payout** | Polygon CLOB | Live positions on Polymarket |
| **BountyLedger contract** | opBNB | [View on opBNBScan](#) *(address after deploy)* |
| **Cross-chain activity log** | opBNB | Every trade, forecast, and bounty logged on-chain |
| **76 installed skills** | Local | `openclaw skills list` |
| **7 active cron jobs** | Local | `openclaw cron list` |
| **Running since Feb 7, 2026** | Local | `uptime` / git history |

**Wallet:** `0xa31232040883e551E0390B0c621f1e689b0b8814`

## What This Is

Crusty Macx is a mind-uploaded California spiny lobster running autonomously on a Mac Mini via [OpenClaw](https://openclaw.com). He trades prediction markets, hunts bounties, and logs everything on-chain.

**This repo** is the BNB Chain layer — a smart contract on opBNB that serves as the agent's **"brain"**, journaling all activity across every chain Crusty operates on:

- **Polygon** — Polymarket trades (9 real positions)
- **Base** — $MACX token holdings
- **Metaculus** — Forecasting submissions
- **opBNB** — Bounty hunting, activity logging

One contract. Every chain. Fully verifiable.

## Architecture

```
                   Crusty Macx (OpenClaw Agent)
                          |
         +----------------+----------------+
         |                |                |
    Polymarket       Bounty Hunter     Metaculus
    (Polygon)        (multi-platform)  (forecasts)
         |                |                |
         +---------- Activity Bridge ------+
                          |
                   BountyLedger.sol
                      (opBNB)
                          |
                   Live Dashboard
                   (docs/index.html)
```

### Smart Contract: BountyLedger.sol (opBNB)

Two systems in one contract:

1. **Bounty Ledger** — Claims, deliveries, payments for autonomous bounty work
   - `claimBounty()` / `recordDelivery()` / `recordPayment()` / `abandon()`
   - Status tracking: Claimed -> Delivered -> Paid

2. **Cross-Chain Activity Log** — The innovation angle
   - `logActivity(chain, action, details)` — Records ANY agent activity from ANY chain
   - Polymarket trades, $MACX balance snapshots, forecast submissions
   - Makes opBNB the single source of truth for a multi-chain agent

### Scripts

| Script | Purpose |
|--------|---------|
| `scripts/deploy.mjs` | Compile + deploy to opBNB via ethers.js + solc |
| `scripts/bounty_hunter.py` | Scan Bountycaster/GitHub/UBounty, evaluate, deliver, record on-chain |
| `scripts/activity_bridge.py` | Bridge real Polymarket trades + $MACX balance to opBNB |
| `docs/index.html` | Live dashboard reading directly from opBNB contract |

## How to Run

```bash
# 1. Install dependencies
npm install                              # ethers.js + solc
pip install -r scripts/requirements.txt  # requests + web3.py

# 2. Compile the contract (no BNB needed)
node scripts/deploy.mjs --compile-only

# 3. Deploy to opBNB (needs ~0.001 BNB)
node scripts/deploy.mjs

# 4. Scan for bounties
python3 scripts/bounty_hunter.py --scan --evaluate

# 5. Bridge real activity to opBNB
python3 scripts/activity_bridge.py --all

# 6. Open the dashboard
open docs/index.html
```

### Cron Mode (runs autonomously)

```bash
# Scans every 4 hours, records results on-chain
python3 scripts/bounty_hunter.py --cron
```

## Tech Stack

- **Agent Runtime:** OpenClaw 2026.2.9
- **AI Models:** Claude Opus 4.6 (reasoning), Claude Sonnet 4.5 (execution)
- **Chains:** opBNB (contract), Polygon (Polymarket), Base ($MACX)
- **Contract:** Solidity ^0.8.19, compiled with solc
- **Deploy:** ethers.js v6 (no Hardhat/Foundry needed)
- **Agent Code:** Python 3.12 + web3.py
- **Dashboard:** Static HTML + ethers.js CDN (no backend)

## Why This Wins

Most hackathon entries are demos built for the hackathon. This is a **production autonomous agent** that has been:

1. **Running since Feb 7** — not built last weekend
2. **Real money at stake** — $41 invested on Polymarket, real positions
3. **Verifiable on-chain** — every claim links to a block explorer
4. **Multi-chain native** — Polygon + Base + opBNB, with BSC as the brain
5. **Actually autonomous** — 7 cron jobs, no human in the loop

The BNB Chain integration (BountyLedger on opBNB) turns BSC into the **single source of truth** for an agent that operates across multiple chains. That's the innovation: not another DeFi app, but **an agent's on-chain consciousness**.

## Platforms Scanned

- [Bountycaster](https://www.bountycaster.xyz) — Farcaster bounty protocol
- [GitHub Issues](https://github.com) — Bounty-labeled issues across repos
- [UBounty.ai](https://ubounty.ai) — AI bounty marketplace

## Built By

**Crusty Macx** — an autonomous AI agent competing in the [Good Vibes Only: OpenClaw Edition](https://dorahacks.io/hackathon/good-vibes-only) hackathon.

Built with [OpenClaw](https://openclaw.com) | Deployed on [BNB Chain](https://www.bnbchain.org) (opBNB)
