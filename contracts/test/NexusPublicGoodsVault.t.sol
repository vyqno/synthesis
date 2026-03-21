// SPDX-License-Identifier: MIT
pragma solidity ^0.8.28;

import {Test, console2} from "forge-std/Test.sol";
import {NexusPublicGoodsVault} from "../src/NexusPublicGoodsVault.sol";

/// @dev Minimal ERC-20 used as a mock wstETH in tests.
contract MockWstETH {
    string public name     = "Wrapped stETH";
    string public symbol   = "wstETH";
    uint8  public decimals = 18;

    uint256 public totalSupply;
    mapping(address => uint256) public balanceOf;
    mapping(address => mapping(address => uint256)) public allowance;

    event Transfer(address indexed from, address indexed to, uint256 amount);
    event Approval(address indexed owner, address indexed spender, uint256 amount);

    function mint(address to, uint256 amount) external {
        totalSupply     += amount;
        balanceOf[to]   += amount;
        emit Transfer(address(0), to, amount);
    }

    // Simulate yield accrual by minting extra tokens directly to vault
    function simulateYield(address vault, uint256 extraAmount) external {
        totalSupply          += extraAmount;
        balanceOf[vault]     += extraAmount;
        emit Transfer(address(0), vault, extraAmount);
    }

    function approve(address spender, uint256 amount) external returns (bool) {
        allowance[msg.sender][spender] = amount;
        emit Approval(msg.sender, spender, amount);
        return true;
    }

    function transfer(address to, uint256 amount) external returns (bool) {
        require(balanceOf[msg.sender] >= amount, "ERC20: insufficient balance");
        balanceOf[msg.sender] -= amount;
        balanceOf[to]         += amount;
        emit Transfer(msg.sender, to, amount);
        return true;
    }

    function transferFrom(address from, address to, uint256 amount) external returns (bool) {
        require(balanceOf[from] >= amount, "ERC20: insufficient balance");
        if (allowance[from][msg.sender] != type(uint256).max) {
            require(allowance[from][msg.sender] >= amount, "ERC20: insufficient allowance");
            allowance[from][msg.sender] -= amount;
        }
        balanceOf[from] -= amount;
        balanceOf[to]   += amount;
        emit Transfer(from, to, amount);
        return true;
    }
}

contract NexusPublicGoodsVaultTest is Test {
    NexusPublicGoodsVault public vault;
    MockWstETH            public wstETH;
    address public octant  = makeAddr("octant");
    address public gitcoin = makeAddr("gitcoin");
    address public alice   = makeAddr("alice");

    function setUp() public {
        wstETH = new MockWstETH();
        vault  = new NexusPublicGoodsVault(address(wstETH), octant, gitcoin);
        wstETH.mint(alice, 10 ether);
        vm.prank(alice);
        wstETH.approve(address(vault), type(uint256).max);
    }

    function test_Deposit() public {
        vm.prank(alice);
        vault.deposit(1 ether);
        assertEq(vault.balanceOf(alice), 1 ether);
        assertEq(wstETH.balanceOf(address(vault)), 1 ether);
    }

    function test_PGVSoulbound() public {
        vm.prank(alice);
        vault.deposit(1 ether);
        address bob = makeAddr("bob");
        vm.prank(alice);
        vm.expectRevert("PGV is soulbound \xe2\x80\x94 non-transferable");
        vault.transfer(bob, 0.5 ether);
    }

    function test_DistributeYield() public {
        vm.prank(alice);
        vault.deposit(5 ether);
        // Simulate 5% yield accrual (0.25 ETH on 5 ETH)
        wstETH.simulateYield(address(vault), 0.25 ether);
        vault.distributeYield();
        // 60% to Octant = 0.15 ETH
        assertEq(wstETH.balanceOf(octant), 0.15 ether);
        // 40% to Gitcoin = 0.1 ETH
        assertEq(wstETH.balanceOf(gitcoin), 0.1 ether);
        // Principal unchanged
        assertEq(vault.totalSupply(), 5 ether);
    }

    function test_NoYieldNothingDistributed() public {
        vm.prank(alice);
        vault.deposit(1 ether);
        vm.expectRevert("No yield to distribute");
        vault.distributeYield();
    }

    function test_GetVaultStats() public {
        vm.prank(alice);
        vault.deposit(3 ether);
        wstETH.simulateYield(address(vault), 0.3 ether);
        (uint256 deposited, uint256 yield, uint256 epoch,,) = vault.getVaultStats();
        assertEq(deposited, 3 ether);
        assertEq(yield, 0.3 ether);
        assertEq(epoch, 0);
    }

    function testFuzz_YieldSplitAlwaysCorrect(uint96 principal, uint96 yieldAmt) public {
        vm.assume(principal >= 0.01 ether);
        vm.assume(yieldAmt >= 100); // avoid rounding
        wstETH.mint(alice, principal);
        vm.prank(alice);
        vault.deposit(principal);
        wstETH.simulateYield(address(vault), yieldAmt);
        uint256 toOctant  = (uint256(yieldAmt) * 6000) / 10000;
        uint256 toGitcoin = uint256(yieldAmt) - toOctant;
        vault.distributeYield();
        assertEq(wstETH.balanceOf(octant), toOctant);
        assertEq(wstETH.balanceOf(gitcoin), toGitcoin);
    }
}
