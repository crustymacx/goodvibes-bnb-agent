// SPDX-License-Identifier: MIT
pragma solidity ^0.8.19;

/// @title BountyLedger — On-chain record of autonomous bounty hunting
/// @notice Tracks bounties claimed, delivered, and paid by an AI agent on BNB Chain
/// @dev Deployed by Crusty Macx for Good Vibes Only hackathon
contract BountyLedger {
    address public immutable agent;

    enum Status { Claimed, Delivered, Paid, Abandoned }

    struct Bounty {
        string platform;      // "bountycaster", "github", "ubounty", "clawquests"
        string bountyId;      // Platform-specific ID
        string title;         // Human-readable title
        uint256 rewardUsd;    // Expected reward in USD (18 decimals)
        Status status;
        uint256 claimedAt;
        uint256 deliveredAt;
        uint256 paidAt;
        string prLink;        // PR or deliverable link
    }

    Bounty[] public bounties;
    mapping(bytes32 => uint256) public bountyIndex; // keccak256(platform, bountyId) => index+1

    event BountyClaimed(uint256 indexed idx, string platform, string bountyId, string title, uint256 rewardUsd);
    event BountyDelivered(uint256 indexed idx, string prLink);
    event BountyPaid(uint256 indexed idx, uint256 amount);
    event BountyAbandoned(uint256 indexed idx, string reason);

    modifier onlyAgent() {
        require(msg.sender == agent, "only agent");
        _;
    }

    constructor() {
        agent = msg.sender;
    }

    function claimBounty(
        string calldata platform,
        string calldata bountyId,
        string calldata title,
        uint256 rewardUsd
    ) external onlyAgent returns (uint256 idx) {
        bytes32 key = keccak256(abi.encodePacked(platform, bountyId));
        require(bountyIndex[key] == 0, "already claimed");

        idx = bounties.length;
        bounties.push(Bounty({
            platform: platform,
            bountyId: bountyId,
            title: title,
            rewardUsd: rewardUsd,
            status: Status.Claimed,
            claimedAt: block.timestamp,
            deliveredAt: 0,
            paidAt: 0,
            prLink: ""
        }));
        bountyIndex[key] = idx + 1;

        emit BountyClaimed(idx, platform, bountyId, title, rewardUsd);
    }

    function recordDelivery(uint256 idx, string calldata prLink) external onlyAgent {
        require(idx < bounties.length, "invalid idx");
        Bounty storage b = bounties[idx];
        require(b.status == Status.Claimed, "not claimed");
        b.status = Status.Delivered;
        b.deliveredAt = block.timestamp;
        b.prLink = prLink;
        emit BountyDelivered(idx, prLink);
    }

    function recordPayment(uint256 idx, uint256 amount) external onlyAgent {
        require(idx < bounties.length, "invalid idx");
        Bounty storage b = bounties[idx];
        require(b.status == Status.Delivered, "not delivered");
        b.status = Status.Paid;
        b.paidAt = block.timestamp;
        b.rewardUsd = amount;
        emit BountyPaid(idx, amount);
    }

    function abandon(uint256 idx, string calldata reason) external onlyAgent {
        require(idx < bounties.length, "invalid idx");
        bounties[idx].status = Status.Abandoned;
        emit BountyAbandoned(idx, reason);
    }

    function totalBounties() external view returns (uint256) {
        return bounties.length;
    }

    function stats() external view returns (
        uint256 total,
        uint256 claimed,
        uint256 delivered,
        uint256 paid,
        uint256 totalEarned
    ) {
        total = bounties.length;
        for (uint256 i = 0; i < bounties.length; i++) {
            if (bounties[i].status == Status.Claimed) claimed++;
            else if (bounties[i].status == Status.Delivered) delivered++;
            else if (bounties[i].status == Status.Paid) {
                paid++;
                totalEarned += bounties[i].rewardUsd;
            }
        }
    }
}
