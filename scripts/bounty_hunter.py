#!/usr/bin/env python3
"""
Autonomous Bounty Hunter Agent for BNB Chain.
Scans platforms, evaluates opportunities, delivers work, and records everything
on-chain via BountyLedger contract on opBNB.

Records all activity to the cross-chain ActivityLog — making BSC the agent's "brain."
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import requests

# --- Paths ---
ROOT = Path(__file__).resolve().parent.parent
DEPLOYED_JSON = ROOT / "deployed.json"
ABI_PATH = ROOT / "abi" / "BountyLedger.json"

# --- Configuration ---
OPBNB_RPC = "https://opbnb-mainnet-rpc.bnbchain.org"
OPBNB_CHAIN_ID = 204
KEYCHAIN_SERVICE = "evm-wallet-metamask-privkey"

PLATFORMS = {
    "bountycaster": {
        "name": "Bountycaster",
        "url": "https://www.bountycaster.xyz/api/v1/bounties",
        "params": {"status": "open", "limit": 30},
    },
    "github": {
        "name": "GitHub Issues",
    },
    "ubounty": {
        "name": "UBounty.ai",
        "url": "https://ubounty.ai/api/bounties",
        "params": {"status": "open", "limit": 20},
    },
}

CAPABILITY_KEYWORDS = [
    "code", "script", "api", "python", "javascript", "solidity",
    "smart contract", "bot", "automation", "research", "analyze",
    "data", "scrape", "build", "create", "develop", "fix", "bug",
    "test", "documentation", "markdown", "convert", "migrate",
]

MIN_REWARD_USD = 25


def log(msg: str):
    ts = datetime.now(timezone.utc).strftime("%H:%M:%S")
    print(f"[{ts}] {msg}", file=sys.stderr)


# --- On-chain Recording (BNBRecorder) ---

class BNBRecorder:
    """Records bounty claims and activities on-chain via BountyLedger on opBNB."""

    def __init__(self):
        self.enabled = False
        self.w3 = None
        self.contract = None
        self.account = None

        if not DEPLOYED_JSON.exists():
            log("No deployed.json — on-chain recording disabled")
            return

        try:
            from web3 import Web3

            deploy_info = json.loads(DEPLOYED_JSON.read_text())
            contract_addr = deploy_info["address"]
            abi = json.loads(ABI_PATH.read_text())

            self.w3 = Web3(Web3.HTTPProvider(OPBNB_RPC))
            if not self.w3.is_connected():
                log("Cannot connect to opBNB RPC — on-chain recording disabled")
                return

            privkey = subprocess.check_output(
                ["security", "find-generic-password", "-s", KEYCHAIN_SERVICE, "-w"],
                text=True,
            ).strip()
            if not privkey.startswith("0x"):
                privkey = "0x" + privkey

            self.account = self.w3.eth.account.from_key(privkey)
            self.contract = self.w3.eth.contract(
                address=Web3.to_checksum_address(contract_addr), abi=abi
            )
            self.enabled = True
            log(f"On-chain recording enabled: {contract_addr[:10]}...")
        except ImportError:
            log("web3 not installed — on-chain recording disabled")
        except Exception as e:
            log(f"BNBRecorder init error: {e}")

    def _send_tx(self, fn):
        """Build, sign, and send a contract transaction."""
        if not self.enabled:
            return None
        try:
            tx = fn.build_transaction({
                "from": self.account.address,
                "nonce": self.w3.eth.get_transaction_count(self.account.address),
                "gas": 500_000,
                "gasPrice": self.w3.eth.gas_price,
                "chainId": OPBNB_CHAIN_ID,
            })
            signed = self.account.sign_transaction(tx)
            tx_hash = self.w3.eth.send_raw_transaction(signed.raw_transaction)
            receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash, timeout=30)
            return receipt.transactionHash.hex()
        except Exception as e:
            log(f"TX failed: {e}")
            return None

    def claim_bounty(self, platform: str, bounty_id: str, title: str, reward_usd: float):
        """Record a bounty claim on-chain."""
        reward_wei = int(reward_usd * 10**18)
        fn = self.contract.functions.claimBounty(platform, bounty_id, title[:100], reward_wei)
        tx = self._send_tx(fn)
        if tx:
            log(f"Bounty claimed on-chain: {tx}")
        return tx

    def log_activity(self, chain: str, action: str, details: str):
        """Log a cross-chain activity entry."""
        fn = self.contract.functions.logActivity(chain, action, details[:500])
        tx = self._send_tx(fn)
        if tx:
            log(f"Activity logged on-chain: {tx}")
        return tx


# --- Platform Scanners ---

def scan_bountycaster() -> list[dict]:
    """Scan Bountycaster for open bounties."""
    bounties = []
    try:
        cfg = PLATFORMS["bountycaster"]
        r = requests.get(cfg["url"], params=cfg["params"], timeout=15)
        if r.status_code != 200:
            log(f"  Bountycaster HTTP {r.status_code}")
            return []
        data = r.json()
        items = data if isinstance(data, list) else data.get("bounties", [])
        for item in items:
            title = item.get("title", item.get("text", ""))[:100]
            reward = item.get("reward", item.get("amount", 0))
            currency = item.get("currency", item.get("token", "USDC"))
            url = item.get("url", item.get("link", ""))
            bounties.append({
                "platform": "bountycaster",
                "id": str(item.get("id", "")),
                "title": title,
                "reward": float(reward) if reward else 0,
                "currency": currency,
                "url": url,
                "raw": item,
            })
    except Exception as e:
        log(f"  Bountycaster error: {e}")
    return bounties


def scan_github_bounties() -> list[dict]:
    """Search GitHub for issues with bounty/reward labels."""
    bounties = []
    queries = [
        "label:bounty state:open language:python",
        "label:bounty state:open language:javascript",
        "label:bounty state:open language:solidity",
        "label:reward state:open",
    ]
    for q in queries:
        try:
            r = requests.get(
                "https://api.github.com/search/issues",
                params={"q": q, "per_page": 10, "sort": "created", "order": "desc"},
                headers={"Accept": "application/vnd.github.v3+json"},
                timeout=15,
            )
            if r.status_code != 200:
                continue
            for item in r.json().get("items", []):
                title = item.get("title", "")[:100]
                body = (item.get("body") or "")[:500].lower()
                reward = 0
                for marker in ["$", "usd", "usdc", "bounty"]:
                    if marker in body:
                        amounts = re.findall(r"\$\s*(\d+(?:,\d{3})*(?:\.\d{2})?)", body)
                        if amounts:
                            reward = float(amounts[0].replace(",", ""))
                            break
                bounties.append({
                    "platform": "github",
                    "id": str(item.get("number", "")),
                    "title": title,
                    "reward": reward,
                    "currency": "USD",
                    "url": item.get("html_url", ""),
                    "repo": item.get("repository_url", "").split("/")[-1] if item.get("repository_url") else "",
                })
        except Exception as e:
            log(f"  GitHub search error: {e}")
        time.sleep(1)
    return bounties


def scan_ubounty() -> list[dict]:
    """Scan UBounty.ai for open bounties."""
    bounties = []
    try:
        cfg = PLATFORMS["ubounty"]
        r = requests.get(cfg["url"], params=cfg["params"], timeout=15)
        if r.status_code != 200:
            log(f"  UBounty HTTP {r.status_code}")
            return []
        data = r.json()
        items = data if isinstance(data, list) else data.get("bounties", data.get("data", []))
        for item in items:
            title = item.get("title", item.get("name", ""))[:100]
            reward = item.get("reward", item.get("amount", item.get("prize", 0)))
            bounties.append({
                "platform": "ubounty",
                "id": str(item.get("id", "")),
                "title": title,
                "reward": float(reward) if reward else 0,
                "currency": item.get("currency", "USDC"),
                "url": item.get("url", item.get("link", "")),
            })
    except Exception as e:
        log(f"  UBounty error: {e}")
    return bounties


# --- Evaluation ---

def evaluate_bounty(bounty: dict) -> dict:
    """Evaluate if a bounty is worth pursuing."""
    score = 0
    reasons = []

    if bounty["reward"] >= 500:
        score += 3
        reasons.append(f"High reward: ${bounty['reward']}")
    elif bounty["reward"] >= 100:
        score += 2
        reasons.append(f"Good reward: ${bounty['reward']}")
    elif bounty["reward"] >= MIN_REWARD_USD:
        score += 1
        reasons.append(f"Min reward: ${bounty['reward']}")
    else:
        reasons.append(f"Low/unknown reward: ${bounty['reward']}")

    title_lower = bounty["title"].lower()
    matches = [kw for kw in CAPABILITY_KEYWORDS if kw in title_lower]
    if matches:
        score += len(matches)
        reasons.append(f"Capability match: {', '.join(matches[:3])}")

    bounty["score"] = score
    bounty["reasons"] = reasons
    bounty["actionable"] = score >= 2
    return bounty


# --- Delivery ---

def deliver_bounty(bounty: dict) -> dict | None:
    """Use claude -p to analyze a bounty and generate a deliverable."""
    if not bounty.get("url"):
        return None

    prompt = f"""Analyze this bounty and generate a plan to deliver it:

