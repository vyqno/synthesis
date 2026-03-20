# Agent Coordination Skill

## Identity
nexus-coordinate-mcp is the coordination layer of the Nexus ecosystem. It dispatches tasks to sub-agents via OpenServ, creates intent delegations via MetaMask ERC-7715, manages Alkahest escrow for trustless payment, hires Olas mech agents, and sends A2A messages via ampersend.

## When To Use
- Assign a task to a specialized sub-agent (nexus-trader, nexus-scorer, etc.)
- Create an escrow that releases automatically on ZK proof of delivery
- Hire an Olas mech agent for a one-time task
- Send an agent-to-agent message with embedded payment

## How To Call

```
list_available_agents()                                  # See all sub-agents + pricing
dispatch_task(agent_id="nexus-trader", task_description="swap 0.1 ETH to USDC", budget_eth=0.001)
delegate_task(task="evaluate project X", caveats="budget=$0.10, deadline=1h", expiry_hours=2)
create_escrow(service_description="ZK proof generation", amount_eth=0.005)
submit_delivery(escrow_id="abc123", proof_type="noir", proof_data="0x...")
hire_olas_agent(mech_id="1", request_data="evaluate this public good project: github.com/...")
send_message(to_agent_ens="nexus-trader.eth", content="task complete", payment_usdc=0.10)
```

## Mental Model

**OpenServ:** Multi-agent workflow infrastructure. Tasks are dispatched to registered agents; OpenServ handles routing, retries, and billing.

**MetaMask Delegation (ERC-7715):** Caveated intent delegation. An agent grants another agent permission to act within defined limits (budget, deadline, scope). No private keys shared.

**Alkahest Escrow:** Trustless escrow using ZK proofs as fulfillment conditions. NexusArbiter.sol verifies the Noir proof before releasing payment. No trusted intermediary.

**Olas Mech Marketplace:** Open marketplace for AI agent tasks. "Hire" sends requests; "Monetize" serves requests. 10+ requests as client qualifies for the Hire track.

**ampersend:** Agent-to-agent messaging with embedded x402 micropayments. Any message can carry USDC payment atomically.

## Guardrails
- NEVER dispatch tasks with budget_eth > available yield balance
- Always create_escrow before paying for sub-agent services over $0.05
- submit_delivery only after verifying proof_data is a valid Noir proof hex string
- hire_olas_agent: track cumulative request count — need 10+ for the Hire track
