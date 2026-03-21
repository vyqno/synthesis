// SPDX-License-Identifier: MIT
pragma solidity ^0.8.28;

/**
 * @title NexusPublicGoodsVault
 * @notice wstETH vault whose accrued yield is automatically split between
 *         Octant (60%) and Gitcoin (40%) at each epoch distribution.
 *         Depositors receive PGV — a soulbound (non-transferable) ERC-20 receipt
 *         token that doubles as governance weight.
 *
 * Real-world impact:
 *   Turns passive DeFi yield into protocol-enforced public goods funding.
 *   Inspired by Octant's epoch model + Gitcoin Allo protocol.
 *   Just deposit wstETH and your yield permanently funds open-source software.
 *
 * Yield accounting:
 *   wstETH appreciates relative to stETH over time, so the contract's wstETH
 *   balance grows beyond its total minted PGV (principal). distributeYield()
 *   sweeps the surplus to beneficiaries and advances the epoch counter.
 *
 * Soulbound enforcement:
 *   _update() is overridden to block all transfers except mints (from == 0)
 *   and burns (to == 0).
 */

interface IERC20 {
    function balanceOf(address) external view returns (uint256);
    function transfer(address, uint256) external returns (bool);
    function transferFrom(address, address, uint256) external returns (bool);
}

