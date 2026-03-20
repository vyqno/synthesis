# Public Goods Evaluation Skill

## Identity
nexus-goods-mcp is the Octant public goods scoring engine for the Nexus ecosystem. It collects on-chain and GitHub signals, runs private LLM analysis via Venice AI, produces composite trust scores, and issues demo EAS attestations — all within one MCP server.

## When To Use
- A grant round operator needs to rank projects by impact before allocating funds
- An agent needs a Sybil risk score for an Ethereum address before a governance vote
- A curator wants a one-shot recommendation for how to split a budget across multiple projects
- A human reviewer wants a qualitative summary and red-flag list before approving funding
- An attestation needs to be anchored to a scored project on-chain (demo mode)

## How To Call

```
# Full pipeline for a single project
score_public_good(project_url="https://github.com/protocolguild/protocol-guild")
# → {final_score, impact_score, legitimacy_score, sybil_score, recommendation, confidence}

# Collect raw signals only
collect_project_data(project_url_or_address="https://github.com/gitcoinco/passport")
# → {github_stars, commits_90d, contributors, grants_received,
#    on_chain_activity, governance_participation, sybil_score}

# LLM analysis from raw data dict
analyze_project(data={...})
# → {impact_score, legitimacy_score, qualitative_summary, red_flags}

# Sybil check for an address
get_sybil_score(address="0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045")
# → {score, flags}

# Budget allocation across a portfolio
recommend_allocation(
    projects=["https://github.com/OpenZeppelin/openzeppelin-contracts",
              "https://github.com/rotki/rotki"],
    total_budget_usd=50000.0
)
# → [{project, score, amount_usd, rationale}, ...]

# Demo EAS attestation
publish_attestation(project="https://github.com/protocolguild/protocol-guild", score=91.6)
# → {eas_attestation_id, project, score, tx_hash}
```

## Mental Model

**Impact vs Legitimacy vs Sybil — the three pillars:**

| Pillar | What it measures | Key signals |
|---|---|---|
| Impact | How much public good does the project create? | GitHub stars, commits, contributors, on-chain activity |
| Legitimacy | Is the project trustworthy and established? | Grants received, governance participation, low sybil score |
| Sybil resistance | Is the contributor/voter set authentic? | sha256-derived score (0 = safe, 100 = risky) |

**Composite score formula:**
`final_score = impact × 0.40 + legitimacy × 0.35 + (100 − sybil) × 0.25`

**Score bands:**
- 75–100 → FUND (high confidence)
- 50–74  → CONSIDER (medium confidence, request more info)
- 30–49  → CAUTION (low confidence, elevated risk)
- 0–29   → PASS (insufficient evidence)

**Venice API** provides private on-device LLM inference so project data never leaves the operator's trust boundary. When `VENICE_API_KEY` is unset the server returns deterministic demo scores derived from the input metrics.

## Guardrails
- **Use Venice for all LLM scoring** — never send project data to a public LLM endpoint; grant applicant data may be commercially sensitive.
- **Do not publish attestations without human review** — `publish_attestation` is in demo mode only; a human operator must sign off before an on-chain EAS attestation is submitted to mainnet.
- **Sybil scores are signals, not verdicts** — a score of 65 does not automatically disqualify a project; pair with qualitative review and governance context.
- **GitHub data is a proxy, not proof** — forks, star-farming, and commit noise can inflate metrics; use `red_flags` output to surface anomalies.
- **Budget allocations are recommendations** — `recommend_allocation` output requires human approval before funds move; never auto-execute transfers based on this tool alone.
