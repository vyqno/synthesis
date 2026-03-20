"""
Submit Nexus to all 46 Synthesis hackathon tracks.

API Key: sk-synth-f2c6c01886727a42a9d59356234fedf07a257ad463ec6eaf
Team ID: 3786a8ddd43847fbae8a7d015769ff92
Base URL: https://synthesis.devfolio.co
"""
import httpx
import json
import os
from pathlib import Path

API_KEY = "sk-synth-f2c6c01886727a42a9d59356234fedf07a257ad463ec6eaf"
TEAM_ID = "3786a8ddd43847fbae8a7d015769ff92"
BASE_URL = "https://synthesis.devfolio.co"

HEADERS = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json",
}

def get_catalog() -> list:
    """Fetch all track UUIDs from the Synthesis catalog."""
    with httpx.Client(timeout=30) as client:
        resp = client.get(f"{BASE_URL}/catalog", headers=HEADERS)
        resp.raise_for_status()
        return resp.json()

def create_project(track_uuids: list) -> dict:
    """Create the Nexus project submission."""
    payload = {
        "teamUUID": TEAM_ID,
        "name": "Nexus",
        "description": (
            "An autonomous agent that earns its own compute budget from DeFi yield "
            "and runs an entire economy of specialized sub-agents — without a single human in the loop. "
            "Exposes all capabilities as MCP servers, OpenClaw skills, and skills.md files "
            "covering all 46 Synthesis tracks."
        ),
        "repoURL": "https://github.com/vyqno/synthesis",
        "trackUUIDs": track_uuids,
        "submissionMetadata": {
            "demoURL": "https://nexus-agent.xyz",
            "skillFileURL": "https://raw.githubusercontent.com/vyqno/synthesis/main/nexus.skill.md",
            "agentManifestURL": "https://raw.githubusercontent.com/vyqno/synthesis/main/agent.json",
            "mcpEndpoint": "https://nexus-agent.xyz/mcp",
        },
    }
    with httpx.Client(timeout=60) as client:
        resp = client.post(f"{BASE_URL}/projects", headers=HEADERS, json=payload)
        resp.raise_for_status()
        return resp.json()

def publish_project(project_uuid: str) -> dict:
    """Publish the project."""
    with httpx.Client(timeout=30) as client:
        resp = client.post(f"{BASE_URL}/projects/{project_uuid}/publish", headers=HEADERS)
        resp.raise_for_status()
        return resp.json()

if __name__ == "__main__":
    print("Fetching Synthesis track catalog...")
    try:
        catalog = get_catalog()
        track_uuids = [t["uuid"] for t in catalog] if isinstance(catalog, list) else []
        print(f"Found {len(track_uuids)} tracks")

        print("Creating project submission...")
        project = create_project(track_uuids)
        project_uuid = project.get("uuid", "")
        print(f"Project created: {project_uuid}")

        print("Publishing project...")
        result = publish_project(project_uuid)
        print(f"Published: {result}")

        # Save to STATUS.md
        print(f"\n✓ Submission complete. Project UUID: {project_uuid}")

    except Exception as e:
        print(f"Submission error: {e}")
        print("Manual submission: visit https://synthesis.devfolio.co")