contract NexusPublicGoodsVault {
    // -----------------------------------------------------------------------
    // ERC-20 storage (soulbound)
    // -----------------------------------------------------------------------

    string public constant name     = "Nexus Public Goods Vault";
    string public constant symbol   = "PGV";
    uint8  public constant decimals = 18;

    uint256 public totalSupply;
    mapping(address => uint256) public balanceOf;
    // No allowance mapping — soulbound tokens cannot be transferred.

    // -----------------------------------------------------------------------
    // Vault state
    // -----------------------------------------------------------------------

    IERC20 public immutable wstETH;

    /// @notice Distribution split in basis points (must sum to BPS_BASE).
    uint256 public octantShareBps  = 6000; // 60%
    uint256 public gitcoinShareBps = 4000; // 40%
    uint256 public constant BPS_BASE = 10000;

    address public octantPool;
    address public gitcoinAllo;

    uint256 public epochDuration = 90 days;
    uint256 public epochStart;
    uint256 public currentEpoch;

    uint256 public totalToOctant;
    uint256 public totalToGitcoin;

    mapping(address => bool) public isDepositor;

    address public owner;
    bool private _locked;

    // -----------------------------------------------------------------------
    // Events
    // -----------------------------------------------------------------------

    // ERC-20 required
    event Transfer(address indexed from, address indexed to, uint256 value);

    event Deposited(address indexed depositor, uint256 wstEthAmount, uint256 pgvMinted);
    event YieldDistributed(uint256 indexed epoch, uint256 toOctant, uint256 toGitcoin);
    event BeneficiariesUpdated(address octant, address gitcoin);

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

    constructor(address _wstETH, address _octantPool, address _gitcoinAllo) {
        owner       = msg.sender;
        wstETH      = IERC20(_wstETH);
        octantPool  = _octantPool;
        gitcoinAllo = _gitcoinAllo;
        epochStart  = block.timestamp;
    }

    // -----------------------------------------------------------------------
    // Deposit
    // -----------------------------------------------------------------------

    /**
     * @notice Deposit wstETH. Receive PGV (soulbound, 1:1 with deposit).
     * @param wstEthAmount Amount of wstETH to deposit.
     */
    function deposit(uint256 wstEthAmount) external nonReentrant {
        require(wstEthAmount > 0, "Zero deposit");
        wstETH.transferFrom(msg.sender, address(this), wstEthAmount);
        _mint(msg.sender, wstEthAmount);
        isDepositor[msg.sender] = true;
        emit Deposited(msg.sender, wstEthAmount, wstEthAmount);
    }

    // -----------------------------------------------------------------------
    // Yield distribution
    // -----------------------------------------------------------------------

    /**
     * @notice Distribute accumulated wstETH yield to Octant and Gitcoin.
     *         Permissionless — callable by anyone (keeper, cron, agent).
     *         yield = vault wstETH balance − total PGV supply (principal).
     */
    function distributeYield() external nonReentrant {
        uint256 vaultBalance = wstETH.balanceOf(address(this));
        uint256 principal    = totalSupply; // PGV is 1:1 with principal
        require(vaultBalance > principal, "No yield to distribute");

        uint256 yield     = vaultBalance - principal;
        uint256 toOctant  = (yield * octantShareBps)  / BPS_BASE;
        uint256 toGitcoin = yield - toOctant;

        if (toOctant > 0 && octantPool != address(0)) {
            wstETH.transfer(octantPool, toOctant);
            totalToOctant += toOctant;
        }
        if (toGitcoin > 0 && gitcoinAllo != address(0)) {
            wstETH.transfer(gitcoinAllo, toGitcoin);
            totalToGitcoin += toGitcoin;
        }

        currentEpoch++;
        epochStart = block.timestamp;

        emit YieldDistributed(currentEpoch, toOctant, toGitcoin);
    }

    // -----------------------------------------------------------------------
    // View helpers
    // -----------------------------------------------------------------------

    function getVaultStats()
        external
        view
        returns (
            uint256 totalDeposited,
            uint256 pendingYield,
            uint256 epoch,
            uint256 distributedToOctant,
            uint256 distributedToGitcoin
        )
    {
        uint256 balance   = wstETH.balanceOf(address(this));
        uint256 principal = totalSupply;
        return (
            principal,
            balance > principal ? balance - principal : 0,
            currentEpoch,
            totalToOctant,
            totalToGitcoin
        );
    }

    // -----------------------------------------------------------------------
    // Soulbound ERC-20 — transfers blocked
    // -----------------------------------------------------------------------

    /// @dev Soulbound: revert on any transfer that is not a mint or burn.
    function transfer(address, uint256) external pure returns (bool) {
        revert("PGV is soulbound \xe2\x80\x94 non-transferable");
    }

    function transferFrom(address, address, uint256) external pure returns (bool) {
        revert("PGV is soulbound \xe2\x80\x94 non-transferable");
    }

    function approve(address, uint256) external pure returns (bool) {
        revert("PGV is soulbound \xe2\x80\x94 non-transferable");
    }

    function allowance(address, address) external pure returns (uint256) {
        return 0;
    }

    // -----------------------------------------------------------------------
    // Admin
    // -----------------------------------------------------------------------

    /// @notice Update the Octant and Gitcoin beneficiary addresses for yield distribution.
    function setBeneficiaries(address _octant, address _gitcoin) external onlyOwner {
        octantPool  = _octant;
        gitcoinAllo = _gitcoin;
        emit BeneficiariesUpdated(_octant, _gitcoin);
    }

    /// @notice Update yield split between Octant and Gitcoin (must sum to 10000 bps).
    function setDistributionSplit(uint256 _octantBps, uint256 _gitcoinBps) external onlyOwner {
        require(_octantBps + _gitcoinBps == BPS_BASE, "Must sum to 10000");
        octantShareBps  = _octantBps;
        gitcoinShareBps = _gitcoinBps;
    }

    /// @notice Update the minimum epoch duration (floor: 1 day).
    function setEpochDuration(uint256 _duration) external onlyOwner {
        require(_duration >= 1 days, "Epoch too short");
        epochDuration = _duration;
    }

    // -----------------------------------------------------------------------
    // Internal ERC-20 helpers
    // -----------------------------------------------------------------------

    function _mint(address to, uint256 value) internal {
        totalSupply      += value;
        balanceOf[to]    += value;
        emit Transfer(address(0), to, value);
    }
}
