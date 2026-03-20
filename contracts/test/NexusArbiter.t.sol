// SPDX-License-Identifier: MIT
pragma solidity ^0.8.28;

import {Test} from "forge-std/Test.sol";
import {NexusArbiter} from "../src/NexusArbiter.sol";

contract NexusArbiterTest is Test {
    NexusArbiter internal arbiter;

    bytes32 internal constant ESCROW_ID   = keccak256("test-escrow-1");
    bytes32 internal constant RESULT_HASH = keccak256("api-result-payload");
    uint256 internal constant DEADLINE_OFFSET = 1 days;

    function setUp() public {
        arbiter = new NexusArbiter();
    }

    // -----------------------------------------------------------------------
    // createEscrow
    // -----------------------------------------------------------------------

    function test_createEscrow_success() public {
        uint256 deadline = block.timestamp + DEADLINE_OFFSET;
        arbiter.createEscrow(ESCROW_ID, address(0), RESULT_HASH, deadline);

        (address verifier,, uint256 storedDeadline, bool released, bool exists) =
            arbiter.escrows(ESCROW_ID);

        assertTrue(exists);
        assertFalse(released);
        assertEq(storedDeadline, deadline);
        assertEq(verifier, address(0));
    }

    function test_createEscrow_revert_alreadyExists() public {
        uint256 deadline = block.timestamp + DEADLINE_OFFSET;
        arbiter.createEscrow(ESCROW_ID, address(0), RESULT_HASH, deadline);

        vm.expectRevert("Escrow already exists");
        arbiter.createEscrow(ESCROW_ID, address(0), RESULT_HASH, deadline);
    }

    function test_createEscrow_revert_deadlineInPast() public {
        vm.expectRevert("Deadline in the past");
        arbiter.createEscrow(ESCROW_ID, address(0), RESULT_HASH, block.timestamp - 1);
    }

    // -----------------------------------------------------------------------
    // verifyDelivery — mock mode (verifier == address(0))
    // -----------------------------------------------------------------------

    function test_verifyDelivery_mockMode_success() public {
        uint256 deadline = block.timestamp + DEADLINE_OFFSET;
        arbiter.createEscrow(ESCROW_ID, address(0), RESULT_HASH, deadline);

        bytes32[] memory inputs = new bytes32[](0);
        bool ok = arbiter.verifyDelivery(ESCROW_ID, "proof-bytes", inputs);
        assertTrue(ok);
        assertTrue(arbiter.isReleased(ESCROW_ID));
    }

    function test_verifyDelivery_mockMode_emptyProofFails() public {
        uint256 deadline = block.timestamp + DEADLINE_OFFSET;
        arbiter.createEscrow(ESCROW_ID, address(0), RESULT_HASH, deadline);

        bytes32[] memory inputs = new bytes32[](0);
        bool ok = arbiter.verifyDelivery(ESCROW_ID, "", inputs);
        assertFalse(ok);
        assertFalse(arbiter.isReleased(ESCROW_ID));
    }

    function test_verifyDelivery_revert_unknownEscrow() public {
        bytes32[] memory inputs = new bytes32[](0);
        vm.expectRevert("Unknown escrow");
        arbiter.verifyDelivery(keccak256("no-such-escrow"), "proof", inputs);
    }

    function test_verifyDelivery_revert_alreadyReleased() public {
        uint256 deadline = block.timestamp + DEADLINE_OFFSET;
        arbiter.createEscrow(ESCROW_ID, address(0), RESULT_HASH, deadline);

        bytes32[] memory inputs = new bytes32[](0);
        arbiter.verifyDelivery(ESCROW_ID, "proof", inputs);

        vm.expectRevert("Already released");
        arbiter.verifyDelivery(ESCROW_ID, "proof", inputs);
    }

    function test_verifyDelivery_revert_deadlinePassed() public {
        uint256 deadline = block.timestamp + 1 hours;
        arbiter.createEscrow(ESCROW_ID, address(0), RESULT_HASH, deadline);

        vm.warp(deadline + 1);

        bytes32[] memory inputs = new bytes32[](0);
        vm.expectRevert("Deadline passed");
        arbiter.verifyDelivery(ESCROW_ID, "proof", inputs);
    }

    // -----------------------------------------------------------------------
    // isActive / isReleased helpers
    // -----------------------------------------------------------------------

    function test_isActive_beforeRelease() public {
        arbiter.createEscrow(ESCROW_ID, address(0), RESULT_HASH, block.timestamp + 1 hours);
        assertTrue(arbiter.isActive(ESCROW_ID));
    }

    function test_isActive_afterRelease() public {
        arbiter.createEscrow(ESCROW_ID, address(0), RESULT_HASH, block.timestamp + 1 hours);
        bytes32[] memory inputs = new bytes32[](0);
        arbiter.verifyDelivery(ESCROW_ID, "proof", inputs);
        assertFalse(arbiter.isActive(ESCROW_ID));
        assertTrue(arbiter.isReleased(ESCROW_ID));
    }

    // -----------------------------------------------------------------------
    // arbitrate() IArbiter interface
    // -----------------------------------------------------------------------

    function test_arbitrate_mockMode() public {
        arbiter.createEscrow(ESCROW_ID, address(0), RESULT_HASH, block.timestamp + 1 hours);

        bytes memory proof = "proof-data";
        bytes32[] memory inputs = new bytes32[](0);
        bytes memory arbitrationData = abi.encode(proof, inputs);

        bool ok = arbiter.arbitrate(ESCROW_ID, arbitrationData);
        assertTrue(ok);
    }

    // -----------------------------------------------------------------------
    // EscrowReleased event
    // -----------------------------------------------------------------------

    function test_verifyDelivery_emitsEscrowReleased() public {
        arbiter.createEscrow(ESCROW_ID, address(0), RESULT_HASH, block.timestamp + 1 hours);

        bytes32[] memory inputs = new bytes32[](0);
        vm.expectEmit(true, true, false, false);
        emit NexusArbiter.EscrowReleased(ESCROW_ID, address(this), inputs);
        arbiter.verifyDelivery(ESCROW_ID, "proof", inputs);
    }
}
