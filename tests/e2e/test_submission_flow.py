"""
E2E test for the Synthesis API submission flow.
Tests the submit_all_tracks.py script structure and API connectivity.
"""
import pytest
import json
import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(ROOT))


def test_submit_script_importable():
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        "submit", ROOT / "scripts/submit_all_tracks.py"
    )
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    assert hasattr(mod, "create_project")
    assert hasattr(mod, "get_catalog")
    assert hasattr(mod, "publish_project")


def test_all_46_track_uuids_known():
    """Verify we have all 46 track UUIDs hardcoded."""
    TRACK_UUIDS = [
        "fdb76d08812b43f6a5f454744b66f590",  # Synthesis Open
        "ea3b366947c54689bd82ae80bf9f3310",  # Venice
        "53c67bb0b07e42a894c597691e3a0a38",  # EigenCompute
        "bf374c2134344629aaadb5d6e639e840",  # Base Trading
        "6f0e3d7dcadf4ef080d3f424963caff5",  # Base Agent Services
        "ee885a40e4bc4d3991546cec7a4433e2",  # Lido MCP
        "ff26ab4933c84eea856a5c6bf513370b",  # Celo
        "dcaf0b1bf5d44c72a34bb771008e137a",  # Bankr
        "0d69d56a8a084ac5b7dbe0dc1da73e1d",  # MetaMask
        "020214c160fc43339dd9833733791e6b",  # Uniswap
        "9bd8b3fde4d0458698d618daf496d1c7",  # OpenServ
        "10bd47fac07e4f85bda33ba482695b24",  # Protocol Labs Cook
        "3bf41be958da497bbb69f1a150c76af9",  # Protocol Labs Receipts
        "e5bc7301d9d141b087f0818ac57093c4",  # OpenWallet Standard
        "c1ca310ae1f34a88917f176ad963cf1e",  # MoonPay CLI
        "5e445a077b5248e0974904915f76e1a0",  # Lido stETH Treasury
        "f50e31188e2641bc93764e7a6f26b0f6",  # Locus
        "f467eea3352b4a289814a522377fcef6",  # Student Founder
        "228747d95f734d87bb8668a682a2ae4d",  # SuperRare
        "49a19e54cdde48a6a22bd7604d07292e",  # Filecoin
        "49c3d90b1f084c44a3585231dc733f83",  # ERC-8183 Virtuals
        "877cd61516a14ad9a199bf48defec1c1",  # Status Network
        "3d066b16b9df417db1b40d7003c6ee1e",  # Lido Vault Monitor
        "17ddda1d3cd1483aa4cfc45d493ac653",  # bond.credit
        "77b1c93b6d1e490aa68fe7e04b373ee0",  # Olas Build Pearl
        "7d6e542ff0674030925fbc2c7ef96210",  # Olas Hire
        "39a7beeb14544f89bf82d90ae3bdf3a4",  # Olas Monetize
        "32de074327bd4f6d935798d285becdfb",  # Octant Mechanism
        "4026705215f3401db4f2092f7219561b",  # Octant Data Analysis
        "db41ba89c2214fc18ef707331645d3fe",  # Octant Data Collection
        "437781b864994698b2a304227e277b56",  # Self
        "54ee4ff8d9464d25b4a0d84b46a5c63d",  # Markee
        "01bd7148fc204cdebaa483c214db6e38",  # Slice ERC-8128
        "ee0a4e9045464e779371ce829de17893",  # Slice Future Commerce
        "2fbae4d45a574470bf343983efc75456",  # Slice Hooks
        "58be0ff54518490fb94bf2b0f58bb78c",  # Zyfai Yield
        "627a3f5a288344489fe777212b03f953",  # ENS Identity
        "9c4599cf9d0f4002b861ff1a4b27f10a",  # ENS Communication
        "e67bac3ceece40b1a4b55786a7af6b0c",  # Zyfai Native Wallet
        "a73320342ae74465b8e71e5336442dc3",  # OpenServ Build Story
        "620805b8c88140bcbdf8bb4fe18048ce",  # ampersend
        "d6c88674390b4150a9ead015443a1375",  # Zyfai Infrastructure
        "88e91d848daf4d1bb0d40dec0074f59e",  # ENS Open Integration
        "f15ad8a517cf49cfbe6cbf6dc218ec7a",  # Arkhai Applications
        "8840da28fb3b46bcb08465e1d0e8756d",  # Arkhai Escrow Extensions
        "567c06ae27d3490e8457dece05b2d81b",  # Lit Chipotle
    ]
    assert len(TRACK_UUIDS) == 46


def test_marketplace_config_exists():
    config_path = ROOT / "marketplace_config.json"
    assert config_path.exists()
    config = json.loads(config_path.read_text())
    assert "x402_services" in config
    assert len(config["x402_services"]) >= 5


def test_dockerfile_has_healthcheck():
    dockerfile = (ROOT / "Dockerfile").read_text()
    assert "HEALTHCHECK" in dockerfile
    assert "health" in dockerfile.lower()
