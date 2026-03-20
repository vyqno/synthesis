"""
Submit Nexus to all 46 Synthesis hackathon tracks.
UUIDs sourced from official catalog.

API Key: sk-synth-f2c6c01886727a42a9d59356234fedf07a257ad463ec6eaf
Team ID: 3786a8ddd43847fbae8a7d015769ff92
"""
import httpx, json, sys
from pathlib import Path

API_KEY = "sk-synth-f2c6c01886727a42a9d59356234fedf07a257ad463ec6eaf"
TEAM_ID = "3786a8ddd43847fbae8a7d015769ff92"
BASE_URL = "https://synthesis.devfolio.co"
HEADERS = {"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"}

# All 46 official track UUIDs
ALL_TRACK_UUIDS = [
    "fdb76d08812b43f6a5f454744b66f590",  # Synthesis Open Track ($28,308)
    "ea3b366947c54689bd82ae80bf9f3310",  # Venice Private Agents ($11,500)
    "53c67bb0b07e42a894c597691e3a0a38",  # EigenCompute ($5,000)
    "bf374c2134344629aaadb5d6e639e840",  # Base Autonomous Trading ($5,000)
    "6f0e3d7dcadf4ef080d3f424963caff5",  # Base Agent Services ($5,000)
    "ee885a40e4bc4d3991546cec7a4433e2",  # Lido MCP ($5,000)
    "ff26ab4933c84eea856a5c6bf513370b",  # Celo Best Agent ($5,000)
    "dcaf0b1bf5d44c72a34bb771008e137a",  # Bankr LLM Gateway ($5,000)
    "0d69d56a8a084ac5b7dbe0dc1da73e1d",  # MetaMask Delegations ($5,000)
    "020214c160fc43339dd9833733791e6b",  # Uniswap Agentic Finance ($5,000)
    "9bd8b3fde4d0458698d618daf496d1c7",  # OpenServ Ship Real ($4,500)
    "10bd47fac07e4f85bda33ba482695b24",  # Protocol Labs Let Cook ($4,000)
    "3bf41be958da497bbb69f1a150c76af9",  # Protocol Labs Receipts ($4,000)
    "e5bc7301d9d141b087f0818ac57093c4",  # OpenWallet Standard ($3,500)
    "c1ca310ae1f34a88917f176ad963cf1e",  # MoonPay CLI Agents ($3,500)
    "5e445a077b5248e0974904915f76e1a0",  # Lido stETH Treasury ($3,000)
    "f50e31188e2641bc93764e7a6f26b0f6",  # Locus ($3,000)
    "f467eea3352b4a289814a522377fcef6",  # Student Founder's Bet ($2,500)
    "228747d95f734d87bb8668a682a2ae4d",  # SuperRare ($2,500)
    "49a19e54cdde48a6a22bd7604d07292e",  # Filecoin Agentic Storage ($2,000)
    "49c3d90b1f084c44a3585231dc733f83",  # ERC-8183 Virtuals ($2,000)
    "877cd61516a14ad9a199bf48defec1c1",  # Status Network Gasless ($2,000)
    "3d066b16b9df417db1b40d7003c6ee1e",  # Lido Vault Monitor ($1,500)
    "17ddda1d3cd1483aa4cfc45d493ac653",  # bond.credit Agents That Pay ($1,500)
    "77b1c93b6d1e490aa68fe7e04b373ee0",  # Olas Build Pearl ($1,000)
    "7d6e542ff0674030925fbc2c7ef96210",  # Olas Hire Agent ($1,000)
    "39a7beeb14544f89bf82d90ae3bdf3a4",  # Olas Monetize ($1,000)
    "32de074327bd4f6d935798d285becdfb",  # Octant Mechanism Design ($1,000)
    "4026705215f3401db4f2092f7219561b",  # Octant Data Analysis ($1,000)
    "db41ba89c2214fc18ef707331645d3fe",  # Octant Data Collection ($1,000)
    "437781b864994698b2a304227e277b56",  # Self Agent ID ($1,000)
    "54ee4ff8d9464d25b4a0d84b46a5c63d",  # Markee GitHub ($800)
    "01bd7148fc204cdebaa483c214db6e38",  # Slice ERC-8128 ($750)
    "ee0a4e9045464e779371ce829de17893",  # Slice Future of Commerce ($750)
    "2fbae4d45a574470bf343983efc75456",  # Slice Hooks ($700)
    "58be0ff54518490fb94bf2b0f58bb78c",  # Zyfai Yield Agents ($600)
    "627a3f5a288344489fe777212b03f953",  # ENS Identity ($600)
    "9c4599cf9d0f4002b861ff1a4b27f10a",  # ENS Communication ($600)
    "e67bac3ceece40b1a4b55786a7af6b0c",  # Zyfai Native Wallet ($500)
    "a73320342ae74465b8e71e5336442dc3",  # OpenServ Build Story ($500)
    "620805b8c88140bcbdf8bb4fe18048ce",  # ampersend ($500)
    "d6c88674390b4150a9ead015443a1375",  # Zyfai Infrastructure ($400)
    "88e91d848daf4d1bb0d40dec0074f59e",  # ENS Open Integration ($300)
    "f15ad8a517cf49cfbe6cbf6dc218ec7a",  # Arkhai Applications ($450)
    "8840da28fb3b46bcb08465e1d0e8756d",  # Arkhai Escrow Extensions ($450)
    "567c06ae27d3490e8457dece05b2d81b",  # Lit Chipotle ($250)
]

