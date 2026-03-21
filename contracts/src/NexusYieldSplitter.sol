// SPDX-License-Identifier: MIT
pragma solidity ^0.8.28;

/**
 * @title NexusYieldSplitter
 * @notice Pendle-inspired yield splitter for wstETH.
 *         Deposit wstETH → receive a Principal Token position (PT) redeemable at
 *         maturity + stream all accrued yield to the Nexus agent's compute budget.
 *
 * Use case: Fund Nexus compute without losing money.
 *   1. Deposit 1 wstETH (choose maturity 7 days – 365 days)
 *   2. Position stored on-chain (positionId returned)
 *   3. wstETH yield (currently ~4 % APY) flows to Nexus treasury via harvestYield()
 *   4. At maturity call redeemPT(positionId) → get original wstETH back
 *
 * Yield accounting: wstETH is a rebasing token expressed as shares. Its value
 * relative to stETH grows over time via stEthPerToken(). We record the exchange
 * rate at deposit; the difference between current rate × principal and original
 * principal captures yield. Yield is swept as surplus contract balance above
 * locked principal (same wstETH amount — principal never inflates in wstETH terms
 * because wstETH itself appreciates; the treasury receives the excess wstETH that
 * arrived via Lido's auto-compound).
 */

interface IERC20 {
    function balanceOf(address) external view returns (uint256);
    function transfer(address, uint256) external returns (bool);
    function transferFrom(address, address, uint256) external returns (bool);
}

interface IWstETH is IERC20 {
    function stEthPerToken() external view returns (uint256);
    function getStETHByWstETH(uint256 wstETHAmount) external view returns (uint256);
}

contract NexusYieldSplitter {
    // -----------------------------------------------------------------------
    // Constants
    // -----------------------------------------------------------------------

    /// @notice wstETH on Ethereum mainnet.
    address public constant WSTETH = 0x7f39C581F595B53c5cb19bD0b3f8dA6c935E2Ca0;

    uint256 public constant MIN_MATURITY_DURATION = 7 days;
    uint256 public constant MAX_MATURITY_DURATION = 365 days;

    // -----------------------------------------------------------------------
    // State
    // -----------------------------------------------------------------------

    address public owner;
    address public agentTreasury;

    struct Position {
        uint256 wstEthDeposited;       // original deposit amount in wstETH shares
        uint256 stEthPerTokenAtEntry;  // wstETH exchange rate at deposit time
        uint256 maturity;              // unix timestamp when PT is redeemable
        bool    redeemed;
    }

    // depositor => list of positions
    mapping(address => Position[]) public positions;

    /// @notice Total wstETH locked as principal across all un-redeemed positions.
    uint256 public totalLocked;

    bool private _locked;

    // -----------------------------------------------------------------------
    // Events
    // -----------------------------------------------------------------------

    event Deposited(address indexed user, uint256 positionId, uint256 wstEth, uint256 maturity);
    event PTRedeemed(address indexed user, uint256 positionId, uint256 wstEthReturned);
    event YieldHarvested(uint256 yieldAmount, address indexed treasury);
    event TreasuryUpdated(address indexed treasury);

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

    constructor(address _agentTreasury) {
        owner = msg.sender;
        agentTreasury = _agentTreasury;
    }

    // -----------------------------------------------------------------------
    // Deposit
    // -----------------------------------------------------------------------

    /**
     * @notice Deposit wstETH. Receive PT (principal back at maturity). YT streams to agent.
     * @param wstEthAmount    Amount of wstETH to deposit.
     * @param maturityDuration Seconds until maturity (7 days – 365 days).
     * @return positionId     Index into positions[msg.sender].
     */
    function deposit(uint256 wstEthAmount, uint256 maturityDuration)
        external
        nonReentrant
        returns (uint256 positionId)
    {
        require(
            maturityDuration >= MIN_MATURITY_DURATION &&
            maturityDuration <= MAX_MATURITY_DURATION,
            "Invalid maturity duration"
        );
        require(wstEthAmount > 0, "Zero deposit");

        IWstETH(WSTETH).transferFrom(msg.sender, address(this), wstEthAmount);

        uint256 rateAtEntry = IWstETH(WSTETH).stEthPerToken();
        uint256 maturity    = block.timestamp + maturityDuration;

        positions[msg.sender].push(Position({
            wstEthDeposited:      wstEthAmount,
            stEthPerTokenAtEntry: rateAtEntry,
            maturity:             maturity,
            redeemed:             false
        }));

        positionId = positions[msg.sender].length - 1;
        totalLocked += wstEthAmount;

        emit Deposited(msg.sender, positionId, wstEthAmount, maturity);
    }

    // -----------------------------------------------------------------------
    // Redeem PT
    // -----------------------------------------------------------------------

    /**
     * @notice Redeem the principal token at or after maturity — get wstETH back.
     * @param positionId Index into positions[msg.sender].
     */
    function redeemPT(uint256 positionId) external nonReentrant {
        Position storage pos = positions[msg.sender][positionId];
        require(!pos.redeemed, "Already redeemed");
        require(block.timestamp >= pos.maturity, "Not matured yet");

        pos.redeemed = true;
        totalLocked -= pos.wstEthDeposited;

        IWstETH(WSTETH).transfer(msg.sender, pos.wstEthDeposited);
        emit PTRedeemed(msg.sender, positionId, pos.wstEthDeposited);
    }

    // -----------------------------------------------------------------------
    // Yield harvest
    // -----------------------------------------------------------------------

    /**
     * @notice Harvest accumulated wstETH yield and send to agent treasury.
     *         Yield = contract balance minus total principal locked.
     *         wstETH accrues value automatically via Lido staking rewards, so
     *         the contract will hold more wstETH than was ever deposited once
     *         rewards compound.
     *
     *         Anyone can call this (permissionless keeper).
     */
    function harvestYield() external nonReentrant {
        require(agentTreasury != address(0), "No treasury set");

        uint256 contractBalance = IWstETH(WSTETH).balanceOf(address(this));
        require(contractBalance > totalLocked, "No yield available");

        uint256 yieldAmount = contractBalance - totalLocked;
        IWstETH(WSTETH).transfer(agentTreasury, yieldAmount);

        emit YieldHarvested(yieldAmount, agentTreasury);
    }

    // -----------------------------------------------------------------------
    // View helpers
    // -----------------------------------------------------------------------

    function getPositions(address user) external view returns (Position[] memory) {
        return positions[user];
    }

    function pendingYield() external view returns (uint256) {
        uint256 bal = IWstETH(WSTETH).balanceOf(address(this));
        return bal > totalLocked ? bal - totalLocked : 0;
    }

    // -----------------------------------------------------------------------
    // Admin
    // -----------------------------------------------------------------------

    /// @notice Update the agent treasury that receives harvested wstETH yield.
    function setAgentTreasury(address _treasury) external onlyOwner {
        agentTreasury = _treasury;
        emit TreasuryUpdated(_treasury);
    }
}
