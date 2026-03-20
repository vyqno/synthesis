// SPDX-License-Identifier: MIT
pragma solidity ^0.8.28;

import {Script, console} from "forge-std/Script.sol";
import {AgentTreasury} from "../src/AgentTreasury.sol";
import {AgentIdentity} from "../src/AgentIdentity.sol";
import {NexusArbiter} from "../src/NexusArbiter.sol";
import {NexusSliceHook} from "../src/NexusSliceHook.sol";

contract Deploy is Script {
    function run() external {
        uint256 pk = vm.envUint("PRIVATE_KEY");
        address deployer = vm.addr(pk);

        vm.startBroadcast(pk);

        AgentIdentity identity = new AgentIdentity();
        AgentTreasury treasury = new AgentTreasury(
            deployer,   // agent address (deployer for now)
            0.01 ether, // perTxCap
            1 hours     // timeWindow
        );
        NexusArbiter arbiter = new NexusArbiter();
        NexusSliceHook hook = new NexusSliceHook(address(identity));

        vm.stopBroadcast();

        console.log("AgentIdentity:", address(identity));
        console.log("AgentTreasury:", address(treasury));
        console.log("NexusArbiter:", address(arbiter));
        console.log("NexusSliceHook:", address(hook));
    }
}
