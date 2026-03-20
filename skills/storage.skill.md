# Agent Storage Skill

## Identity
nexus-storage-mcp handles all persistent storage operations for the Nexus ecosystem: uploading agent data to Filecoin Onchain Cloud for permanent content-addressed retrieval, maintaining a structured agent action log across sessions, and querying account balance/spend metrics.

## When To Use
- Persist agent outputs, decisions, or artefacts beyond the current session
- Record every significant action for auditability (regulatory, debugging, cross-agent trust)
- Retrieve a previously stored payload by its CID
- Check how much Filecoin storage budget remains before a large upload
- Reconstruct an agent's last known state after a restart

## How To Call

```
store(data_json='{"result": 42}', label="my-label")
# → {cid, label, size_bytes, stored: true}

retrieve(cid="bafk...")
# → {cid, data}

log_action(agent_id="nexus", action="swap", result="ok", metadata={"tx": "0x..."})
# → {cid, logged: true, entry_count}

get_agent_state(agent_id="nexus")
# → {agent_id, latest_state, cid, updated_at}

list_logs(agent_id="nexus", limit=20)
# → {agent_id, entries, total_for_agent}

get_storage_balance()
# → {balance_usd, spend_rate_per_day, token_configured}
```

## Mental Model

**CID format:** Content Identifier — a hash of the stored bytes. `store()` returns a real CID when `FILECOIN_TOKEN` is set; without it, a deterministic demo CID is generated as `bafk` + first 32 hex chars of `sha256(data_json)`. The same data always produces the same demo CID. CIDs are permanent — once uploaded to Filecoin they cannot be deleted.

**Agent log schema:**
```json
{
  "agent": "nexus",
  "session": "20260320-083000",
  "entries": [
    {"t": "HH:MM:SS", "agent": "nexus", "action": "swap", "result": "ok", "metadata": {}}
  ]
}
```
The log file lives at `agent_log.json` in the repo root. Each `log_action` call appends one entry and also stores that entry on Filecoin, giving every action a permanent CID.

**get_agent_state** scans the log and returns the most recent entry for the requested agent, enabling stateful resumption across sessions.

## Guardrails
- Always call `log_action` after every significant agent operation — the log is the source of truth for audits and cross-agent trust scoring.
- CIDs are permanent. Never store sensitive credentials or private keys via `store()`.
- Check `get_storage_balance()` before bulk uploads; halt if `balance_usd` is below a safe threshold (e.g. $0.10).
- In demo mode (`token_configured: false`), CIDs are local hashes only — they are not retrievable from the Filecoin network.
- `metadata` in `log_action` should be serialisable JSON; avoid embedding large binary blobs.
