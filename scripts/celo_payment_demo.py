"""
Celo stablecoin payment demo for bond.credit / Celo Best Agent track.
Nexus agent pays for a service using cUSD on Celo mainnet.
"""
import os
from web3 import Web3
from eth_account import Account
from dotenv import load_dotenv

load_dotenv()

CELO_RPC = os.getenv("CELO_RPC_URL", "https://forno.celo.org")

# cUSD on Celo mainnet
CUSD_ADDRESS = "0x765DE816845861e75A25fCA122bb6898B8B1282a"
ERC20_ABI = [
    {"name": "transfer", "type": "function", "inputs": [{"name": "to", "type": "address"}, {"name": "amount", "type": "uint256"}], "outputs": [{"type": "bool"}], "stateMutability": "nonpayable"},
    {"name": "balanceOf", "type": "function", "inputs": [{"name": "account", "type": "address"}], "outputs": [{"type": "uint256"}], "stateMutability": "view"},
]

def demo_celo_payment(recipient: str, amount_cusd: float) -> dict:
    """Send cUSD payment on Celo — demonstrates agent-to-service payment."""
    w3 = Web3(Web3.HTTPProvider(CELO_RPC))
    pk = os.getenv("PRIVATE_KEY", "")

    if not pk:
        return {
            "demo": True,
            "chain": "celo",
            "token": "cUSD",
            "amount": amount_cusd,
            "recipient": recipient,
            "note": "Set PRIVATE_KEY to execute real payment",
        }

    account = Account.from_key(pk)
    cusd = w3.eth.contract(address=Web3.to_checksum_address(CUSD_ADDRESS), abi=ERC20_ABI)

    amount_wei = int(amount_cusd * 10**18)
    tx = cusd.functions.transfer(
        Web3.to_checksum_address(recipient), amount_wei
    ).build_transaction({
        "from": account.address,
        "nonce": w3.eth.get_transaction_count(account.address),
        "gas": 100000,
        "gasPrice": w3.eth.gas_price,
    })

    signed = account.sign_transaction(tx)
    tx_hash = w3.eth.send_raw_transaction(signed.raw_transaction)

    return {
        "tx_hash": tx_hash.hex(),
        "chain": "celo",
        "token": "cUSD",
        "amount": amount_cusd,
        "recipient": recipient,
        "status": "submitted",
    }

if __name__ == "__main__":
    # Demo: pay 0.10 cUSD to a service
    result = demo_celo_payment("0x742d35Cc6634C0532925a3b8D4C9C8e2F1234567", 0.10)
    import json
    print(json.dumps(result, indent=2))