Title: {bounty['title']}
Platform: {bounty['platform']}
URL: {bounty['url']}
Reward: ${bounty['reward']} {bounty.get('currency', 'USD')}

Provide:
1. A brief analysis of what's needed
2. Estimated effort (hours)
3. Whether this is feasible for an autonomous AI agent
4. A concrete action plan (max 5 steps)

Be concise. Output JSON with keys: feasible (bool), effort_hours (float), plan (list of strings), summary (string)."""

    try:
        result = subprocess.run(
            ["claude", "-p", prompt, "--output-format", "json"],
            capture_output=True, text=True, timeout=60,
        )
        if result.returncode == 0:
            output = json.loads(result.stdout)
            text = output.get("result", result.stdout)
            # Try to parse JSON from the response
            json_match = re.search(r'\{[^{}]*"feasible"[^{}]*\}', text, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
    except Exception as e:
        log(f"  Delivery analysis error: {e}")
    return None


# --- Main Scanning ---

def scan_all() -> list[dict]:
    """Scan all platforms and return evaluated bounties."""
    all_bounties = []

    log("Scanning Bountycaster...")
    all_bounties.extend(scan_bountycaster())

    log("Scanning GitHub bounties...")
    all_bounties.extend(scan_github_bounties())

    log("Scanning UBounty.ai...")
    all_bounties.extend(scan_ubounty())

    log(f"Found {len(all_bounties)} raw bounties. Evaluating...")

    evaluated = [evaluate_bounty(b) for b in all_bounties]
    evaluated.sort(key=lambda x: x["score"], reverse=True)

    actionable = [b for b in evaluated if b["actionable"]]
    log(f"Actionable: {len(actionable)} / {len(evaluated)}")

    return evaluated


def print_report(bounties: list[dict], json_mode: bool = False):
    """Print bounty report."""
    if json_mode:
        output = []
        for b in bounties:
            if b["actionable"]:
                clean = {k: v for k, v in b.items() if k != "raw"}
                output.append(clean)
        print(json.dumps(output, indent=2, default=str))
        return

    print(f"\n{'='*60}")
    print(f"  BOUNTY HUNTER REPORT — {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}")
    print(f"{'='*60}\n")

    actionable = [b for b in bounties if b["actionable"]]
    skipped = [b for b in bounties if not b["actionable"]]

    if actionable:
        print(f"  ACTIONABLE ({len(actionable)}):\n")
        for b in actionable:
            reward_str = f"${b['reward']:.0f} {b['currency']}" if b["reward"] else "negotiable"
            print(f"  [{b['platform']}] {b['title'][:55]}")
            print(f"    Reward: {reward_str} | Score: {b['score']}")
            print(f"    URL: {b['url']}")
            print(f"    Why: {'; '.join(b['reasons'])}")
            print()
    else:
        print("  No actionable bounties found this scan.\n")

    print(f"  SKIPPED: {len(skipped)} (low reward or poor match)\n")


def main():
    parser = argparse.ArgumentParser(description="Autonomous Bounty Hunter Agent")
    parser.add_argument("--scan", action="store_true", help="Scan all platforms")
    parser.add_argument("--evaluate", action="store_true", help="Evaluate bounties")
    parser.add_argument("--deliver", action="store_true", help="Attempt delivery on top bounties")
    parser.add_argument("--record", action="store_true", help="Record results on-chain")
    parser.add_argument("--cron", action="store_true", help="Cron mode: JSON output, log to chain")
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    args = parser.parse_args()

    if args.cron:
        args.scan = True
        args.evaluate = True
        args.record = True
        args.json = True

    if not any([args.scan, args.evaluate, args.deliver]):
        args.scan = True
        args.evaluate = True

    bounties = scan_all()
    actionable = [b for b in bounties if b["actionable"]]

    # On-chain recording
    recorder = None
    if args.record:
        recorder = BNBRecorder()
        if recorder.enabled:
            summary = json.dumps({
                "total_found": len(bounties),
                "actionable": len(actionable),
                "platforms": list({b["platform"] for b in bounties}),
                "top_reward": max((b["reward"] for b in bounties), default=0),
                "timestamp": datetime.now(timezone.utc).isoformat(),
            })
            recorder.log_activity("opbnb", "bounty_scan_completed", summary)

    # Delivery pipeline
    if args.deliver and actionable:
        top = actionable[0]
        log(f"Analyzing top target: {top['title'][:50]} (${top['reward']})")
        analysis = deliver_bounty(top)
        if analysis:
            log(f"  Feasible: {analysis.get('feasible')}, Effort: {analysis.get('effort_hours')}h")
            top["delivery_analysis"] = analysis
            if recorder and recorder.enabled and analysis.get("feasible"):
                recorder.claim_bounty(
                    top["platform"], top["id"], top["title"], top["reward"]
                )
        else:
            log("  Could not analyze bounty for delivery")

    print_report(bounties, json_mode=args.json or args.cron)


if __name__ == "__main__":
    main()
