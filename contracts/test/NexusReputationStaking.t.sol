// SPDX-License-Identifier: MIT
pragma solidity ^0.8.28;

import {Test, console2} from "forge-std/Test.sol";
import {NexusReputationStaking} from "../src/NexusReputationStaking.sol";

contract NexusReputationStakingTest is Test {
    NexusReputationStaking public staking;
    address public publicGoods = makeAddr("publicGoods");
    address public identity    = makeAddr("identity");
    address public agent       = makeAddr("agent");
    address public harmed      = makeAddr("harmed");
    address public val1        = makeAddr("val1");
    address public val2        = makeAddr("val2");
    address public val3        = makeAddr("val3");

    function setUp() public {
        staking = new NexusReputationStaking(publicGoods, identity);
        staking.addValidator(val1);
        staking.addValidator(val2);
        staking.addValidator(val3);
    }

    function test_Stake() public {
        vm.deal(agent, 1 ether);
        vm.prank(agent);
        staking.stake{value: 0.1 ether}();
        (uint256 amount,,) = staking.getStake(agent);
        assertEq(amount, 0.1 ether);
    }

    function test_StakeBelowMinimumReverts() public {
        vm.deal(agent, 1 ether);
        vm.prank(agent);
        vm.expectRevert("Below minimum stake");
        staking.stake{value: 0.001 ether}();
    }

    function test_UnstakeDelay() public {
        vm.deal(agent, 1 ether);
        vm.prank(agent);
        staking.stake{value: 0.1 ether}();
        vm.prank(agent);
        staking.requestUnstake();
        // Can't unstake immediately — cooldown not elapsed
        vm.prank(agent);
        vm.expectRevert("Cooldown not elapsed");
        staking.unstake();
        // Can unstake after 7 days
        vm.warp(block.timestamp + 7 days + 1);
        vm.prank(agent);
        staking.unstake();
        (uint256 amount,,) = staking.getStake(agent);
        assertEq(amount, 0);
    }

    function test_SlashWithQuorum() public {
        vm.deal(agent, 1 ether);
        vm.prank(agent);
        staking.stake{value: 0.5 ether}();

        uint256 harmedBefore = harmed.balance;
        uint256 goodsBefore  = publicGoods.balance;

        // 3 validators vote to slash 0.1 ETH
        vm.prank(val1);
        uint256 proposalId = staking.proposeSlash(agent, harmed, 0.1 ether, "Failed delivery");
        vm.prank(val2);
        staking.voteSlash(proposalId);
        vm.prank(val3);
        staking.voteSlash(proposalId); // triggers execution at quorum=3

        // 50% to harmed, 50% to public goods
        assertEq(harmed.balance - harmedBefore, 0.05 ether);
        assertEq(publicGoods.balance - goodsBefore, 0.05 ether);

        // Agent stake reduced
        (uint256 remaining,,) = staking.getStake(agent);
        assertEq(remaining, 0.4 ether);
    }

    function test_DoubleVoteReverts() public {
        vm.deal(agent, 1 ether);
        vm.prank(agent);
        staking.stake{value: 0.5 ether}();
        vm.prank(val1);
        uint256 proposalId = staking.proposeSlash(agent, harmed, 0.1 ether, "Fraud");
        vm.prank(val1);
        vm.expectRevert("Already voted");
        staking.voteSlash(proposalId);
    }

    function testFuzz_SlashNeverExceedsStake(uint96 stakeAmt, uint96 slashAmt) public {
        vm.assume(stakeAmt >= 0.01 ether);
        vm.assume(slashAmt > 0 && slashAmt <= stakeAmt);
        vm.deal(agent, stakeAmt);
        vm.prank(agent);
        staking.stake{value: stakeAmt}();
        uint256 actual = staking.effectiveSlashAmount(agent, slashAmt);
        assertLe(actual, stakeAmt);
    }
}
