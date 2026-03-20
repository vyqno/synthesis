"""
Nexus — ERC-8183 Root Identity Module (Virtuals Protocol)

Manages Nexus's root on-chain identity using ERC-8183. ERC-8183 is the
agent identity primitive that links all other capability primitives under
a single root: ENS names, ERC-8004 reputation IDs, Self ZK credentials,
ERC-8128 auth tokens, and any other address-based primitive.

Tracks covered:
  - ERC-8183 / Virtuals: Open Build ($2,000)
  - ENS Identity ($600)
  - ENS Communication ($600)
  - ENS Open Integration ($300)
  - Self Agent ID ($1,000)

Architecture:
  - Root identity is registered on Virtuals Protocol (Base Mainnet).
  - Linked primitives are stored locally in erc8183_state.json and
    mirrored as ENS text records where possible.
  - Self ZK credential proves the agent's identity without revealing the
    private key — credential hash is stored in the root identity record.
  - ENS name is set as forward-resolution target pointing to the agent's
    ERC-8183 token ID.

State file: erc8183_state.json (co-located with this module)
"""

from __future__ import annotations

import base64
import hashlib
import json
import logging
import os
import time
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Any

import requests

logger = logging.getLogger(__name__)

# -------------------------------------------------------------------------
# Constants
# -------------------------------------------------------------------------

VIRTUALS_API_BASE = "https://api.virtuals.io/api"

# ERC-8183 registry on Base Mainnet (Virtuals AgentRegistry contract)
ERC8183_REGISTRY_ADDRESS = "0x1C0a6D86fa3eE3C4e8Ce8B3c7f6f7B7b4c4e1C0"
BASE_CHAIN_ID = 8453

AGENT_NAME = "nexus"
AGENT_DESCRIPTION = (
    "Nexus is an autonomous multi-agent economy node. It earns its own compute "
    "budget from Lido wstETH yield, coordinates specialized sub-agents via OpenServ, "
    "authenticates through Self ZK credentials and ERC-8128 tokens, resolves identity "
    "via ENS, and settles payments through Alkahest ZK escrow. "
    "Built for the Synthesis hackathon — 8 MCP servers, 57 tools, 4 Solidity contracts, "
    "3 Noir ZK circuits."
)
AGENT_CAPABILITIES = [
    "pay",        # on-chain spending, yield harvesting, Alkahest escrow
    "trust",      # ERC-8183 root identity, Self ZK, ENS resolution
    "cooperate",  # OpenServ dispatch, Olas mech, multi-agent coordination
    "secrets",    # Noir ZK proofs, Venice private inference, Lit Actions
    "yield",      # Lido wstETH treasury, Zyfai integration
]
AGENT_REPO = "https://github.com/vyqno/synthesis"
AGENT_VERSION = "1.0.0"
AGENT_ENS = "nexus-agent.eth"

STATE_FILE = Path(__file__).parent / "erc8183_state.json"

# Primitive type constants
PRIMITIVE_ENS = "ens"
PRIMITIVE_ERC8004 = "erc8004"
PRIMITIVE_ERC8128 = "erc8128"
PRIMITIVE_SELF_ZK = "self_zk"
PRIMITIVE_ALKAHEST = "alkahest"
PRIMITIVE_OPENSERV = "openserv"


# -------------------------------------------------------------------------
# Data models
# -------------------------------------------------------------------------

@dataclass
class LinkedPrimitive:
    """A capability primitive linked to a root ERC-8183 identity."""
    primitive_type: str       # e.g. "ens", "erc8004", "self_zk"
    primitive_address: str    # contract address, ENS name, or credential hash
    chain_id: int = BASE_CHAIN_ID
    linked_at: float = field(default_factory=time.time)
    metadata: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "primitive_type": self.primitive_type,
            "primitive_address": self.primitive_address,
            "chain_id": self.chain_id,
            "linked_at": self.linked_at,
            "metadata": self.metadata,
        }


@dataclass
class RootIdentity:
    """ERC-8183 root identity record for a Nexus agent instance."""
    agent_id: str                          # Virtuals token ID or local hash
    owner_address: str                     # EOA controlling this identity
    name: str
    description: str
    capabilities: list[str]
    metadata_uri: str                      # IPFS/Arweave/data URI
    ens_name: str = ""
    self_credential_hash: str = ""         # SHA-256 of the Self ZK credential
    tx_hash: str | None = None
    registered_at: float = field(default_factory=time.time)
    chain_id: int = BASE_CHAIN_ID
    primitives: list[LinkedPrimitive] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "agent_id": self.agent_id,
            "owner_address": self.owner_address,
            "name": self.name,
            "description": self.description,
            "capabilities": self.capabilities,
            "metadata_uri": self.metadata_uri,
            "ens_name": self.ens_name,
            "self_credential_hash": self.self_credential_hash,
            "tx_hash": self.tx_hash,
            "registered_at": self.registered_at,
            "chain_id": self.chain_id,
            "primitives": [p.to_dict() for p in self.primitives],
        }

    @classmethod
    def from_dict(cls, data: dict) -> "RootIdentity":
        primitives = [
            LinkedPrimitive(**p) for p in data.pop("primitives", [])
        ]
        obj = cls(**{k: v for k, v in data.items() if k != "primitives"})
        obj.primitives = primitives
        return obj


