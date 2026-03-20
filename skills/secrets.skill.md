# Secrets & ZK Skill

## Identity
nexus-secrets-mcp handles private computation and zero-knowledge proofs. It seals JavaScript logic in Lit Protocol TEE nodes (tamper-proof execution), runs sealed actions with verifiable outputs, and generates/verifies Noir ZK proofs for use in NexusArbiter escrow verification.

## When To Use
- Seal sensitive business logic (scoring algorithms, private pricing) in a TEE
- Generate a ZK proof that an API call was made with valid credentials
- Verify a proof before releasing an escrow payment
- Prove account balance > threshold without revealing the balance

## How To Call

```
seal_function(js_code="const result = fetch(...)", description="private scoring logic")
run_action(action_cid="Qm...", params={"threshold": 80})
generate_proof(circuit_name="api_proof", private_inputs={"api_key_hash": "0x..."}, public_inputs={"endpoint": "0x...", "result_hash": "0x..."})
verify_proof(circuit_name="api_proof", proof="0x...", public_inputs=["0x..."])
```

## Mental Model

**Lit Actions:** JavaScript code encrypted and stored on IPFS, executed only inside Lit Protocol's TEE nodes. No one (not even Lit) can read the code or intercept results. Outputs are signed by the Lit network.

**Noir ZK circuits:**
- `api_proof`: Proves "I called API endpoint X with valid credentials and got result Y" — without revealing the API key. Used by NexusArbiter to release escrow.
- `balance_proof`: Proves "My balance > threshold" without revealing the actual balance.
- `identity_proof`: Proves knowledge of an identity preimage (for ERC-8004 onboarding).

**Proof flow for escrow:**
1. nexus-prover calls an API (private)
2. `generate_proof(circuit="api_proof", ...)` → proof bytes
3. `submit_delivery(escrow_id, proof_type="noir", proof_data=proof)` (via coordinate-mcp)
4. NexusArbiter.sol verifies proof on-chain → releases payment

## Guardrails
- NEVER put private keys in `js_code` passed to seal_function — use Lit's encryption primitives instead
- Always verify_proof before calling submit_delivery on an escrow
- ZK proofs are single-use for escrow — don't reuse the same proof bytes
