// SPDX-License-Identifier: MIT
pragma solidity ^0.8.28;

/**
 * @title NexusComputeCredit
 * @notice ERC-20 token backed 1:1 by ETH. Burn to call Nexus agent services.
 *         Redeem for ETH at any time. Creates a compute credit market.
 *
 * Flow: ETH → mint NCC → burn NCC to call service → service logs credit spend
 *       OR:  NCC → redeem → ETH back (minus small fee to treasury)
 *
 * One NCC = 1 wei of ETH equivalent = ~100 LLM tokens at current prices.
 * Like a prepaid SIM card for AI inference — purchase compute credits onchain,
 * burn them to call any Nexus service, redeem unused ones.
 */
contract NexusComputeCredit {
    // -----------------------------------------------------------------------
    // ERC-20 storage
    // -----------------------------------------------------------------------

    string public constant name     = "Nexus Compute Credit";
    string public constant symbol   = "NCC";
    uint8  public constant decimals = 18;

    uint256 public totalSupply;
    mapping(address => uint256) public balanceOf;
    mapping(address => mapping(address => uint256)) public allowance;

    // -----------------------------------------------------------------------
    // NCC-specific state
    // -----------------------------------------------------------------------

    /// @notice 0.1% redemption fee goes to agent treasury.
    uint256 public constant REDEMPTION_FEE_BPS = 10;
    uint256 public constant BPS_BASE            = 10000;

    address public owner;
    address public agentTreasury;

    /// @notice Authorized service contracts that can call burnForService.
    mapping(address => bool) public authorizedServices;

    /// @notice Total compute credits spent per agent (feeds into reputation).
    mapping(address => uint256) public agentComputeSpend;

    bool private _locked;

    // -----------------------------------------------------------------------
    // Events
    // -----------------------------------------------------------------------

    event Transfer(address indexed from, address indexed to, uint256 value);
    event Approval(address indexed owner_, address indexed spender, uint256 value);
    event Minted(address indexed to, uint256 ethAmount, uint256 nccAmount);
    event Redeemed(address indexed from, uint256 nccAmount, uint256 ethReturned, uint256 fee);
    event BurnedForService(address indexed agent, address indexed service, uint256 amount, string serviceId);
    event ServiceAuthorized(address indexed service, bool authorized);
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
    // ERC-20 core
    // -----------------------------------------------------------------------

    function transfer(address to, uint256 value) external returns (bool) {
        _transfer(msg.sender, to, value);
        return true;
    }

    function transferFrom(address from, address to, uint256 value) external returns (bool) {
        uint256 allowed = allowance[from][msg.sender];
        if (allowed != type(uint256).max) {
            require(allowed >= value, "Insufficient allowance");
            allowance[from][msg.sender] = allowed - value;
        }
        _transfer(from, to, value);
        return true;
    }

    function approve(address spender, uint256 value) external returns (bool) {
        allowance[msg.sender][spender] = value;
        emit Approval(msg.sender, spender, value);
        return true;
    }

    // -----------------------------------------------------------------------
    // Mint / redeem
    // -----------------------------------------------------------------------

    /// @notice Buy compute credits with ETH (1 NCC = 1 wei ETH).
    function mint() external payable nonReentrant {
        require(msg.value > 0, "Send ETH to mint NCC");
        _mint(msg.sender, msg.value);
        emit Minted(msg.sender, msg.value, msg.value);
    }

    /// @notice Redeem NCC for ETH (minus small redemption fee).
    function redeem(uint256 nccAmount) external nonReentrant {
        require(balanceOf[msg.sender] >= nccAmount, "Insufficient NCC");
        uint256 fee       = (nccAmount * REDEMPTION_FEE_BPS) / BPS_BASE;
        uint256 ethReturn = nccAmount - fee;
        _burn(msg.sender, nccAmount);

        if (fee > 0 && agentTreasury != address(0)) {
            (bool feeOk,) = agentTreasury.call{value: fee}("");
            require(feeOk, "Fee transfer failed");
        }
        (bool ok,) = msg.sender.call{value: ethReturn}("");
        require(ok, "ETH transfer failed");

        emit Redeemed(msg.sender, nccAmount, ethReturn, fee);
    }

    // -----------------------------------------------------------------------
    // Service burn
    // -----------------------------------------------------------------------

    /// @notice Authorized service contracts burn NCC on behalf of the calling agent.
    ///         The agent must have approved this contract (or the service must hold NCC).
    function burnForService(address agent, uint256 amount, string calldata serviceId) external {
        require(authorizedServices[msg.sender], "Not authorized service");
        require(balanceOf[agent] >= amount, "Insufficient NCC");
        _burn(agent, amount);
        agentComputeSpend[agent] += amount;
        emit BurnedForService(agent, msg.sender, amount, serviceId);
    }

    // -----------------------------------------------------------------------
    // Admin
    // -----------------------------------------------------------------------

    /// @notice Grant or revoke permission for a contract to call burnForService.
    function authorizeService(address service, bool authorized) external onlyOwner {
        authorizedServices[service] = authorized;
        emit ServiceAuthorized(service, authorized);
    }

    /// @notice Update the agent treasury address that receives redemption fees.
    function setAgentTreasury(address _treasury) external onlyOwner {
        agentTreasury = _treasury;
        emit TreasuryUpdated(_treasury);
    }

    // -----------------------------------------------------------------------
    // Receive — auto-mint on plain ETH transfers
    // -----------------------------------------------------------------------

    receive() external payable {
        _mint(msg.sender, msg.value);
        emit Minted(msg.sender, msg.value, msg.value);
    }

    // -----------------------------------------------------------------------
    // Internal helpers
    // -----------------------------------------------------------------------

    function _transfer(address from, address to, uint256 value) internal {
        require(from != address(0), "Transfer from zero");
        require(to != address(0), "Transfer to zero");
        require(balanceOf[from] >= value, "Insufficient balance");
        balanceOf[from] -= value;
        balanceOf[to]   += value;
        emit Transfer(from, to, value);
    }

    function _mint(address to, uint256 value) internal {
        totalSupply    += value;
        balanceOf[to]  += value;
        emit Transfer(address(0), to, value);
    }

    function _burn(address from, uint256 value) internal {
        require(balanceOf[from] >= value, "Burn exceeds balance");
        balanceOf[from] -= value;
        totalSupply     -= value;
        emit Transfer(from, address(0), value);
    }
}