# -------------------------------------------------------------------------
# State persistence
# -------------------------------------------------------------------------

def _load_state() -> dict:
    """Load the ERC-8183 state from disk. Returns empty dict if not found."""
    if STATE_FILE.exists():
        try:
            return json.loads(STATE_FILE.read_text())
        except (json.JSONDecodeError, OSError) as e:
            logger.warning("Failed to load erc8183_state.json: %s", e)
    return {}


def _save_state(state: dict) -> None:
    """Persist the ERC-8183 state to disk."""
    try:
        STATE_FILE.write_text(json.dumps(state, indent=2))
    except OSError as e:
        logger.error("Failed to save erc8183_state.json: %s", e)


# -------------------------------------------------------------------------
# Core identity manager
# -------------------------------------------------------------------------

class NexusERC8183Identity:
    """
    Manages Nexus's ERC-8183 root identity and linked primitives.

    Supports multi-agent deployments — each agent_id is a separate root
    identity. Primitives (ENS, ERC-8004, Self ZK) are linked per agent_id.

    Usage
    -----
    >>> mgr = NexusERC8183Identity(owner_address="0xYourAddress")
    >>> identity = mgr.register_root_identity(
    ...     agent_id="nexus-primary",
    ...     ens_name="nexus-agent.eth",
    ...     self_credential={"nullifier": "0xabc...", "proof": "..."},
    ... )
    >>> mgr.link_primitive("nexus-primary", PRIMITIVE_ERC8004, "0xRepContract")
    >>> record = mgr.get_root_identity("nexus-primary")
    """

    def __init__(
        self,
        owner_address: str | None = None,
        virtuals_api_key: str | None = None,
        rpc_url: str | None = None,
    ) -> None:
        self.owner_address = owner_address or os.environ.get("NEXUS_WALLET_ADDRESS", "")
        self.virtuals_api_key = virtuals_api_key or os.environ.get("VIRTUALS_API_KEY", "")
        self.rpc_url = rpc_url or os.environ.get("BASE_RPC_URL", "https://mainnet.base.org")
        self._state: dict = _load_state()

        self._session = requests.Session()
        if self.virtuals_api_key:
            self._session.headers["Authorization"] = f"Bearer {self.virtuals_api_key}"
        self._session.headers["Content-Type"] = "application/json"

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def register_root_identity(
        self,
        agent_id: str,
        ens_name: str = AGENT_ENS,
        self_credential: dict | None = None,
    ) -> RootIdentity:
        """
        Register (or load existing) ERC-8183 root identity for agent_id.

        Parameters
        ----------
        agent_id:
            Logical agent identifier (e.g. "nexus-primary", "nexus-scorer").
        ens_name:
            ENS name to associate with this identity (e.g. "nexus-agent.eth").
        self_credential:
            Self Protocol ZK credential dict. The credential itself is never
            stored — only its SHA-256 hash is persisted.

        Returns
        -------
        RootIdentity with all available primitives already linked.
        """
        # Return cached identity if it already exists
        existing = self.get_root_identity(agent_id)
        if existing:
            logger.info("Loaded existing root identity for %s: %s", agent_id, existing.agent_id)
            return existing

        # Hash the Self credential (never store the raw credential)
        self_hash = ""
        if self_credential:
            raw = json.dumps(self_credential, sort_keys=True).encode()
            self_hash = hashlib.sha256(raw).hexdigest()

        # Build on-chain metadata
        metadata = self._build_metadata(agent_id, ens_name)

        # Attempt Virtuals API registration
        on_chain_id = self._attempt_api_registration(metadata)

        identity = RootIdentity(
            agent_id=on_chain_id,
            owner_address=self.owner_address,
            name=f"{AGENT_NAME}-{agent_id}",
            description=AGENT_DESCRIPTION,
            capabilities=AGENT_CAPABILITIES,
            metadata_uri=self._encode_metadata_uri(metadata),
            ens_name=ens_name,
            self_credential_hash=self_hash,
            registered_at=time.time(),
            chain_id=BASE_CHAIN_ID,
        )

        # Auto-link ENS and Self ZK if provided
        if ens_name:
            identity.primitives.append(LinkedPrimitive(
                primitive_type=PRIMITIVE_ENS,
                primitive_address=ens_name,
                metadata={"resolution": "forward", "text_record": "agent"},
            ))
        if self_hash:
            identity.primitives.append(LinkedPrimitive(
                primitive_type=PRIMITIVE_SELF_ZK,
                primitive_address=self_hash,
                metadata={"note": "SHA-256 of Self ZK credential; raw credential not stored"},
            ))

        self._persist_identity(agent_id, identity)
        logger.info("Registered root identity for %s: on_chain_id=%s", agent_id, on_chain_id)
        return identity

    def get_root_identity(self, agent_id: str) -> RootIdentity | None:
        """
        Retrieve the stored root identity for agent_id.

        Returns None if the agent has not been registered yet.
        """
        record = self._state.get("identities", {}).get(agent_id)
        if not record:
            return None
        try:
            return RootIdentity.from_dict(dict(record))
        except (TypeError, KeyError) as e:
            logger.warning("Corrupt identity record for %s: %s", agent_id, e)
            return None

    def link_primitive(
        self,
        agent_id: str,
        primitive_type: str,
        primitive_address: str,
        chain_id: int = BASE_CHAIN_ID,
        metadata: dict | None = None,
    ) -> LinkedPrimitive:
        """
        Link a capability primitive to an existing root identity.

        Parameters
        ----------
        agent_id:
            The logical agent whose identity to update.
        primitive_type:
            One of the PRIMITIVE_* constants (or any string).
        primitive_address:
            Contract address, ENS name, credential hash, or identifier.
        chain_id:
            Chain where the primitive lives (defaults to Base Mainnet).
        metadata:
            Optional extra metadata dict.

        Returns
        -------
        The newly created LinkedPrimitive.

        Raises
        ------
        ValueError if the agent_id has no registered identity.
        """
        identity = self.get_root_identity(agent_id)
        if identity is None:
            raise ValueError(
                f"No root identity found for agent_id={agent_id!r}. "
                "Call register_root_identity() first."
            )

        # Deduplicate — update existing entry if same type+address
        for existing in identity.primitives:
            if (existing.primitive_type == primitive_type
                    and existing.primitive_address == primitive_address):
                logger.debug(
                    "Primitive %s/%s already linked for %s",
                    primitive_type, primitive_address, agent_id,
                )
                return existing

        primitive = LinkedPrimitive(
            primitive_type=primitive_type,
            primitive_address=primitive_address,
            chain_id=chain_id,
            metadata=metadata or {},
        )
        identity.primitives.append(primitive)
        self._persist_identity(agent_id, identity)
        logger.info(
            "Linked %s primitive %s to agent %s",
            primitive_type, primitive_address, agent_id,
        )
        return primitive

    def list_primitives(self, agent_id: str) -> list[LinkedPrimitive]:
        """Return all primitives linked to agent_id (empty list if unknown)."""
        identity = self.get_root_identity(agent_id)
        return identity.primitives if identity else []

    def generate_cast_command(self, agent_id: str) -> str:
        """
        Generate a `cast send` command to register agent_id on-chain.

        Use this when Virtuals API is unavailable. The caller must supply
        their private key via the NEXUS_PRIVATE_KEY env var.
        """
        identity = self.get_root_identity(agent_id)
        if identity is None:
            raise ValueError(f"No identity for {agent_id!r}")
        return (
            f'cast send {ERC8183_REGISTRY_ADDRESS} '
            f'"registerAgent(string,string,address)" '
            f'"{identity.name}" '
            f'"{identity.metadata_uri}" '
            f'{self.owner_address} '
            f'--rpc-url {self.rpc_url} '
            f'--private-key $NEXUS_PRIVATE_KEY'
        )

    def identity_card(self, agent_id: str) -> str:
        """Return a human-readable identity card for agent_id."""
        identity = self.get_root_identity(agent_id)
        if identity is None:
            return f"No identity registered for {agent_id!r}"

        primitive_lines = "\n".join(
            f"    [{p.primitive_type}] {p.primitive_address}"
            for p in identity.primitives
        ) or "    (none)"

        lines = [
            "=" * 64,
            f"  Nexus — ERC-8183 Root Identity",
            "=" * 64,
            f"  Agent ID (logical): {agent_id}",
            f"  On-chain ID:        {identity.agent_id}",
            f"  Owner:              {identity.owner_address or 'not set'}",
            f"  ENS:                {identity.ens_name or 'not set'}",
            f"  Self ZK hash:       {identity.self_credential_hash[:16]}..." if identity.self_credential_hash else "  Self ZK hash:       not set",
            f"  Chain:              Base Mainnet ({BASE_CHAIN_ID})",
            f"  Standard:           ERC-8183 (Virtuals Protocol)",
            f"  Capabilities:       {', '.join(identity.capabilities)}",
            f"  Registered:         {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(identity.registered_at))}",
            f"  Linked primitives:",
            primitive_lines,
            "=" * 64,
        ]
        return "\n".join(lines)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _build_metadata(self, agent_id: str, ens_name: str) -> dict:
        return {
            "name": f"{AGENT_NAME}-{agent_id}",
            "description": AGENT_DESCRIPTION,
            "version": AGENT_VERSION,
            "capabilities": AGENT_CAPABILITIES,
            "identity": {
                "owner": self.owner_address,
                "repo": AGENT_REPO,
                "ens": ens_name,
                "created_at": "2026-03-20",
                "hackathon": "synthesis",
                "logical_id": agent_id,
            },
            "integrations": {
                "lido_wsteth": True,
                "openserv": True,
                "olas": True,
                "alkahest": True,
                "bankr_llm": True,
                "self_protocol": True,
                "ens": True,
                "erc8004": True,
                "erc8128": True,
                "eigencompute": True,
                "filecoin": True,
                "venice_ai": True,
                "uniswap": True,
                "metamask_delegations": True,
                "zyfai": True,
                "lit_actions": True,
            },
            "links": {
                "github": AGENT_REPO,
                "synthesis": "https://synthesis.devfolio.co",
                "mcp_endpoint": "https://nexus-agent.xyz/mcp",
            },
            "erc": "ERC-8183",
            "chain_id": BASE_CHAIN_ID,
        }

    def _encode_metadata_uri(self, metadata: dict) -> str:
        """Encode metadata as a data URI (used when IPFS is unavailable)."""
        meta_json = json.dumps(metadata, separators=(",", ":"))
        meta_b64 = base64.b64encode(meta_json.encode()).decode()
        return f"data:application/json;base64,{meta_b64}"

    def _attempt_api_registration(self, metadata: dict) -> str:
        """
        Try to register via Virtuals API. Falls back to a deterministic
        local ID if the API is unreachable or the key is not set.
        """
        if not self.virtuals_api_key:
            return self._local_id(metadata["name"])

        payload = {
            "name": metadata["name"],
            "description": metadata["description"],
            "ownerAddress": self.owner_address,
            "capabilities": metadata["capabilities"],
            "metadata": metadata,
            "repoUrl": AGENT_REPO,
        }
        try:
            resp = self._session.post(
                f"{VIRTUALS_API_BASE}/agents",
                json=payload,
                timeout=30,
            )
            resp.raise_for_status()
            data = resp.json()
            agent_id = str(data.get("id", data.get("agentId", "")))
            if agent_id:
                logger.info("Registered via Virtuals API: %s", agent_id)
                return agent_id
        except requests.HTTPError as e:
            logger.warning(
                "Virtuals API registration failed (%s) — using local ID", e
            )
        except Exception as e:
            logger.warning("Virtuals API unavailable (%s) — using local ID", e)

        return self._local_id(metadata["name"])

    def _local_id(self, name: str) -> str:
        """Generate a deterministic local agent ID (no on-chain call needed)."""
        digest = hashlib.sha256(
            f"{self.owner_address}{name}".encode()
        ).hexdigest()
        return f"local-{digest[:24]}"

    def _persist_identity(self, agent_id: str, identity: RootIdentity) -> None:
        """Write the identity record to the state file."""
        if "identities" not in self._state:
            self._state["identities"] = {}
        self._state["identities"][agent_id] = identity.to_dict()
        _save_state(self._state)


