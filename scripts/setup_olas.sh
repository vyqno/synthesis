#!/bin/bash
# Olas Mech Marketplace setup
# Client: 10+ requests (Hire Agent track = $1k)
# Server: 50+ requests (Monetize Agent track = $1k)

echo "=== Olas Mech Setup ==="

# Install mech-client
pip install mech-client 2>/dev/null || echo "mech-client install: check pip"

# Check if mechx is available
if command -v mechx &> /dev/null; then
    echo "✓ mech-client installed"

    # Send 1 test request to Olas Mech Marketplace
    echo "Sending test request to Olas mech marketplace..."
    mechx interact --agent-id 2 --prompt "Is this a legitimate public good project? https://github.com/ethereum/ethereum-org-website" 2>/dev/null || echo "Olas mech request: needs PRIVATE_KEY and ETH on Gnosis Chain"
else
    echo "mechx not found — install: pip install mech-client"
fi

echo ""
echo "=== Olas Mech Server Setup ==="
pip install mech-server 2>/dev/null || echo "mech-server: check pip"

echo ""
echo "Manual steps:"
echo "1. Client: mechx interact --agent-id 2 --prompt 'your request'"
echo "   Repeat 10+ times for Hire Agent track"
echo "2. Server: Register nexus-scorer as mech server"
echo "   Visit: https://marketplace.olas.network"
echo "   Serve 50+ requests for Monetize track"
