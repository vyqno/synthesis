#!/bin/bash
# Deploy a Gnosis Safe multisig for Nexus
# Agent key (hot) + human recovery key (cold), threshold=1
# This ensures: if agent key compromised, human can recover funds

set -e

echo "=== Nexus Safe Multisig Setup ==="
echo ""
echo "This creates a 1-of-2 Safe:"
echo "  Owner 1: Agent wallet (hot key, operates automatically)"
echo "  Owner 2: Recovery wallet (cold key, human-controlled)"
echo "  Threshold: 1 (agent operates independently)"
echo ""

if [ -z "$AGENT_WALLET" ]; then
  echo "Error: AGENT_WALLET not set"
  echo "Usage: AGENT_WALLET=0x... RECOVERY_WALLET=0x... CHAIN=base bash scripts/setup_safe.sh"
  exit 1
fi

if [ -z "$RECOVERY_WALLET" ]; then
  echo "Error: RECOVERY_WALLET not set"
  exit 1
fi

CHAIN=${CHAIN:-base}
echo "Chain: $CHAIN"
echo "Agent wallet:    $AGENT_WALLET"
echo "Recovery wallet: $RECOVERY_WALLET"
echo ""

# Safe factory addresses (same on all major chains)
SAFE_FACTORY="0xa6B71E26C5e0845f74c812102Ca7114b6a896AB2"
SAFE_SINGLETON="0xd9Db270c1B5E3Bd161E8c8503c55cEABeE709552"

echo "Deploying Safe via factory: $SAFE_FACTORY"
echo ""
echo "Run this with cast or foundry:"
echo ""
echo "cast send $SAFE_FACTORY \\"
echo "  'createProxyWithNonce(address,bytes,uint256)' \\"
echo "  $SAFE_SINGLETON \\"
echo "  \$(cast abi-encode 'f(address[],uint256,address,bytes,address,address,uint256,address)' \\"
echo "    '[\"$AGENT_WALLET\",\"$RECOVERY_WALLET\"]' 1 \\"
echo "    0x0000000000000000000000000000000000000000 0x \\"
echo "    0x0000000000000000000000000000000000000000 \\"
echo "    0x0000000000000000000000000000000000000000 0 \\"
echo "    0x0000000000000000000000000000000000000000) \\"
echo "  \$NONCE \\"
echo "  --rpc-url \$${CHAIN^^}_RPC_URL \\"
echo "  --private-key \$PRIVATE_KEY"
echo ""
echo "After deployment, set NEXUS_SAFE_ADDRESS in .env"
echo "Then transfer ownership of all contracts to the Safe address."