def get_catalog() -> list:
    with httpx.Client(timeout=30) as client:
        resp = client.get(f"{BASE_URL}/catalog", headers=HEADERS)
        resp.raise_for_status()
        return resp.json()

def create_project(track_uuids: list) -> dict:
    payload = {
        "teamUUID": TEAM_ID,
        "name": "Nexus",
        "description": (
            "An autonomous agent that earns its own compute budget from DeFi yield "
            "and runs an entire economy of specialized sub-agents — without a single human in the loop. "
            "8 MCP servers exposing 57 tools, 4 Solidity contracts (43 tests), 3 Noir ZK circuits, "
            "self-funding wstETH treasury, OpenClaw skill discovery, EigenCompute Docker deployment, "
            "and coverage of all 46 Synthesis tracks."
        ),
        "repoURL": "https://github.com/vyqno/synthesis",
        "trackUUIDs": track_uuids,
        "submissionMetadata": {
            "demoURL": "https://nexus-agent.xyz",
            "skillFileURL": "https://raw.githubusercontent.com/vyqno/synthesis/main/nexus.skill.md",
            "agentManifestURL": "https://raw.githubusercontent.com/vyqno/synthesis/main/agent.json",
            "mcpEndpoint": "https://nexus-agent.xyz/mcp",
            "eigencomputeArch": "https://raw.githubusercontent.com/vyqno/synthesis/main/docs/eigencompute-architecture.md",
        },
    }
    with httpx.Client(timeout=60) as client:
        resp = client.post(f"{BASE_URL}/projects", headers=HEADERS, json=payload)
        resp.raise_for_status()
        return resp.json()

def transfer_custody() -> dict:
    with httpx.Client(timeout=30) as client:
        resp = client.post(f"{BASE_URL}/participants/me/transfer/init", headers=HEADERS)
        resp.raise_for_status()
        return resp.json()

def publish_project(project_uuid: str) -> dict:
    with httpx.Client(timeout=30) as client:
        resp = client.post(f"{BASE_URL}/projects/{project_uuid}/publish", headers=HEADERS)
        resp.raise_for_status()
        return resp.json()

if __name__ == "__main__":
    dry_run = "--dry-run" in sys.argv

    print(f"Nexus Submission — {len(ALL_TRACK_UUIDS)} tracks")
    print(f"Team: {TEAM_ID}")
    print(f"Mode: {'DRY RUN' if dry_run else 'LIVE'}")
    print()

    if dry_run:
        print("DRY RUN — would submit:")
        for uuid in ALL_TRACK_UUIDS:
            print(f"  {uuid}")
        sys.exit(0)

    try:
        print("Creating project...")
        project = create_project(ALL_TRACK_UUIDS)
        project_uuid = project.get("uuid", project.get("id", ""))
        print(f"Project created: {project_uuid}")

        print("Publishing...")
        result = publish_project(project_uuid)
        print(f"Published: {result}")
        print(f"\nProject UUID: {project_uuid}")

        # Update STATUS.md
        status_path = Path("/home/vyqno/synthesis-hackathon/nexus/STATUS.md")
        if status_path.exists():
            content = status_path.read_text()
            content = content.replace("| Project created | No |", "| Project created | Yes |")
            content = content.replace("| Project UUID | — |", f"| Project UUID | {project_uuid} |")
            content = content.replace("| Published | No |", "| Published | Yes |")
            status_path.write_text(content)
            print("STATUS.md updated")

    except Exception as e:
        print(f"Error: {e}")
        print("Check API key and connectivity")
        sys.exit(1)
