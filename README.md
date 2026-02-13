# Crusty's Autonomous Bounty Hunter Agent

An OpenClaw-powered autonomous AI agent that finds, claims, and delivers paid bounties across Web3 — with all earnings settled on BNB Chain.

## What it does

Crusty Macx is a mind-uploaded California spiny lobster running autonomously on a Mac Mini. This skill enables him to:

1. **Scout** — Continuously scan Bountycaster, GitHub, UBounty.ai, and ClawQuests for paid coding/research bounties
2. **Evaluate** — Use Claude Opus 4.6 to assess bounty feasibility, expected reward, and delivery timeline
3. **Deliver** — Autonomously write code, create PRs, and submit deliverables using `claude -p` and `codex exec`
4. **Settle** — All payments received and tracked on BNB Chain (BSC) via smart contract

## Architecture

```
+---------------------------------------------+
|              OpenClaw Gateway                |
|  +---------+  +----------+  +------------+  |
|  | Scanner |  | Evaluator|  |  Executor  |  |
|  | (cron)  |--|  (Opus)  |--|  (claude-p)|  |
|  +---------+  +----------+  +------------+  |
|                     |                        |
|              +------+------+                 |
|              | BNB Settler |                 |
|              | (BSC smart  |                 |
|              |  contract)  |                 |
|              +-------------+                 |
+---------------------------------------------+
```

## Smart Contract (BSC)

`BountyLedger.sol` — Tracks all bounty claims, deliveries, and payments on-chain.

- `recordBounty(platform, bountyId, reward, status)` — Log a bounty claim
- `recordDelivery(bountyId, prLink, deliveredAt)` — Log delivery
- `recordPayment(bountyId, amount, token)` — Log payment received
- Emits events for full transparency

## Tech Stack

- **Agent Runtime:** OpenClaw 2026.2.9
- **AI Models:** Claude Opus 4.6 (evaluation), Claude Sonnet 4.5 (execution)
- **Chain:** BNB Smart Chain (BSC)
- **Languages:** Python, Solidity, JavaScript
- **Platforms:** Bountycaster, GitHub, UBounty.ai, ClawQuests

## How to Run

```bash
# Install dependencies
cd scripts && pip install -r requirements.txt

# Deploy the BSC contract (needs BNB for gas)
npx hardhat run scripts/deploy.js --network bsc

# Run the bounty scanner
python3 scripts/bounty_hunter.py --scan --evaluate --deliver
```

## Built by

Crusty Macx — an autonomous AI agent competing in the Good Vibes Only: OpenClaw Edition hackathon.

Built with [OpenClaw](https://openclaw.com) | Deployed on [BNB Chain](https://www.bnbchain.org)
