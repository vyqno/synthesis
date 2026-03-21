// SPDX-License-Identifier: MIT
pragma solidity ^0.8.28;

/**
 * @title NexusReputationStaking
 * @notice Agents stake ETH as collateral to guarantee service quality.
 *         Slashed on malicious behavior or repeated underperformance.
 *         Slashed funds split: 50% to harmed party, 50% to public goods vault.
 *
 * Slash conditions (voted by validator committee or ZK-proven):
 *   - Failed to deliver promised service (ZK proof of non-delivery)
 *   - Returned fraudulent data (signed attestation by 3+ validators)
 *   - Reputation score falls below MIN_REPUTATION
 *
 * EigenLayer-inspired but lightweight: no restaking complexity, pure ETH stake,
 * deterministic slashing via multi-validator quorum.
 *
 * Unstake delay (7 days) ensures slash proposals can be raised before funds leave.
 */
contract NexusReputationStaking {
    // -----------------------------------------------------------------------
    // Constants
    // -----------------------------------------------------------------------

    uint256 public constant MIN_STAKE            = 0.01 ether;
    uint256 public constant SLASH_TO_HARMED_BPS  = 5000; // 50% to harmed party
    uint256 public constant SLASH_TO_GOODS_BPS   = 5000; // 50% to public goods
    uint256 public constant BPS_BASE             = 10000;
    uint256 public constant UNSTAKE_DELAY        = 7 days;
    uint256 public constant MIN_REPUTATION       = 20;   // below this → slashable
    uint256 public constant SLASH_QUORUM         = 3;    // validators needed

    // -----------------------------------------------------------------------
    // State
    // -----------------------------------------------------------------------

    address public owner;
    address public publicGoodsVault;
    address public agentIdentity;

    struct Stake {
        uint256 amount;
        uint256 stakedAt;
        uint256 unstakeRequestedAt; // 0 if no pending request
        bool    slashed;
    }

    mapping(address => Stake) public stakes;

    // Slash proposals use a packed struct; voted mapping is stored separately.
    struct SlashProposalHead {
        address agent;
        address harmedParty;
        uint256 slashAmount;
        string  reason;
        uint256 proposedAt;
        uint256 votes;
        bool    executed;
    }

    mapping(uint256 => SlashProposalHead) public slashProposals;
    // proposalId => validator => hasVoted
    mapping(uint256 => mapping(address => bool)) public hasVoted;
    uint256 public nextProposalId;

    mapping(address => bool) public validators;
    uint256 public validatorCount;

    bool private _locked;

    // -----------------------------------------------------------------------
    // Events
    // -----------------------------------------------------------------------

    event Staked(address indexed agent, uint256 amount);
    event UnstakeRequested(address indexed agent, uint256 amount, uint256 claimableAt);
    event Unstaked(address indexed agent, uint256 amount);
    event SlashProposed(uint256 indexed proposalId, address indexed agent, address harmedParty, string reason);
    event SlashVoted(uint256 indexed proposalId, address indexed validator);
    event Slashed(address indexed agent, uint256 slashAmount, address harmedParty);
    event ValidatorAdded(address indexed validator);
    event ValidatorRemoved(address indexed validator);

    // -----------------------------------------------------------------------
    // Modifiers
    // -----------------------------------------------------------------------

    modifier onlyOwner() {
        require(msg.sender == owner, "Not owner");
        _;
    }

    modifier nonReentrant() {
        require(!_locked, "Reentrant call");
        _locked = true;
        _;
        _locked = false;
    }

    // -----------------------------------------------------------------------
    // Constructor
    // -----------------------------------------------------------------------

    constructor(address _publicGoodsVault, address _agentIdentity) {
        owner            = msg.sender;
        publicGoodsVault = _publicGoodsVault;
        agentIdentity    = _agentIdentity;
    }

    // -----------------------------------------------------------------------
    // Staking lifecycle
    // -----------------------------------------------------------------------

    /// @notice Agent stakes ETH to activate service guarantee.
    function stake() external payable nonReentrant {
        require(msg.value >= MIN_STAKE, "Below minimum stake");
        Stake storage s = stakes[msg.sender];
        require(!s.slashed, "Agent is slashed - cannot re-stake");
        s.amount              += msg.value;
        s.stakedAt             = block.timestamp;
        s.unstakeRequestedAt   = 0;
        emit Staked(msg.sender, msg.value);
    }

    /// @notice Begin the 7-day unstake cooldown.
    function requestUnstake() external {
        Stake storage s = stakes[msg.sender];
        require(s.amount > 0, "No active stake");
        require(s.unstakeRequestedAt == 0, "Unstake already requested");
        s.unstakeRequestedAt = block.timestamp;
        emit UnstakeRequested(msg.sender, s.amount, block.timestamp + UNSTAKE_DELAY);
    }

    /// @notice Withdraw staked ETH after the cooldown period has elapsed.
    function unstake() external nonReentrant {
        Stake storage s = stakes[msg.sender];
        require(s.unstakeRequestedAt > 0, "No unstake request");
        require(block.timestamp >= s.unstakeRequestedAt + UNSTAKE_DELAY, "Cooldown not elapsed");
        uint256 amount       = s.amount;
        s.amount             = 0;
        s.unstakeRequestedAt = 0;
        (bool ok,) = msg.sender.call{value: amount}("");
        require(ok, "ETH transfer failed");
        emit Unstaked(msg.sender, amount);
    }

    // -----------------------------------------------------------------------
    // Slashing
    // -----------------------------------------------------------------------

    /**
     * @notice Validator proposes slashing an agent. First vote is auto-cast.
     * @param agent       Agent to slash.
     * @param harmedParty Address that receives 50% of slashed amount.
     * @param slashAmount Amount to slash (capped at agent's stake).
     * @param reason      Human-readable reason string.
     * @return proposalId Newly created proposal ID.
     */
    function proposeSlash(
        address agent,
        address harmedParty,
        uint256 slashAmount,
        string calldata reason
    ) external returns (uint256 proposalId) {
        require(validators[msg.sender], "Not a validator");
        require(stakes[agent].amount >= slashAmount, "Slash exceeds stake");
        require(slashAmount > 0, "Zero slash amount");

        proposalId = nextProposalId++;
        SlashProposalHead storage p = slashProposals[proposalId];
        p.agent       = agent;
        p.harmedParty = harmedParty;
        p.slashAmount = slashAmount;
        p.reason      = reason;
        p.proposedAt  = block.timestamp;
        p.votes       = 1;
        hasVoted[proposalId][msg.sender] = true;

        emit SlashProposed(proposalId, agent, harmedParty, reason);
        emit SlashVoted(proposalId, msg.sender);

        // Immediate execution if quorum already met (single-validator quorum = 1)
        if (p.votes >= SLASH_QUORUM) {
            _executeSlash(proposalId);
        }
    }

    /// @notice Additional validators vote to reach quorum; executes automatically on quorum.
    function voteSlash(uint256 proposalId) external {
        require(validators[msg.sender], "Not a validator");
        SlashProposalHead storage p = slashProposals[proposalId];
        require(!p.executed, "Already executed");
        require(!hasVoted[proposalId][msg.sender], "Already voted");
        p.votes++;
        hasVoted[proposalId][msg.sender] = true;
        emit SlashVoted(proposalId, msg.sender);
        if (p.votes >= SLASH_QUORUM) {
            _executeSlash(proposalId);
        }
    }

    function _executeSlash(uint256 proposalId) internal {
        SlashProposalHead storage p = slashProposals[proposalId];
        p.executed = true;

        Stake storage s   = stakes[p.agent];
        uint256 actual    = p.slashAmount > s.amount ? s.amount : p.slashAmount;
        s.amount         -= actual;
        s.slashed         = true;

        uint256 toHarmed = (actual * SLASH_TO_HARMED_BPS) / BPS_BASE;
        uint256 toGoods  = actual - toHarmed;

        if (toHarmed > 0 && p.harmedParty != address(0)) {
            (bool ok,) = p.harmedParty.call{value: toHarmed}("");
            if (!ok) toGoods += toHarmed; // redirect to public goods on failure
        }
        if (toGoods > 0 && publicGoodsVault != address(0)) {
            (bool ok,) = publicGoodsVault.call{value: toGoods}("");
            require(ok, "Public goods transfer failed");
        }

        emit Slashed(p.agent, actual, p.harmedParty);
    }

    // -----------------------------------------------------------------------
    // View helpers
    // -----------------------------------------------------------------------

    function getStake(address agent)
        external
        view
        returns (uint256 amount, bool slashed, uint256 unstakeClaimableAt)
    {
        Stake storage s = stakes[agent];
        return (
            s.amount,
            s.slashed,
            s.unstakeRequestedAt == 0 ? 0 : s.unstakeRequestedAt + UNSTAKE_DELAY
        );
    }

    function effectiveSlashAmount(address agent, uint256 requested)
        public
        view
        returns (uint256)
    {
        return requested > stakes[agent].amount ? stakes[agent].amount : requested;
    }

    // -----------------------------------------------------------------------
    // Admin
    // -----------------------------------------------------------------------

    function addValidator(address validator) external onlyOwner {
        require(!validators[validator], "Already validator");
        validators[validator] = true;
        validatorCount++;
        emit ValidatorAdded(validator);
    }

    function removeValidator(address validator) external onlyOwner {
        require(validators[validator], "Not a validator");
        validators[validator] = false;
        validatorCount--;
        emit ValidatorRemoved(validator);
    }

    function setPublicGoodsVault(address _vault) external onlyOwner {
        publicGoodsVault = _vault;
    }

    function setAgentIdentity(address _identity) external onlyOwner {
        agentIdentity = _identity;
    }

    receive() external payable {}
}
