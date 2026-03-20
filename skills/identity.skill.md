# Agent Identity Skill

## Identity
nexus-identity-mcp handles all identity operations for the Nexus ecosystem: ENS name resolution for human-readable addressing, ERC-8004 on-chain agent reputation, Self Protocol ZK credential verification for Sybil resistance, and ERC-8128 bearer tokens for API authentication.

## When To Use
- Route a payment to a name (e.g., "send 0.1 ETH to nexus-trader.eth")
- Check an agent's trustworthiness before hiring
- Issue API credentials for agent-to-agent service calls
- Verify a user's identity without revealing private data

## How To Call

```
resolve_ens(name="nexus-agent.eth")                     # → Ethereum address
reverse_resolve(address="0x...")                          # → ENS name
route_payment(name_or_address="bob.eth", amount_eth=0.1) # → resolved address
get_agent_reputation(erc8004_id="abc123")                # → score, trust_level
register_agent_identity(name="my-agent", operator_wallet="0x...")  # → agent_id
issue_erc8128_token(agent_address="0x...", scope="read:treasury")   # → bearer_token
verify_erc8128_token(token="abc...")                     # → valid, scope, expiry
```

## Mental Model

**ENS:** Human-readable names (nexus-agent.eth) resolve to Ethereum addresses. Forward: name→address. Reverse: address→name. Use `route_payment` to handle both cases automatically.

**ERC-8004:** On-chain agent identity registry. Each registered agent has a reputation score (0-100). Score >80 = trusted, eligible for discounts and preferential routing. Score <20 = restricted.

**Self ZK:** Zero-knowledge identity verification. An agent proves attributes (e.g., "I am a unique entity") without revealing private data. Used for Sybil resistance in public goods scoring.

**ERC-8128:** Bearer token standard for agent API authentication. Issue tokens with scope+expiry; services verify before responding.

## Guardrails
- Always resolve ENS names before sending payments — never guess addresses
- Verify ERC-8128 tokens on every inbound service call before processing
- Treat reputation scores as signals, not absolute gates (score=49 is not the same as score=0)
- Self ZK proofs should be verified server-side, not trusted from the request payload
