// SPDX-License-Identifier: MIT
pragma solidity ^0.8.28;

import {Test, console2} from "forge-std/Test.sol";
import {NexusComputeCredit} from "../src/NexusComputeCredit.sol";

contract NexusComputeCreditTest is Test {
    NexusComputeCredit public ncc;
    address public treasury = makeAddr("treasury");
    address public alice    = makeAddr("alice");
    address public service  = makeAddr("service");

    function setUp() public {
        ncc = new NexusComputeCredit(treasury);
    }

    function test_MintWithETH() public {
        vm.deal(alice, 1 ether);
        vm.prank(alice);
        ncc.mint{value: 0.5 ether}();
        assertEq(ncc.balanceOf(alice), 0.5 ether);
    }

    function test_MintViaReceive() public {
        vm.deal(alice, 1 ether);
        vm.prank(alice);
        (bool ok,) = address(ncc).call{value: 0.1 ether}("");
        assertTrue(ok);
        assertEq(ncc.balanceOf(alice), 0.1 ether);
    }

    function test_Redeem() public {
        vm.deal(alice, 1 ether);
        vm.prank(alice);
        ncc.mint{value: 1 ether}();
        uint256 aliceBefore = alice.balance;
        vm.prank(alice);
        ncc.redeem(1 ether);
        assertEq(ncc.balanceOf(alice), 0);
        // alice gets back 1 ether minus 0.1% fee
        uint256 fee = (1 ether * 10) / 10000;
        assertEq(alice.balance - aliceBefore, 1 ether - fee);
        assertGe(treasury.balance, fee);
    }

    function test_RedeemFeeGoesToTreasury() public {
        vm.deal(alice, 1 ether);
        vm.prank(alice);
        ncc.mint{value: 1 ether}();
        uint256 treasuryBefore = treasury.balance;
        vm.prank(alice);
        ncc.redeem(1 ether);
        uint256 expectedFee = (1 ether * 10) / 10000;
        assertEq(treasury.balance - treasuryBefore, expectedFee);
    }

    function test_BurnForService() public {
        // Setup: authorize service, fund alice
        ncc.authorizeService(service, true);
        vm.deal(alice, 1 ether);
        vm.prank(alice);
        ncc.mint{value: 0.5 ether}();
        // Service burns on alice's behalf
        vm.prank(service);
        ncc.burnForService(alice, 0.1 ether, "inference:gpt4o");
        assertEq(ncc.balanceOf(alice), 0.4 ether);
        assertEq(ncc.agentComputeSpend(alice), 0.1 ether);
    }

    function test_BurnForServiceUnauthorizedReverts() public {
        vm.deal(alice, 1 ether);
        vm.prank(alice);
        ncc.mint{value: 0.5 ether}();
        vm.prank(service); // not authorized
        vm.expectRevert("Not authorized service");
        ncc.burnForService(alice, 0.1 ether, "inference:gpt4o");
    }

    function test_RedeemInsufficientReverts() public {
        vm.deal(alice, 1 ether);
        vm.prank(alice);
        ncc.mint{value: 0.1 ether}();
        vm.prank(alice);
        vm.expectRevert("Insufficient NCC");
        ncc.redeem(0.5 ether);
    }

    // Fuzz: any ETH amount minted should mint exact NCC
    function testFuzz_MintAmount(uint96 amount) public {
        vm.assume(amount > 0);
        vm.deal(alice, amount);
        vm.prank(alice);
        ncc.mint{value: amount}();
        assertEq(ncc.balanceOf(alice), amount);
    }

    // Fuzz: redemption fee always <= 0.1% of amount
    function testFuzz_RedemptionFeeNeverExceeds(uint96 amount) public {
        vm.assume(amount > 10000); // avoid rounding to zero
        vm.deal(alice, amount);
        vm.prank(alice);
        ncc.mint{value: amount}();
        uint256 aliceBefore = alice.balance;
        vm.prank(alice);
        ncc.redeem(amount);
        uint256 returned = alice.balance - aliceBefore;
        uint256 maxFee   = (uint256(amount) * 10) / 10000 + 1;
        assertGe(returned + maxFee, amount);
    }
}
