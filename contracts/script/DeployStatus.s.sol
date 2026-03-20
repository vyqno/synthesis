// SPDX-License-Identifier: MIT
pragma solidity ^0.8.28;

import {Script, console} from "forge-std/Script.sol";
import {AgentTreasury} from "../src/AgentTreasury.sol";

contract DeployStatus is Script {
    function run() external {
        uint256 pk = vm.envUint("PRIVATE_KEY");
        address deployer = vm.addr(pk);

        vm.startBroadcast(pk);

        AgentTreasury treasury = new AgentTreasury(
            deployer,     // agent
            0.01 ether,   // perTxCap
            1 hours       // timeWindow
        );

        vm.stopBroadcast();

        console.log("AgentTreasury on Status Network:", address(treasury));
        console.log("Gasless tx demo: gas=0 supported by Status Network");
    }
}
