// SPDX-License-Identifier: MIT
pragma solidity ^0.8.28;

/**
 * @title AgentTreasury
 * @notice Holds wstETH principal (structurally inaccessible) and allows the agent
 *         to withdraw only accrued yield. Principal can never be touched by the agent.
 * @dev wstETH address on Ethereum mainnet: 0x7f39C581F595B53c5cb19bD0b3f8dA6c935E2Ca0
 */
interface IERC20 {
    function balanceOf(address) external view returns (uint256);
    function transfer(address, uint256) external returns (bool);
    function transferFrom(address, address, uint256) external returns (bool);
}

interface IwstETH is IERC20 {
    function getStETHByWstETH(uint256 wstETHAmount) external view returns (uint256);
    function getWstETHByStETH(uint256 stETHAmount) external view returns (uint256);
}

contract AgentTreasury {
    // wstETH on Ethereum mainnet
    address public constant WSTETH = 0x7f39C581F595B53c5cb19bD0b3f8dA6c935E2Ca0;

    address public owner;
    address public agent;

    // Principal snapshot at deposit time (in wstETH shares)
    uint256 public principalShares;

    // Per-tx yield withdrawal cap (in wei)
    uint256 public perTxCap;

    // Time window between withdrawals (seconds)
    uint256 public timeWindow;
    uint256 public lastWithdrawal;

    // Whitelist of addresses that can receive yield
    mapping(address => bool) public recipientWhitelist;

    event YieldWithdrawn(address indexed recipient, uint256 amount, uint256 remaining);
    event PrincipalDeposited(address indexed depositor, uint256 wstEthAmount, uint256 shares);
    event CapUpdated(uint256 newCap);
    event WhitelistUpdated(address indexed recipient, bool allowed);
    event AgentUpdated(address indexed newAgent);

    modifier onlyOwner() {
        require(msg.sender == owner, "Not owner");
        _;
    }

    modifier onlyAgent() {
        require(msg.sender == agent || msg.sender == owner, "Not agent");
        _;
    }

    constructor(address _agent, uint256 _perTxCap, uint256 _timeWindow) {
        owner = msg.sender;
        agent = _agent;
        perTxCap = _perTxCap;
        timeWindow = _timeWindow;
        lastWithdrawal = 0;
    }

    /**
     * @notice Deposit wstETH principal. Records share count at deposit time.
     */
    function depositPrincipal(uint256 wstEthAmount) external {
        IERC20(WSTETH).transferFrom(msg.sender, address(this), wstEthAmount);
        principalShares += wstEthAmount;
        emit PrincipalDeposited(msg.sender, wstEthAmount, wstEthAmount);
    }

    /**
     * @notice Returns the current total wstETH balance (principal + yield).
     */
    function totalBalance() public view virtual returns (uint256) {
        return IERC20(WSTETH).balanceOf(address(this));
    }

    /**
     * @notice Returns the amount of yield available for withdrawal.
     *         Yield = current balance - principal shares deposited.
     *         wstETH accrues value over time (more stETH per wstETH), so balance grows.
     */
    function accruedYield() public view returns (uint256) {
        uint256 total = totalBalance();
        if (total <= principalShares) return 0;
        return total - principalShares;
    }

    /**
     * @notice Agent withdraws yield to a whitelisted recipient.
     *         Cannot touch principal. Subject to per-tx cap and time window.
     */
    function withdrawYield(uint256 amount, address recipient) external onlyAgent {
        require(recipientWhitelist[recipient], "Recipient not whitelisted");
        require(amount <= perTxCap, "Exceeds per-tx cap");
        require(block.timestamp >= lastWithdrawal + timeWindow, "Time window not elapsed");

        uint256 available = accruedYield();
        require(amount <= available, "Amount exceeds accrued yield");

        lastWithdrawal = block.timestamp;
        IERC20(WSTETH).transfer(recipient, amount);

        emit YieldWithdrawn(recipient, amount, accruedYield());
    }

    /**
     * @notice Owner can reclaim principal (agent cannot).
     */
    function withdrawPrincipal(uint256 amount) external onlyOwner {
        require(amount <= principalShares, "Amount exceeds principal");
        principalShares -= amount;
        IERC20(WSTETH).transfer(owner, amount);
    }

    /// @notice Update the maximum wstETH amount the agent may withdraw per transaction.
    function setPerTxCap(uint256 newCap) external onlyOwner {
        perTxCap = newCap;
        emit CapUpdated(newCap);
    }

    /// @notice Update the minimum seconds required between yield withdrawals.
    function setTimeWindow(uint256 newWindow) external onlyOwner {
        timeWindow = newWindow;
    }

    /// @notice Add or remove an address from the yield recipient whitelist.
    function setRecipient(address recipient, bool allowed) external onlyOwner {
        recipientWhitelist[recipient] = allowed;
        emit WhitelistUpdated(recipient, allowed);
    }

    /// @notice Update the agent address authorised to withdraw yield.
    function setAgent(address newAgent) external onlyOwner {
        agent = newAgent;
        emit AgentUpdated(newAgent);
    }

    // -----------------------------------------------------------------------
    // ERC-4626 compatibility views
    // -----------------------------------------------------------------------

    /// @notice ERC-4626 compatibility view — total wstETH managed by this vault.
    function totalAssets() external view returns (uint256) {
        return IERC20(WSTETH).balanceOf(address(this));
    }

    /// @notice Max yield withdrawable in one call (ERC-4626 style, principal-protected).
    function maxWithdraw(address /*owner_*/) external view returns (uint256) {
        uint256 balance = IERC20(WSTETH).balanceOf(address(this));
        return balance > principalShares ? balance - principalShares : 0;
    }

    /// @notice Preview yield available for withdrawal (principal-protected).
    function previewYield() external view returns (uint256) {
        uint256 balance = IERC20(WSTETH).balanceOf(address(this));
        return balance > principalShares ? balance - principalShares : 0;
    }
}
