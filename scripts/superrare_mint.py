"""
SuperRare autonomous minting demo.
Nexus mints a commemorative NFT when yield milestones are hit.
Track: SuperRare Partner Track ($2.5k)
"""
import os, json, subprocess, hashlib, time
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

NFT_METADATA = {
    "name": "Nexus Proof of Computation #1",
    "description": "Autonomous agent milestone: Nexus earned its first yield-funded inference. "
                   "This NFT commemorates the moment the agent became financially self-sufficient.",
    "image": "ipfs://bafkreiabcdef1234567890",  # Placeholder IPFS CID
    "attributes": [
        {"trait_type": "Agent", "value": "nexus"},
        {"trait_type": "Milestone", "value": "First yield-funded inference"},
        {"trait_type": "Chain", "value": "Base Sepolia"},
        {"trait_type": "Autonomy", "value": "Full — no human intervention"},
    ],
}

def mint_milestone_nft() -> dict:
    """Mint a Nexus milestone NFT via Rare Protocol CLI."""
    # Try Rare CLI
    try:
        result = subprocess.run(
            ["npx", "@rareprotocol/rare-cli", "mint",
             "--name", NFT_METADATA["name"],
             "--description", NFT_METADATA["description"],
             "--network", "base-sepolia"],
            capture_output=True, text=True, timeout=60
        )
        if result.returncode == 0:
            return json.loads(result.stdout)
    except Exception:
        pass

    # Demo fallback
    token_id = int(hashlib.sha256(f"nexus-{time.time()}".encode()).hexdigest()[:8], 16)
    return {
        "demo": True,
        "token_id": token_id,
        "name": NFT_METADATA["name"],
        "chain": "base-sepolia",
        "contract": "0x" + hashlib.sha256(b"nexus-nft").hexdigest()[:40],
        "metadata": NFT_METADATA,
        "minted_by": "nexus-autonomous-agent",
        "note": "Install @rareprotocol/rare-cli and set PRIVATE_KEY for real mint",
    }

if __name__ == "__main__":
    result = mint_milestone_nft()
    print(json.dumps(result, indent=2))
