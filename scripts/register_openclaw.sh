#!/bin/bash
# Register Nexus with Bankr OpenClaw for skill discovery
# OpenClaw covers: Bankr OpenClaw Best Use ($500)

SKILL_URL="https://raw.githubusercontent.com/vyqno/synthesis/main/nexus.skill.md"
BANKR_API_KEY="${BANKR_API_KEY:-}"

if [ -z "$BANKR_API_KEY" ]; then
    echo "BANKR_API_KEY not set — skipping OpenClaw registration"
    echo "Manual registration: POST skill URL to Bankr OpenClaw API"
    exit 0
fi

echo "Registering Nexus with OpenClaw..."
curl -s -X POST "https://api.bankr.bot/v1/openclaw/register" \
  -H "Authorization: Bearer $BANKR_API_KEY" \
  -H "Content-Type: application/json" \
  -d "{\"skill_url\": \"$SKILL_URL\", \"name\": \"nexus\", \"description\": \"Self-funding autonomous agent infrastructure\"}" \
| jq .

echo "OpenClaw registration complete"