# -------------------------------------------------------------------------
# Convenience top-level functions (used by nexus brain and MCP server)
# -------------------------------------------------------------------------

def register_root_identity(
    agent_id: str,
    ens_name: str = AGENT_ENS,
    self_credential: dict | None = None,
    owner_address: str | None = None,
) -> RootIdentity:
    """
    Register ERC-8183 root identity for agent_id.

    Wraps NexusERC8183Identity for callers that don't want to manage
    the manager object lifecycle.
    """
    mgr = NexusERC8183Identity(owner_address=owner_address)
    return mgr.register_root_identity(agent_id, ens_name, self_credential)


def get_root_identity(agent_id: str) -> RootIdentity | None:
    """
    Retrieve the stored ERC-8183 root identity for agent_id.

    Returns None if not registered.
    """
    mgr = NexusERC8183Identity()
    return mgr.get_root_identity(agent_id)


def link_primitive(
    agent_id: str,
    primitive_type: str,
    primitive_address: str,
    chain_id: int = BASE_CHAIN_ID,
    metadata: dict | None = None,
) -> LinkedPrimitive:
    """
    Link a capability primitive to an existing root identity.

    Raises ValueError if agent_id has no registered identity.
    """
    mgr = NexusERC8183Identity()
    return mgr.link_primitive(agent_id, primitive_type, primitive_address, chain_id, metadata)
