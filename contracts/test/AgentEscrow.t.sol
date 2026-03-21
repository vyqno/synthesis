// SPDX-License-Identifier: MIT
pragma solidity ^0.8.28;

import {Test, console2} from "forge-std/Test.sol";
import {AgentEscrow} from "../src/AgentEscrow.sol";

contract MockArbiter {
    bool public shouldVerify = true;

    function verifyDelivery(bytes32, bytes calldata, bytes32[] calldata) external view returns (bool) {
        return shouldVerify;
    }

    function setVerify(bool v) external {
        shouldVerify = v;
    }
}

contract AgentEscrowTest is Test {
    AgentEscrow   public escrow;
    MockArbiter   public arbiter;
    address public hirer = makeAddr("hirer");
    address public agent = makeAddr("agent");

    function setUp() public {
        arbiter = new MockArbiter();
        escrow  = new AgentEscrow(address(arbiter));
        vm.deal(hirer, 10 ether);
    }

    function _createJob() internal returns (bytes32 jobId) {
        vm.prank(hirer);
        jobId = escrow.createJob{value: 1 ether}(
            agent,
            keccak256("deliver: summarize https://arxiv.org/123"),
            1 days,
            "Summarize paper"
        );
    }

    function test_CreateJob() public {
        bytes32 jobId     = _createJob();
        AgentEscrow.Job memory job = escrow.getJob(jobId);
        assertEq(job.hirer, hirer);
        assertEq(job.agent, agent);
        // 2% insurance fee deducted
        assertEq(job.payment, 0.98 ether);
        assertEq(uint8(job.status), uint8(AgentEscrow.JobStatus.Open));
    }

    function test_InsurancePoolFunded() public {
        _createJob();
        assertEq(escrow.insurancePool(), 0.02 ether); // 2% of 1 ETH
    }

    function test_ClaimPaymentWithProof() public {
        bytes32 jobId     = _createJob();
        uint256 agentBefore = agent.balance;
        vm.prank(agent);
        escrow.claimPayment(jobId, abi.encode("mock_proof"), new bytes32[](0));
        assertEq(agent.balance - agentBefore, 0.98 ether);
        assertEq(uint8(escrow.getJob(jobId).status), uint8(AgentEscrow.JobStatus.Paid));
        assertEq(escrow.agentJobsCompleted(agent), 1);
    }

    function test_ClaimPaymentFailsIfProofFails() public {
        arbiter.setVerify(false);
        bytes32 jobId = _createJob();
        vm.prank(agent);
        vm.expectRevert("Proof verification failed");
        escrow.claimPayment(jobId, abi.encode("bad_proof"), new bytes32[](0));
    }

    function test_LateDeliveryPenalty() public {
        bytes32 jobId = _createJob();
        // Warp past deadline
        vm.warp(block.timestamp + 2 days);
        uint256 agentBefore = agent.balance;
        vm.prank(agent);
        escrow.claimPayment(jobId, abi.encode("late_proof"), new bytes32[](0));
        uint256 earned  = agent.balance - agentBefore;
        uint256 penalty = (0.98 ether * 1000) / 10000; // 10%
        assertEq(earned, 0.98 ether - penalty);
    }

    function test_CancelExpired() public {
        bytes32 jobId = _createJob();
        vm.warp(block.timestamp + 2 days + 1);
        uint256 hirerBefore = hirer.balance;
        escrow.cancelExpired(jobId);
        uint256 refund = (0.98 ether * 9000) / 10000;
        assertEq(hirer.balance - hirerBefore, refund);
        assertEq(escrow.agentJobsFailed(agent), 1);
    }

    function test_DisputeJob() public {
        bytes32 jobId = _createJob();
        vm.prank(hirer);
        escrow.disputeJob(jobId);
        assertEq(uint8(escrow.getJob(jobId).status), uint8(AgentEscrow.JobStatus.Disputed));
    }

    function test_NonAgentCannotClaim() public {
        bytes32 jobId = _createJob();
        vm.prank(hirer);
        vm.expectRevert("Not the assigned agent");
        escrow.claimPayment(jobId, abi.encode("proof"), new bytes32[](0));
    }

    function testFuzz_InsuranceFeeAlways2Pct(uint96 payment) public {
        vm.assume(payment >= 0.01 ether);
        vm.deal(hirer, payment);
        vm.prank(hirer);
        bytes32 jobId = escrow.createJob{value: payment}(
            agent, keccak256("task"), 1 days, "test"
        );
        uint256 expectedFee = (uint256(payment) * 200) / 10000;
        assertEq(escrow.insurancePool(), expectedFee);
        assertEq(escrow.getJob(jobId).payment, uint256(payment) - expectedFee);
    }
}
