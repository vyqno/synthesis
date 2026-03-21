// SPDX-License-Identifier: MIT
pragma solidity ^0.8.28;

import {Script, console2} from "forge-std/Script.sol";
import {AgentIdentity} from "../src/AgentIdentity.sol";
import {AgentTreasury} from "../src/AgentTreasury.sol";
import {AgentEscrow} from "../src/AgentEscrow.sol";
import {NexusComputeCredit} from "../src/NexusComputeCredit.sol";
import {NexusReputationStaking} from "../src/NexusReputationStaking.sol";
import {NexusPublicGoodsVault} from "../src/NexusPublicGoodsVault.sol";
import {NexusYieldSplitter} from "../src/NexusYieldSplitter.sol";
import {NexusArbiter} from "../src/NexusArbiter.sol";
import {NexusSliceHook} from "../src/NexusSliceHook.sol";

/**
 * @title DeployAll
 * @notice Deploys the full Nexus Protocol suite to Sepolia (or any EVM chain).
 *
 * Deploy order (dependency graph):
 *   1. NexusPublicGoodsVault  — no contract deps (only wstETH addr + beneficiary addrs)
 *   2. AgentIdentity          — no deps
 *   3. NexusArbiter           — no deps
 *   4. AgentTreasury          — no contract deps (agent addr = deployer initially)
 *   5. NexusComputeCredit     — needs AgentTreasury
 *   6. NexusReputationStaking — needs NexusPublicGoodsVault + AgentIdentity
 *   7. NexusYieldSplitter     — needs AgentTreasury
 *   8. AgentEscrow            — needs NexusArbiter
 *   9. NexusSliceHook         — needs AgentIdentity
 *
 * After deploy, cross-wire:
 *   - Register deployer as validator on NexusReputationStaking
 *   - Whitelist deployer address as yield recipient in AgentTreasury
 *   - Authorize AgentEscrow as a service on NexusComputeCredit
 *
 * Required env vars:
 *   PRIVATE_KEY          — deployer private key (0x-prefixed)
 *   SEPOLIA_RPC_URL      — Sepolia JSON-RPC URL
 *   ETHERSCAN_API_KEY    — For contract verification on Etherscan
 *
 * Sepolia wstETH: 0xB82381A3fBD3FaFA77B3a7bE693342618240067b
 * Octant / Gitcoin: placeholder addrs below — update before using real beneficiaries.
 */
