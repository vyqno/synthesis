// SPDX-License-Identifier: MIT
pragma solidity ^0.8.28;

import {Test, console} from "forge-std/Test.sol";
import {AgentTreasury} from "../src/AgentTreasury.sol";

// ---------------------------------------------------------------------------
// Mock wstETH — a minimal ERC-20 that lets us control the balance freely.
// ---------------------------------------------------------------------------
contract MockWstETH {
    mapping(address => uint256) public balanceOf;
    mapping(address => mapping(address => uint256)) public allowance;

    function mint(address to, uint256 amount) external {
        balanceOf[to] += amount;
    }

    /// @dev Simulate yield accrual by crediting the treasury directly.
    function simulateYield(address treasury, uint256 yieldAmount) external {
        balanceOf[treasury] += yieldAmount;
    }

    function approve(address spender, uint256 amount) external returns (bool) {
        allowance[msg.sender][spender] = amount;
        return true;
    }

    function transfer(address to, uint256 amount) external returns (bool) {
        require(balanceOf[msg.sender] >= amount, "Insufficient balance");
        balanceOf[msg.sender] -= amount;
        balanceOf[to] += amount;
        return true;
    }

    function transferFrom(address from, address to, uint256 amount) external returns (bool) {
        require(balanceOf[from] >= amount, "Insufficient balance");
        require(allowance[from][msg.sender] >= amount, "Insufficient allowance");
        allowance[from][msg.sender] -= amount;
        balanceOf[from] -= amount;
        balanceOf[to] += amount;
        return true;
    }
}

// ---------------------------------------------------------------------------
// Harness — overrides the hardcoded WSTETH constant so we can inject our mock.
// ---------------------------------------------------------------------------
contract AgentTreasuryHarness is AgentTreasury {
    address public mockWstETH;

    constructor(address _agent, uint256 _perTxCap, uint256 _timeWindow, address _mockWstETH)
        AgentTreasury(_agent, _perTxCap, _timeWindow)
    {
        mockWstETH = _mockWstETH;
    }

    // Shadow the constant functions to route through the mock token.
    function totalBalance() public view override returns (uint256) {
        return MockWstETH(mockWstETH).balanceOf(address(this));
    }

    // Override WSTETH usage in depositPrincipal / withdrawYield / withdrawPrincipal
    // by re-implementing them using mockWstETH.

    function depositPrincipalMock(uint256 wstEthAmount) external {
        MockWstETH(mockWstETH).transferFrom(msg.sender, address(this), wstEthAmount);
        principalShares += wstEthAmount;
        emit PrincipalDeposited(msg.sender, wstEthAmount, wstEthAmount);
    }

    function withdrawYieldMock(uint256 amount, address recipient) external onlyAgent {
        require(recipientWhitelist[recipient], "Recipient not whitelisted");
        require(amount <= perTxCap, "Exceeds per-tx cap");
        require(block.timestamp >= lastWithdrawal + timeWindow, "Time window not elapsed");

        uint256 available = accruedYield();
        require(amount <= available, "Amount exceeds accrued yield");

        lastWithdrawal = block.timestamp;
        MockWstETH(mockWstETH).transfer(recipient, amount);
        emit YieldWithdrawn(recipient, amount, accruedYield());
    }

    function withdrawPrincipalMock(uint256 amount) external onlyOwner {
        require(amount <= principalShares, "Amount exceeds principal");
        principalShares -= amount;
        MockWstETH(mockWstETH).transfer(owner, amount);
    }
}

