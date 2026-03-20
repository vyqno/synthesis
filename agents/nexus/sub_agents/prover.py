"""
nexus-prover — Noir ZK proof generator.

Strategy:
- Generates ZK proofs via nargo CLI (subprocess)
- Caches proofs for 30 minutes to avoid redundant computation
- Optionally seals proofs with Lit Protocol for access control

Env vars:
    NARGO_PATH       — Path to nargo binary (default: "nargo")
    LIT_API_KEY      — Lit Protocol API key for proof sealing
"""
from __future__ import annotations

import hashlib
import json
import os
import time
from typing import Any

from agents.nexus.sub_agents.base import SubAgent

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

CACHE_TTL_SECS = 1800  # 30 minutes


class NexusProver(SubAgent):
    """
    ZK proof generator using Noir/nargo. Caches proofs; optionally seals via Lit.
    """

    agent_id = "nexus-prover"
    description = "Noir ZK proof generator with 30-min proof cache"

    def __init__(self) -> None:
        super().__init__()
        self.nargo_path: str = os.environ.get("NARGO_PATH", "nargo")
        self.lit_api_key: str = os.environ.get("LIT_API_KEY", "")
        self._cache: dict[str, dict[str, Any]] = {}

    # ------------------------------------------------------------------
    # Public interface
    # ------------------------------------------------------------------

    async def run_cycle(self) -> dict[str, Any]:
        """
        Prover is request-driven.
        Cycle returns readiness status and cache stats.
        """
        self._evict_expired_cache()
        result = {
            "status": "ready",
            "cache_size": len(self._cache),
            "nargo": self.nargo_path,
            "lit_configured": bool(self.lit_api_key),
        }
        self.log_action("heartbeat", result)
        return result

    async def generate_proof(
        self,
        circuit: str,
        private_inputs: dict[str, Any],
        public_inputs: dict[str, Any],
    ) -> dict[str, Any]:
        """
        Generate (or retrieve cached) a ZK proof for the given circuit + inputs.

        Args:
            circuit:        Circuit name or path
            private_inputs: Witness values (not included in proof output)
            public_inputs:  Public inputs included in verification

        Returns:
            Proof dict with circuit, proof hex, verification_key, public_inputs.
        """
        key = self._cache_key(circuit, private_inputs, public_inputs)

        # Return cached proof if still fresh
        cached = self._cache.get(key)
        if cached and time.time() - cached["ts"] < CACHE_TTL_SECS:
            return {**cached["proof"], "cached": True}

        # Mock proof — production impl calls: nargo prove --circuit <circuit>
        proof_hex = "0x" + hashlib.sha256(key.encode()).hexdigest() * 4
        vk_hex = "0x" + hashlib.sha256((key + "vk").encode()).hexdigest()

        proof: dict[str, Any] = {
            "circuit": circuit,
            "proof": proof_hex,
            "verification_key": vk_hex,
            "public_inputs": public_inputs,
            "generated_at": int(time.time()),
            "cached": False,
            "note": "mock proof — wire nargo subprocess for production",
        }
        self._cache[key] = {"proof": proof, "ts": time.time()}
        self.log_action("proof_generated", {"circuit": circuit, "public_inputs": public_inputs})
        return proof

    async def verify_proof(
        self,
        circuit: str,
        proof: str,
        public_inputs: dict[str, Any],
    ) -> bool:
        """
        Verify a ZK proof. Mock: checks proof length > 10.
        Production: calls `nargo verify`.
        """
        return len(proof) > 10

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _cache_key(
        self,
        circuit: str,
        private_inputs: dict[str, Any],
        public_inputs: dict[str, Any],
    ) -> str:
        payload = json.dumps(
            {"c": circuit, "priv": private_inputs, "pub": public_inputs},
            sort_keys=True,
        )
        return hashlib.sha256(payload.encode()).hexdigest()

    def _evict_expired_cache(self) -> None:
        """Remove cache entries older than CACHE_TTL_SECS."""
        now = time.time()
        expired = [k for k, v in self._cache.items() if now - v["ts"] >= CACHE_TTL_SECS]
        for k in expired:
            del self._cache[k]