contract DeployAll is Script {
    // -------------------------------------------------------------------------
    // Sepolia external addresses
    // -------------------------------------------------------------------------

    /// @dev wstETH on Sepolia testnet
    address public constant WSTETH_SEPOLIA = 0xB82381A3fBD3FaFA77B3a7bE693342618240067b;

    /// @dev Octant public goods pool — use deployer as placeholder on testnet
    address public constant OCTANT_POOL_PLACEHOLDER  = address(0);
    /// @dev Gitcoin Allo contract — use deployer as placeholder on testnet
    address public constant GITCOIN_ALLO_PLACEHOLDER = address(0);

    // -------------------------------------------------------------------------
    // Deployed contract references (readable after run())
    // -------------------------------------------------------------------------

    NexusPublicGoodsVault  public pgVault;
    AgentIdentity          public identity;
    NexusArbiter           public arbiter;
    AgentTreasury          public treasury;
    NexusComputeCredit     public computeCredit;
    NexusReputationStaking public repStaking;
    NexusYieldSplitter     public yieldSplitter;
    AgentEscrow            public escrow;
    NexusSliceHook         public sliceHook;

    // -------------------------------------------------------------------------
    // run()
    // -------------------------------------------------------------------------

    function run() external {
        uint256 deployerPrivateKey = vm.envUint("PRIVATE_KEY");
        address deployer = vm.addr(deployerPrivateKey);

        console2.log("=== Nexus Protocol -- Full Deployment ===");
        console2.log("Deployer:    ", deployer);
        console2.log("Chain ID:    ", block.chainid);
        console2.log("wstETH addr: ", WSTETH_SEPOLIA);
        console2.log("");

        vm.startBroadcast(deployerPrivateKey);

        // ------------------------------------------------------------------
        // 1. NexusPublicGoodsVault
        //    Receives slashed stake (50%) and wstETH yield donations.
        //    Distributes to Octant (60%) and Gitcoin (40%).
        //    Constructor: (address wstETH, address octantPool, address gitcoinAllo)
        // ------------------------------------------------------------------
        pgVault = new NexusPublicGoodsVault(
            WSTETH_SEPOLIA,
            OCTANT_POOL_PLACEHOLDER,
            GITCOIN_ALLO_PLACEHOLDER
        );
        console2.log("NexusPublicGoodsVault:  ", address(pgVault));

        // ------------------------------------------------------------------
        // 2. AgentIdentity
        //    ERC-8004 on-chain agent identity registry. No constructor args.
        // ------------------------------------------------------------------
        identity = new AgentIdentity();
        console2.log("AgentIdentity:          ", address(identity));

        // ------------------------------------------------------------------
        // 3. NexusArbiter
        //    Noir ZK proof arbiter for escrow release. No constructor args.
        // ------------------------------------------------------------------
        arbiter = new NexusArbiter();
        console2.log("NexusArbiter:           ", address(arbiter));

        // ------------------------------------------------------------------
        // 4. AgentTreasury
        //    Holds wstETH principal; agent may only withdraw accrued yield.
        //    Constructor: (address agent, uint256 perTxCap, uint256 timeWindow)
        //    - agent = deployer (operator wallet); can be updated via setAgent()
        //    - perTxCap = 0.01 wstETH per withdrawal (conservative for testnet)
        //    - timeWindow = 1 hour between withdrawals
        // ------------------------------------------------------------------
        treasury = new AgentTreasury(
            deployer,    // agent address
            0.01 ether,  // perTxCap (in wstETH units, same decimals as ETH)
            1 hours      // timeWindow
        );
        // Whitelist the deployer as an initial yield recipient
        treasury.setRecipient(deployer, true);
        console2.log("AgentTreasury:          ", address(treasury));

        // ------------------------------------------------------------------
        // 5. NexusComputeCredit
        //    ETH-backed ERC-20 compute credit token (1 NCC = 1 wei ETH).
        //    Constructor: (address agentTreasury)
        // ------------------------------------------------------------------
        computeCredit = new NexusComputeCredit(address(treasury));
        console2.log("NexusComputeCredit:     ", address(computeCredit));

        // ------------------------------------------------------------------
        // 6. NexusReputationStaking
        //    ETH stake with slashing. Slashed funds → harmed party + pgVault.
        //    Constructor: (address publicGoodsVault, address agentIdentity)
        // ------------------------------------------------------------------
        repStaking = new NexusReputationStaking(
            address(pgVault),
            address(identity)
        );
        // Register deployer as the initial slash validator
        repStaking.addValidator(deployer);
        console2.log("NexusReputationStaking: ", address(repStaking));

        // ------------------------------------------------------------------
        // 7. NexusYieldSplitter
        //    Pendle-style PT/YT splitter — yield streams to agent treasury.
        //    Constructor: (address agentTreasury)
        // ------------------------------------------------------------------
        yieldSplitter = new NexusYieldSplitter(address(treasury));
        console2.log("NexusYieldSplitter:     ", address(yieldSplitter));

        // ------------------------------------------------------------------
        // 8. AgentEscrow
        //    ZK-verified job escrow with insurance pool.
        //    Constructor: (address arbiter)
        // ------------------------------------------------------------------
        escrow = new AgentEscrow(address(arbiter));
        // Authorize AgentEscrow as a service on NexusComputeCredit so it can
        // burn NCC when verifying proofs on behalf of agents
        computeCredit.authorizeService(address(escrow), true);
        console2.log("AgentEscrow:            ", address(escrow));

        // ------------------------------------------------------------------
        // 9. NexusSliceHook
        //    Reputation-based pricing hook for Slice protocol.
        //    Constructor: (address identityRegistry)
        // ------------------------------------------------------------------
        sliceHook = new NexusSliceHook(address(identity));
        console2.log("NexusSliceHook:         ", address(sliceHook));

        vm.stopBroadcast();

        // ------------------------------------------------------------------
        // Summary
        // ------------------------------------------------------------------
        console2.log("");
        console2.log("=== Deployment complete ===");
        console2.log("Chain:                  ", block.chainid);
        console2.log("NexusPublicGoodsVault:  ", address(pgVault));
        console2.log("AgentIdentity:          ", address(identity));
        console2.log("NexusArbiter:           ", address(arbiter));
        console2.log("AgentTreasury:          ", address(treasury));
        console2.log("NexusComputeCredit:     ", address(computeCredit));
        console2.log("NexusReputationStaking: ", address(repStaking));
        console2.log("NexusYieldSplitter:     ", address(yieldSplitter));
        console2.log("AgentEscrow:            ", address(escrow));
        console2.log("NexusSliceHook:         ", address(sliceHook));
        console2.log("");
        console2.log("Next steps:");
        console2.log("  1. Update pgVault beneficiaries: setBeneficiaries(octant, gitcoin)");
        console2.log("  2. Register agent identity: identity.registerIdentity(...)");
        console2.log("  3. Add additional validators: repStaking.addValidator(...)");
        console2.log("  4. Deposit wstETH principal: treasury.depositPrincipal(amount)");
    }
}
