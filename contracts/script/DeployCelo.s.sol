// SPDX-License-Identifier: MIT
pragma solidity ^0.8.28;

import {Script, console} from "forge-std/Script.sol";
import {AgentTreasury} from "../src/AgentTreasury.sol";

contract DeployCelo is Script {
    // USDC on Celo (use as treasury asset)
    address constant CUSDC = 0xcebA9300f2b948710d2653dD7B07f33A8B32118C;

    function run() external {
        uint256 pk = vm.envUint("PRIVATE_KEY");
        address deployer = vm.addr(pk);

        vm.startBroadcast(pk);

        AgentTreasury treasury = new AgentTreasury(
            deployer,
            0.01 ether,
            1 hours
        );

        vm.stopBroadcast();

        console.log("AgentTreasury on Celo:", address(treasury));
        console.log("cUSD/cEUR payments enabled");
    }
}
