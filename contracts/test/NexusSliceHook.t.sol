// SPDX-License-Identifier: MIT
pragma solidity ^0.8.28;

import {Test} from "forge-std/Test.sol";
import {NexusSliceHook} from "../src/NexusSliceHook.sol";
import {AgentIdentity} from "../src/AgentIdentity.sol";

contract NexusSliceHookTest is Test {
    AgentIdentity internal identity;
    NexusSliceHook internal hook;

    address internal highRepBuyer  = address(0xAAAA);
    address internal lowRepBuyer   = address(0xBBBB);
    address internal midRepBuyer   = address(0xCCCC);
    address internal unknownBuyer  = address(0xDDDD); // not registered

    uint256 internal constant BASE_PRICE = 1 ether;

    function setUp() public {
        identity = new AgentIdentity();
        hook     = new NexusSliceHook(address(identity));

        // Register three buyers with different reputation scores
        vm.prank(highRepBuyer);
        identity.registerIdentity("HighRep Agent", "highrep.eth", "");

        vm.prank(lowRepBuyer);
        identity.registerIdentity("LowRep Agent", "lowrep.eth", "");

        vm.prank(midRepBuyer);
        identity.registerIdentity("Mid Agent", "mid.eth", "");

        // Set scores (owner is the test contract)
        uint256 highId = identity.getAgentIdByAddress(highRepBuyer);
        uint256 lowId  = identity.getAgentIdByAddress(lowRepBuyer);
        uint256 midId  = identity.getAgentIdByAddress(midRepBuyer);

        identity.updateReputation(highId, 90); // > 80 → 20% discount
        identity.updateReputation(lowId,  10); // < 20 → 20% premium
        identity.updateReputation(midId,  50); // 20–80 → standard
    }

    // -----------------------------------------------------------------------
    // High reputation: 20% discount
    // -----------------------------------------------------------------------

    function test_highRep_gets20PercentDiscount() public view {
        uint256 price = hook.getPrice(highRepBuyer, 1, BASE_PRICE);
        // Expected: 1 ether * 80 / 100 = 0.8 ether
        assertEq(price, (BASE_PRICE * 8000) / 10000);
    }

    function test_highRep_exactThreshold() public {
        // Score exactly 81 → still discount
        uint256 agentId = identity.getAgentIdByAddress(highRepBuyer);
        identity.updateReputation(agentId, 81);
        uint256 price = hook.getPrice(highRepBuyer, 1, BASE_PRICE);
        assertEq(price, (BASE_PRICE * 8000) / 10000);
    }

    function test_highRep_scoreOf100() public {
        uint256 agentId = identity.getAgentIdByAddress(highRepBuyer);
        identity.updateReputation(agentId, 100);
        uint256 price = hook.getPrice(highRepBuyer, 1, BASE_PRICE);
        assertEq(price, (BASE_PRICE * 8000) / 10000);
    }

    // -----------------------------------------------------------------------
    // Low reputation: 20% premium
    // -----------------------------------------------------------------------

    function test_lowRep_gets20PercentPremium() public view {
        uint256 price = hook.getPrice(lowRepBuyer, 1, BASE_PRICE);
        // Expected: 1 ether * 120 / 100 = 1.2 ether
        assertEq(price, (BASE_PRICE * 12000) / 10000);
    }

    function test_lowRep_exactThreshold() public {
        // Score exactly 19 → still premium
        uint256 agentId = identity.getAgentIdByAddress(lowRepBuyer);
        identity.updateReputation(agentId, 19);
        uint256 price = hook.getPrice(lowRepBuyer, 1, BASE_PRICE);
        assertEq(price, (BASE_PRICE * 12000) / 10000);
    }

    function test_lowRep_scoreOf0() public {
        uint256 agentId = identity.getAgentIdByAddress(lowRepBuyer);
        identity.updateReputation(agentId, 0);
        uint256 price = hook.getPrice(lowRepBuyer, 1, BASE_PRICE);
        assertEq(price, (BASE_PRICE * 12000) / 10000);
    }

    // -----------------------------------------------------------------------
    // Mid reputation: standard price
    // -----------------------------------------------------------------------

    function test_midRep_getsStandardPrice() public view {
        uint256 price = hook.getPrice(midRepBuyer, 1, BASE_PRICE);
        assertEq(price, BASE_PRICE);
    }

    function test_midRep_boundaryLow() public {
        // Score == 20 → not < 20, so standard price
        uint256 agentId = identity.getAgentIdByAddress(midRepBuyer);
        identity.updateReputation(agentId, 20);
        uint256 price = hook.getPrice(midRepBuyer, 1, BASE_PRICE);
        assertEq(price, BASE_PRICE);
    }

    function test_midRep_boundaryHigh() public {
        // Score == 80 → not > 80, so standard price
        uint256 agentId = identity.getAgentIdByAddress(midRepBuyer);
        identity.updateReputation(agentId, 80);
        uint256 price = hook.getPrice(midRepBuyer, 1, BASE_PRICE);
        assertEq(price, BASE_PRICE);
    }

    // -----------------------------------------------------------------------
    // Unknown buyer (not registered) — neutral treatment
    // -----------------------------------------------------------------------

    function test_unknownBuyer_getsStandardPrice() public view {
        // agentId == 0 → score defaults to 50 in the hook
        uint256 price = hook.getPrice(unknownBuyer, 1, BASE_PRICE);
        assertEq(price, BASE_PRICE);
    }

    // -----------------------------------------------------------------------
    // Different base prices
    // -----------------------------------------------------------------------

    function test_discount_withDifferentBasePrice() public view {
        uint256 base  = 500;
        uint256 price = hook.getPrice(highRepBuyer, 99, base);
        assertEq(price, (base * 8000) / 10000); // 400
    }

    function test_premium_withDifferentBasePrice() public view {
        uint256 base  = 500;
        uint256 price = hook.getPrice(lowRepBuyer, 99, base);
        assertEq(price, (base * 12000) / 10000); // 600
    }

    // -----------------------------------------------------------------------
    // applyPriceHook (emitting variant)
    // -----------------------------------------------------------------------

    function test_applyPriceHook_emitsEvent() public {
        vm.expectEmit(true, true, false, true);
        emit NexusSliceHook.PriceCalculated(
            highRepBuyer,
            1,
            BASE_PRICE,
            (BASE_PRICE * 8000) / 10000,
            90
        );
        hook.applyPriceHook(highRepBuyer, 1, BASE_PRICE);
    }

    // -----------------------------------------------------------------------
    // Fuzz: price is always within expected range
    // -----------------------------------------------------------------------

    function testFuzz_priceRange(uint256 score, uint256 basePrice) public {
        score     = bound(score, 0, 100);
        basePrice = bound(basePrice, 0, 1_000_000 ether);

        uint256 agentId = identity.getAgentIdByAddress(midRepBuyer);
        identity.updateReputation(agentId, score);

        uint256 price = hook.getPrice(midRepBuyer, 1, basePrice);

        if (score > 80) {
            assertEq(price, (basePrice * 8000) / 10000);
        } else if (score < 20) {
            assertEq(price, (basePrice * 12000) / 10000);
        } else {
            assertEq(price, basePrice);
        }
    }
}
