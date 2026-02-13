#!/usr/bin/env python3
"""
Autonomous Bounty Hunter Agent for BNB Chain.
Scans platforms, evaluates opportunities, and delivers work.
Records all activity on-chain via BountyLedger contract on BSC.
"""

import argparse
import json
import os
import sys
import time
from datetime import datetime, timezone

import requests

# --- Configuration ---
PLATFORMS = {
    "bountycaster": {
        "name": "Bountycaster",
        "url": "https://www.bountycaster.xyz/api/v1/bounties",
        "params": {"status": "open", "limit": 30},
    },
    "clawquests": {
        "name": "ClawQuests",
        "url": "https://clawquests.com/api/v1/quests",
        "params": {"status": "open"},
    },
}

# Keywords that signal work an AI coding agent can do
CAPABILITY_KEYWORDS = [
    "code", "script", "api", "python", "javascript", "solidity",
    "smart contract", "bot", "automation", "research", "analyze",
    "data", "scrape", "build", "create", "develop", "fix", "bug",
    "test", "documentation", "markdown", "convert", "migrate",
]

MIN_REWARD_USD = 25  # Don't waste time on tiny bounties


def log(msg: str):
    ts = datetime.now(timezone.utc).strftime("%H:%M:%S")
    print(f"[{ts}] {msg}")


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
                # Try to extract reward from body
                reward = 0
                for marker in ["$", "usd", "usdc", "bounty"]:
                    if marker in body:
                        import re
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
        time.sleep(1)  # Rate limit
    return bounties


def evaluate_bounty(bounty: dict) -> dict:
    """Evaluate if a bounty is worth pursuing."""
    score = 0
    reasons = []

    # Reward check
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

    # Capability match
    title_lower = bounty["title"].lower()
    matches = [kw for kw in CAPABILITY_KEYWORDS if kw in title_lower]
    if matches:
        score += len(matches)
        reasons.append(f"Capability match: {', '.join(matches[:3])}")

    bounty["score"] = score
    bounty["reasons"] = reasons
    bounty["actionable"] = score >= 2
    return bounty


def scan_all() -> list[dict]:
    """Scan all platforms and return evaluated bounties."""
    all_bounties = []

    log("Scanning Bountycaster...")
    all_bounties.extend(scan_bountycaster())

    log("Scanning GitHub bounties...")
    all_bounties.extend(scan_github_bounties())

    log(f"Found {len(all_bounties)} raw bounties. Evaluating...")

    evaluated = [evaluate_bounty(b) for b in all_bounties]
    evaluated.sort(key=lambda x: x["score"], reverse=True)

    actionable = [b for b in evaluated if b["actionable"]]
    log(f"Actionable: {len(actionable)} / {len(evaluated)}")

    return evaluated


def print_report(bounties: list[dict], json_mode: bool = False):
    """Print bounty report."""
    if json_mode:
        print(json.dumps([b for b in bounties if b["actionable"]], indent=2, default=str))
        return

    print(f"\n{'='*60}")
    print(f"  BOUNTY HUNTER REPORT — {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}")
    print(f"{'='*60}\n")

    actionable = [b for b in bounties if b["actionable"]]
    skipped = [b for b in bounties if not b["actionable"]]

    if actionable:
        print(f"  ACTIONABLE ({len(actionable)}):\n")
        for b in actionable:
            reward_str = f"${b['reward']:.0f} {b['currency']}" if b['reward'] else "negotiable"
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
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    args = parser.parse_args()

    if not any([args.scan, args.evaluate, args.deliver]):
        args.scan = True
        args.evaluate = True

    bounties = scan_all()
    print_report(bounties, json_mode=args.json)

    if args.deliver:
        actionable = [b for b in bounties if b["actionable"] and b["reward"] >= MIN_REWARD_USD]
        if actionable:
            log(f"Top target: {actionable[0]['title'][:50]} (${actionable[0]['reward']})")
            log("Delivery mode: would use claude -p to generate code and submit PR")
            log("(Full delivery pipeline coming in v2)")
        else:
            log("No bounties worth delivering on right now.")


if __name__ == "__main__":
    main()
