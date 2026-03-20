"""
MoonPay CLI DCA demo — automated ETH purchase from yield budget.
Track: MoonPay CLI Agents ($3.5k)
"""
import os, json, subprocess
from dotenv import load_dotenv

load_dotenv()

def run_moonpay(args: list) -> dict:
    """Run MoonPay CLI command."""
    try:
        result = subprocess.run(
            ["npx", "@moonpay/cli"] + args,
            capture_output=True, text=True, timeout=60,
            env={**os.environ, "MOONPAY_API_KEY": os.getenv("MOONPAY_API_KEY", "")}
        )
        if result.returncode == 0 and result.stdout.strip():
            try:
                return json.loads(result.stdout)
            except json.JSONDecodeError:
                return {"output": result.stdout.strip(), "success": True}
        return {"error": result.stderr[:200], "demo": True}
    except FileNotFoundError:
        return {"demo": True, "note": "Install MoonPay CLI: npm install -g @moonpay/cli"}
    except Exception as e:
        return {"demo": True, "error": str(e)}

def setup_dca(token: str = "ETH", amount_usd: float = 50.0, frequency: str = "weekly") -> dict:
    """Set up recurring DCA from Nexus yield budget."""
    result = run_moonpay(["dca", "--token", token, "--amount", str(amount_usd), "--frequency", frequency])
    if result.get("demo"):
        return {
            "demo": True,
            "schedule": {
                "token": token,
                "amount_usd": amount_usd,
                "frequency": frequency,
                "funded_from": "wstETH_yield",
                "next_execution": "weekly",
                "status": "scheduled",
            },
            "note": result.get("note", "MoonPay CLI demo mode"),
        }
    return result

def get_portfolio() -> dict:
    """Get portfolio via MoonPay CLI."""
    result = run_moonpay(["portfolio", "--format", "json"])
    if result.get("demo"):
        return {
            "demo": True,
            "portfolio": {
                "total_value_usd": 2440.50,
                "assets": [
                    {"token": "ETH", "amount": 1.0, "value_usd": 2400.0, "chain": "ethereum"},
                    {"token": "USDC", "amount": 40.50, "value_usd": 40.50, "chain": "base"},
                ],
            }
        }
    return result

if __name__ == "__main__":
    print("=== MoonPay CLI DCA Demo ===")
    print(json.dumps(setup_dca("ETH", 50.0, "weekly"), indent=2))
    print("\n=== Portfolio ===")
    print(json.dumps(get_portfolio(), indent=2))
