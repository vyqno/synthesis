# Nexus EigenCompute Architecture

## Overview

Nexus runs as a Docker container on EigenCompute's TEE infrastructure. The container executes the full autonomous agent loop — checking treasury yield, making allocation decisions via Venice AI, dispatching sub-agents, and logging results to Filecoin.

## Container Architecture

```
┌─────────────────────────────────────────────┐
│           EigenCompute TEE Node              │
│                                              │
│  ┌─────────────────────────────────────┐    │
│  │         Nexus Container              │    │
│  │                                      │    │
│  │  ┌──────────┐   ┌────────────────┐  │    │
│  │  │ Health   │   │  Nexus Brain   │  │    │
│  │  │ Server   │   │  (main.py)     │  │    │
│  │  │ :8080    │   │                │  │    │
│  │  └──────────┘   │ Venice API ────┼──┼────┼──► private reasoning
│  │                 │ Bankr API  ────┼──┼────┼──► inference billing
│  │                 │ Treasury   ────┼──┼────┼──► wstETH yield
│  │                 │ Filecoin   ────┼──┼────┼──► state persistence
│  │                 └────────────────┘  │    │
│  └─────────────────────────────────────┘    │
└─────────────────────────────────────────────┘
```

## Why EigenCompute

EigenCompute provides verifiable off-chain execution in a TEE. When Nexus executes the yield→inference loop:
1. The computation is verifiable — anyone can confirm the Docker image hash
2. The results are tamper-proof — TEE prevents manipulation
3. The agent_log.json output is cryptographically attested

## Environment Variables

Required: PRIVATE_KEY, BANKR_API_KEY, VENICE_API_KEY, SEPOLIA_RPC_URL, FILECOIN_TOKEN

Optional: VENICE_MODEL (default: "venice-uncensored") — override the Venice model used for private reasoning

## Running Locally

```bash
docker build -t nexus .
docker run -e PRIVATE_KEY=0x... -e VENICE_API_KEY=... nexus
# Health: curl http://localhost:8080/health
```
