// SPDX-License-Identifier: MIT
pragma solidity ^0.8.28;

import {Script, console} from "forge-std/Script.sol";
import {AgentTreasury} from "../src/AgentTreasury.sol";
import {AgentIdentity} from "../src/AgentIdentity.sol";
import {NexusArbiter} from "../src/NexusArbiter.sol";
import {NexusSliceHook} from "../src/NexusSliceHook.sol";
import {NexusComputeCredit} from "../src/NexusComputeCredit.sol";
import {NexusYieldSplitter} from "../src/NexusYieldSplitter.sol";
import {NexusReputationStaking} from "../src/NexusReputationStaking.sol";
import {NexusPublicGoodsVault} from "../src/NexusPublicGoodsVault.sol";
import {AgentEscrow} from "../src/AgentEscrow.sol";

contract Deploy is Script {
    function run() external {
        uint256 pk = vm.envUint("PRIVATE_KEY");
        address deployer = vm.addr(pk);

        vm.startBroadcast(pk);

        // ---- Existing contracts ----
        AgentIdentity identity = new AgentIdentity();
        AgentTreasury treasury = new AgentTreasury(
            deployer,   // agent address (deployer for now)
            0.01 ether, // perTxCap
            1 hours     // timeWindow
        );
        NexusArbiter arbiter = new NexusArbiter();
        NexusSliceHook hook = new NexusSliceHook(address(identity));

        // ---- New contracts ----

        // 1. NexusComputeCredit: ETH-backed ERC-20 compute credit token
        NexusComputeCredit computeCredit = new NexusComputeCredit(address(treasury));

        // 2. NexusYieldSplitter: principal/yield splitter for wstETH
        NexusYieldSplitter yieldSplitter = new NexusYieldSplitter(address(treasury));

        // 3. NexusPublicGoodsVault: yield donation vault (Octant + Gitcoin)
        //    Placeholder beneficiary addresses — update before mainnet deploy.
        address octantPool  = address(0x1); // replace with real Octant pool
        address gitcoinAllo = address(0x2); // replace with real Gitcoin Allo contract
        NexusPublicGoodsVault pgVault = new NexusPublicGoodsVault(
            0x7f39C581F595B53c5cb19bD0b3f8dA6c935E2Ca0, // wstETH mainnet
            octantPool,
            gitcoinAllo
        );

        // 4. NexusReputationStaking: stake-to-guarantee with slashing
        NexusReputationStaking repStaking = new NexusReputationStaking(
            address(pgVault),    // slashed funds go to public goods vault
            address(identity)    // ERC-8004 identity registry
        );
        // Register deployer as initial validator
        repStaking.addValidator(deployer);

        // 5. AgentEscrow: ZK-verified agent job escrow with insurance pool
        AgentEscrow escrow = new AgentEscrow(address(arbiter));

        vm.stopBroadcast();

        // ---- Log addresses ----
        console.log("AgentIdentity:           ", address(identity));
        console.log("AgentTreasury:           ", address(treasury));
        console.log("NexusArbiter:            ", address(arbiter));
        console.log("NexusSliceHook:          ", address(hook));
        console.log("NexusComputeCredit:      ", address(computeCredit));
        console.log("NexusYieldSplitter:      ", address(yieldSplitter));
        console.log("NexusPublicGoodsVault:   ", address(pgVault));
        console.log("NexusReputationStaking:  ", address(repStaking));
        console.log("AgentEscrow:             ", address(escrow));
    }
}