// ---------------------------------------------------------------------------
// Tests
// ---------------------------------------------------------------------------
contract AgentTreasuryTest is Test {
    MockWstETH internal wstETH;
    AgentTreasuryHarness internal treasury;

    address internal owner   = address(this);
    address internal agent   = address(0xA9e4);
    address internal recipient = address(0xBEEF);

    uint256 internal constant PER_TX_CAP  = 1 ether;
    uint256 internal constant TIME_WINDOW = 1 hours;
    uint256 internal constant PRINCIPAL   = 10 ether;

    function setUp() public {
        wstETH   = new MockWstETH();
        treasury = new AgentTreasuryHarness(agent, PER_TX_CAP, TIME_WINDOW, address(wstETH));

        // Whitelist recipient
        treasury.setRecipient(recipient, true);

        // Fund owner and deposit principal
        wstETH.mint(owner, PRINCIPAL);
        wstETH.approve(address(treasury), PRINCIPAL);
        treasury.depositPrincipalMock(PRINCIPAL);
    }

    // -----------------------------------------------------------------------
    // Yield calculation
    // -----------------------------------------------------------------------

    function test_noYieldInitially() public view {
        assertEq(treasury.accruedYield(), 0);
    }

    function test_yieldAfterBalanceIncrease() public {
        // Simulate wstETH rebasing — credit 2 ETH of yield directly
        wstETH.simulateYield(address(treasury), 2 ether);
        assertEq(treasury.accruedYield(), 2 ether);
    }

    function test_totalBalance() public {
        wstETH.simulateYield(address(treasury), 0.5 ether);
        assertEq(treasury.totalBalance(), PRINCIPAL + 0.5 ether);
    }

    // -----------------------------------------------------------------------
    // withdrawYield — success path
    // -----------------------------------------------------------------------

    function test_withdrawYield_success() public {
        wstETH.simulateYield(address(treasury), 2 ether);

        // Advance time past the window
        vm.warp(block.timestamp + TIME_WINDOW);

        uint256 amount = 0.5 ether;
        vm.prank(agent);
        treasury.withdrawYieldMock(amount, recipient);

        assertEq(wstETH.balanceOf(recipient), amount);
        assertEq(treasury.accruedYield(), 2 ether - amount);
    }

    // -----------------------------------------------------------------------
    // withdrawYield — exceed per-tx cap
    // -----------------------------------------------------------------------

    function test_withdrawYield_exceedsCap() public {
        wstETH.simulateYield(address(treasury), 5 ether);
        vm.warp(block.timestamp + TIME_WINDOW);

        vm.prank(agent);
        vm.expectRevert("Exceeds per-tx cap");
        treasury.withdrawYieldMock(PER_TX_CAP + 1, recipient);
    }

    // -----------------------------------------------------------------------
    // withdrawYield — unwhitelisted recipient
    // -----------------------------------------------------------------------

    function test_withdrawYield_unwhitelistedRecipient() public {
        wstETH.simulateYield(address(treasury), 2 ether);
        vm.warp(block.timestamp + TIME_WINDOW);

        vm.prank(agent);
        vm.expectRevert("Recipient not whitelisted");
        treasury.withdrawYieldMock(0.1 ether, address(0xDEAD));
    }

    // -----------------------------------------------------------------------
    // withdrawYield — time window not elapsed
    // -----------------------------------------------------------------------

    function test_withdrawYield_timeWindowNotElapsed() public {
        wstETH.simulateYield(address(treasury), 2 ether);
        // Do NOT warp time

        vm.prank(agent);
        vm.expectRevert("Time window not elapsed");
        treasury.withdrawYieldMock(0.1 ether, recipient);
    }

    function test_withdrawYield_timeWindowEnforced_secondCall() public {
        wstETH.simulateYield(address(treasury), 2 ether);
        vm.warp(block.timestamp + TIME_WINDOW);

        vm.prank(agent);
        treasury.withdrawYieldMock(0.1 ether, recipient);

        // Second call immediately after — should fail
        vm.prank(agent);
        vm.expectRevert("Time window not elapsed");
        treasury.withdrawYieldMock(0.1 ether, recipient);

        // After waiting the window it should work again
        vm.warp(block.timestamp + TIME_WINDOW);
        vm.prank(agent);
        treasury.withdrawYieldMock(0.1 ether, recipient);
    }

    // -----------------------------------------------------------------------
    // withdrawYield — amount exceeds accrued yield
    // -----------------------------------------------------------------------

    function test_withdrawYield_exceedsYield() public {
        wstETH.simulateYield(address(treasury), 0.5 ether);
        vm.warp(block.timestamp + TIME_WINDOW);

        vm.prank(agent);
        vm.expectRevert("Amount exceeds accrued yield");
        treasury.withdrawYieldMock(0.6 ether, recipient); // only 0.5 available
    }

    function test_withdrawYield_zeroYield() public {
        // No yield simulated — accrued == 0
        vm.warp(block.timestamp + TIME_WINDOW);

        vm.prank(agent);
        vm.expectRevert("Amount exceeds accrued yield");
        treasury.withdrawYieldMock(1, recipient);
    }

    // -----------------------------------------------------------------------
    // Principal protection — agent cannot call withdrawPrincipal
    // -----------------------------------------------------------------------

    function test_principalProtection_agentCannotWithdraw() public {
        vm.prank(agent);
        vm.expectRevert("Not owner");
        treasury.withdrawPrincipalMock(1 ether);
    }

    function test_principalProtection_ownerCanWithdraw() public {
        uint256 before = wstETH.balanceOf(owner);
        treasury.withdrawPrincipalMock(1 ether);
        assertEq(wstETH.balanceOf(owner), before + 1 ether);
        assertEq(treasury.principalShares(), PRINCIPAL - 1 ether);
    }

    function test_principalProtection_cannotExceedPrincipal() public {
        vm.expectRevert("Amount exceeds principal");
        treasury.withdrawPrincipalMock(PRINCIPAL + 1);
    }

    // -----------------------------------------------------------------------
    // Fuzz test: withdrawYield reverts when amount > accrued yield
    // -----------------------------------------------------------------------

    function testFuzz_withdrawYield_revertWhenExceedsYield(uint256 extraYield, uint256 withdrawAmount) public {
        // Bound extra yield to something reasonable
        extraYield = bound(extraYield, 0, 50 ether);
        wstETH.simulateYield(address(treasury), extraYield);

        vm.warp(block.timestamp + TIME_WINDOW);

        uint256 yield = treasury.accruedYield();

        // Bound withdrawAmount to (yield+1, perTxCap) — must exceed yield but fit cap
        // If yield >= perTxCap there's nothing valid to test here
        if (yield >= PER_TX_CAP) return;

        withdrawAmount = bound(withdrawAmount, yield + 1, PER_TX_CAP);

        vm.prank(agent);
        vm.expectRevert("Amount exceeds accrued yield");
        treasury.withdrawYieldMock(withdrawAmount, recipient);
    }

    // -----------------------------------------------------------------------
    // Admin setters
    // -----------------------------------------------------------------------

    function test_setPerTxCap() public {
        treasury.setPerTxCap(2 ether);
        assertEq(treasury.perTxCap(), 2 ether);
    }

    function test_setAgent() public {
        address newAgent = address(0x1234);
        treasury.setAgent(newAgent);
        assertEq(treasury.agent(), newAgent);
    }

    function test_setRecipient_removeFromWhitelist() public {
        treasury.setRecipient(recipient, false);
        assertFalse(treasury.recipientWhitelist(recipient));
    }
}
