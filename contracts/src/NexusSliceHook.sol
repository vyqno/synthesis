// SPDX-License-Identifier: MIT
pragma solidity ^0.8.28;

/**
 * @title NexusSliceHook
 * @notice Slice protocol pricing hook that adjusts product price based on the
 *         buyer's ERC-8004 reputation score stored in AgentIdentity.
 *
 *         Pricing rules:
 *           score > 80  → 20% discount  (finalPrice = basePrice * 80 / 100)
 *           score < 20  → 20% premium   (finalPrice = basePrice * 120 / 100)
 *           otherwise   → standard price (finalPrice = basePrice)
 *
 * @dev If the buyer has no registered agent identity (agentId == 0) they pay
 *      the standard price.
 */

interface IAgentIdentity {
    function getReputation(uint256 agentId) external view returns (uint256);
    function getAgentIdByAddress(address agent) external view returns (uint256);
}

contract NexusSliceHook {
    // -----------------------------------------------------------------------
    // Constants
    // -----------------------------------------------------------------------

    uint256 public constant DISCOUNT_THRESHOLD = 80;   // score > 80 → discount
    uint256 public constant PREMIUM_THRESHOLD  = 20;   // score < 20 → premium
    uint256 public constant DISCOUNT_BPS       = 8000; // 80% of base → 20% off
    uint256 public constant PREMIUM_BPS        = 12000; // 120% of base → 20% on
    uint256 public constant BPS_DENOM          = 10000;

    // -----------------------------------------------------------------------
    // State
    // -----------------------------------------------------------------------

    IAgentIdentity public identityRegistry;

    // -----------------------------------------------------------------------
    // Events
    // -----------------------------------------------------------------------

    event PriceCalculated(
        address indexed buyer,
        uint256 indexed productId,
        uint256 basePrice,
        uint256 finalPrice,
        uint256 reputationScore
    );

    // -----------------------------------------------------------------------
    // Constructor
    // -----------------------------------------------------------------------

    constructor(address _identityRegistry) {
        require(_identityRegistry != address(0), "Zero address");
        identityRegistry = IAgentIdentity(_identityRegistry);
    }

    // -----------------------------------------------------------------------
    // Hook interface
    // -----------------------------------------------------------------------

    /**
     * @notice Compute the final price for a buyer based on their reputation score.
     * @param buyer      Address of the prospective buyer.
     * @param basePrice  Standard product price.
     * @return finalPrice Adjusted price after applying reputation modifier.
     */
    function getPrice(
        address buyer,
        uint256 /* productId */,
        uint256 basePrice
    ) external view returns (uint256 finalPrice) {
        uint256 score = _getReputationSafe(buyer);
        finalPrice = _applyModifier(basePrice, score);
    }

    /**
     * @notice Same as getPrice but also emits an event (useful for off-chain
     *         tracking when called as a state-changing hook).
     */
    function applyPriceHook(
        address buyer,
        uint256 productId,
        uint256 basePrice
    ) external returns (uint256 finalPrice) {
        uint256 score = _getReputationSafe(buyer);
        finalPrice = _applyModifier(basePrice, score);
        emit PriceCalculated(buyer, productId, basePrice, finalPrice, score);
    }

    // -----------------------------------------------------------------------
    // Internal helpers
    // -----------------------------------------------------------------------

    /**
     * @dev Fetch reputation score; returns 50 (neutral) if buyer has no identity.
     */
    function _getReputationSafe(address buyer) internal view returns (uint256 score) {
        uint256 agentId = identityRegistry.getAgentIdByAddress(buyer);
        if (agentId == 0) {
            return 50; // unregistered buyers get neutral treatment
        }
        return identityRegistry.getReputation(agentId);
    }

    /**
     * @dev Apply pricing modifier based on reputation score.
     */
    function _applyModifier(uint256 basePrice, uint256 score) internal pure returns (uint256) {
        if (score > DISCOUNT_THRESHOLD) {
            // 20% discount
            return (basePrice * DISCOUNT_BPS) / BPS_DENOM;
        } else if (score < PREMIUM_THRESHOLD) {
            // 20% premium
            return (basePrice * PREMIUM_BPS) / BPS_DENOM;
        } else {
            // Standard price
            return basePrice;
        }
    }
}
