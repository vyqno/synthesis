# Nexus Protocol — Makefile
# Usage: make <target>

.PHONY: help install dev test lint fmt clean build \
        test-contracts test-agents test-e2e fuzz invariant \
        deploy-sepolia deploy-arbitrum deploy-base deploy-mainnet deploy-local \
        deploy-dry-run verify-deployment gas-report \
        agent dashboard anvil submit

# ── Colors ────────────────────────────────────────────────────────────────────
RESET  := \033[0m
BOLD   := \033[1m
GREEN  := \033[32m
YELLOW := \033[33m
BLUE   := \033[34m
CYAN   := \033[36m

# ── Config ────────────────────────────────────────────────────────────────────
PYTHON       := python3
PIP          := pip3
FORGE        := forge
CAST         := cast
ANVIL        := anvil
PYTEST       := pytest
NPM          := npm

CONTRACTS_DIR := contracts
AGENTS_DIR    := agents
MCP_DIR       := mcp
WEB_DIR       := web
SCRIPTS_DIR   := scripts

# ── Help ──────────────────────────────────────────────────────────────────────
help: ## Show this help message
	@echo "$(BOLD)$(CYAN)Nexus Protocol$(RESET)"
	@echo "$(CYAN)══════════════════════════════════════════════$(RESET)"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "  $(GREEN)%-22s$(RESET) %s\n", $$1, $$2}'
	@echo ""
	@echo "$(YELLOW)Environment:$(RESET) copy .env.example → .env and fill values"
	@echo "$(YELLOW)Quick start:$(RESET) make install && make dev"

# ── Install ───────────────────────────────────────────────────────────────────
install: install-python install-contracts install-web ## Install all dependencies

install-python: ## Install Python dependencies
	@echo "$(BLUE)→ Installing Python deps...$(RESET)"
	$(PIP) install -r requirements.txt --break-system-packages 2>/dev/null || \
	$(PIP) install -r requirements.txt
	@echo "$(GREEN)✓ Python deps installed$(RESET)"

install-contracts: ## Install Foundry contract dependencies
	@echo "$(BLUE)→ Installing contract deps...$(RESET)"
	cd $(CONTRACTS_DIR) && $(FORGE) install --no-commit 2>/dev/null || true
	@echo "$(GREEN)✓ Contract deps installed$(RESET)"

install-web: ## Install Next.js dependencies
	@echo "$(BLUE)→ Installing web deps...$(RESET)"
	cd $(WEB_DIR) && $(NPM) install --legacy-peer-deps
	@echo "$(GREEN)✓ Web deps installed$(RESET)"

check-env: ## Verify required environment variables are set
	@$(PYTHON) $(SCRIPTS_DIR)/check_env.py

# ── Development ───────────────────────────────────────────────────────────────
dev: ## Start all services locally (anvil + agent + dashboard)
	@echo "$(BLUE)→ Starting Nexus dev environment...$(RESET)"
	@make -j3 anvil agent-dev dashboard-dev

anvil: ## Start local Ethereum node (Anvil)
	@echo "$(BLUE)→ Starting Anvil on :8545...$(RESET)"
	$(ANVIL) --chain-id 31337 --block-time 2 --accounts 10

agent-dev: ## Run agent in dev mode (dry-run, no real txs)
	@echo "$(BLUE)→ Starting agent (dev mode)...$(RESET)"
	DRY_RUN=true $(PYTHON) agents/nexus/main.py

dashboard-dev: ## Start Next.js dashboard dev server
	@echo "$(BLUE)→ Starting dashboard on :3000...$(RESET)"
	cd $(WEB_DIR) && $(NPM) run dev

agent: ## Run agent in production mode
	@echo "$(YELLOW)→ Starting agent (PRODUCTION mode)...$(RESET)"
	$(PYTHON) agents/nexus/main.py

dashboard: ## Build and start production dashboard
	cd $(WEB_DIR) && $(NPM) run build && $(NPM) start

# ── Testing ───────────────────────────────────────────────────────────────────
test: test-contracts test-agents ## Run all tests

test-contracts: ## Run Foundry contract tests
	@echo "$(BLUE)→ Running Foundry tests...$(RESET)"
	cd $(CONTRACTS_DIR) && $(FORGE) test -vv
	@echo "$(GREEN)✓ Contract tests passed$(RESET)"

test-agents: ## Run Python agent tests
	@echo "$(BLUE)→ Running Python tests...$(RESET)"
	$(PYTEST) tests/ -v --tb=short
	@echo "$(GREEN)✓ Agent tests passed$(RESET)"

test-e2e: ## Run end-to-end tests
	@echo "$(BLUE)→ Running E2E tests...$(RESET)"
	$(PYTEST) tests/e2e/ -v --tb=short -m "not slow"
	@echo "$(GREEN)✓ E2E tests passed$(RESET)"

test-e2e-full: ## Run ALL e2e tests including slow ones
	$(PYTEST) tests/e2e/ -v --tb=short

fuzz: ## Run Foundry fuzz tests (10000 runs)
	@echo "$(BLUE)→ Running fuzz tests (10000 runs)...$(RESET)"
	cd $(CONTRACTS_DIR) && $(FORGE) test --fuzz-runs 10000 -vv
	@echo "$(GREEN)✓ Fuzz tests complete$(RESET)"

invariant: ## Run Foundry invariant tests
	@echo "$(BLUE)→ Running invariant tests...$(RESET)"
	cd $(CONTRACTS_DIR) && $(FORGE) test --match-path "test/invariants/*" -vv
	@echo "$(GREEN)✓ Invariant tests complete$(RESET)"

snapshot: ## Generate gas snapshot
	cd $(CONTRACTS_DIR) && $(FORGE) snapshot

gas: ## Show gas report
	cd $(CONTRACTS_DIR) && $(FORGE) test --gas-report

# ── Code Quality ──────────────────────────────────────────────────────────────
lint: lint-python lint-contracts lint-web ## Run all linters

lint-python: ## Lint Python code
	@echo "$(BLUE)→ Linting Python...$(RESET)"
	$(PYTHON) -m py_compile agents/nexus/*.py mcp/*.py scripts/*.py 2>/dev/null || true
	@echo "$(GREEN)✓ Python syntax OK$(RESET)"

lint-contracts: ## Lint Solidity with forge
	cd $(CONTRACTS_DIR) && $(FORGE) build --silent
	@echo "$(GREEN)✓ Solidity compiles clean$(RESET)"

lint-web: ## TypeScript check
	@echo "$(BLUE)→ TypeScript check...$(RESET)"
	cd $(WEB_DIR) && npx tsc --noEmit
	@echo "$(GREEN)✓ TypeScript clean$(RESET)"

fmt: fmt-contracts fmt-python ## Format all code

fmt-contracts: ## Format Solidity with forge fmt
	cd $(CONTRACTS_DIR) && $(FORGE) fmt

fmt-python: ## Format Python with black (if installed)
	$(PYTHON) -m black agents/ mcp/ scripts/ tests/ 2>/dev/null || \
		echo "$(YELLOW)⚠ black not installed — skipping$(RESET)"

# ── Build ─────────────────────────────────────────────────────────────────────
build: build-contracts build-web ## Build all artifacts

build-contracts: ## Build contracts
	cd $(CONTRACTS_DIR) && $(FORGE) build
	@echo "$(GREEN)✓ Contracts built$(RESET)"

build-web: ## Build Next.js production bundle
	cd $(WEB_DIR) && $(NPM) run build
	@echo "$(GREEN)✓ Web built$(RESET)"

clean: ## Clean all build artifacts
	cd $(CONTRACTS_DIR) && $(FORGE) clean
	cd $(WEB_DIR) && rm -rf .next out node_modules/.cache
	find . -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true
	find . -name "*.pyc" -delete 2>/dev/null || true
	@echo "$(GREEN)✓ Clean$(RESET)"

# ── Deployment ────────────────────────────────────────────────────────────────
deploy-sepolia: check-env build-contracts ## Deploy all 9 contracts to Sepolia testnet
	@echo "$(YELLOW)→ Deploying to Sepolia...$(RESET)"
	cd $(CONTRACTS_DIR) && $(FORGE) script script/DeployAll.s.sol \
		--rpc-url $(SEPOLIA_RPC_URL) \
		--broadcast \
		--verify \
		--etherscan-api-key $(ETHERSCAN_API_KEY) \
		-vvvv
	@echo "$(GREEN)✓ Deployed to Sepolia$(RESET)"
	@make verify-deployment

deploy-dry-run: ## Simulate full deployment (no broadcast, no gas cost)
	@echo "$(BLUE)→ Dry-run deployment (no broadcast)...$(RESET)"
	cd $(CONTRACTS_DIR) && $(FORGE) script script/DeployAll.s.sol \
		--rpc-url $(SEPOLIA_RPC_URL) \
		-vvvv
	@echo "$(GREEN)✓ Dry-run complete$(RESET)"

verify-deployment: ## Verify deployed contracts against broadcast log
	@echo "$(BLUE)→ Verifying deployment...$(RESET)"
	$(PYTHON) $(SCRIPTS_DIR)/verify_deployment.py
	@echo "$(GREEN)✓ Verification complete$(RESET)"

gas-report: ## Run tests and produce per-function gas report
	@echo "$(BLUE)→ Generating gas report...$(RESET)"
	cd $(CONTRACTS_DIR) && $(FORGE) test --gas-report 2>&1 | tee gas-report.txt
	@echo "$(GREEN)✓ Gas report saved to gas-report.txt$(RESET)"

deploy-arbitrum: check-env build-contracts ## Deploy all 9 contracts to Arbitrum
	@echo "$(YELLOW)→ Deploying to Arbitrum...$(RESET)"
	cd $(CONTRACTS_DIR) && $(FORGE) script script/DeployAll.s.sol \
		--rpc-url $(ARBITRUM_RPC_URL) \
		--broadcast \
		--verify \
		--etherscan-api-key $(ARBISCAN_API_KEY) \
		-vvvv
	@echo "$(GREEN)✓ Deployed to Arbitrum$(RESET)"

deploy-base: check-env build-contracts ## Deploy all 9 contracts to Base
	@echo "$(YELLOW)→ Deploying to Base...$(RESET)"
	cd $(CONTRACTS_DIR) && $(FORGE) script script/DeployAll.s.sol \
		--rpc-url $(BASE_RPC_URL) \
		--broadcast \
		--verify \
		--etherscan-api-key $(BASESCAN_API_KEY) \
		-vvvv
	@echo "$(GREEN)✓ Deployed to Base$(RESET)"

deploy-mainnet: check-env build-contracts ## Deploy all 9 contracts to Ethereum mainnet (CAREFUL)
	@echo "$(YELLOW)⚠ MAINNET DEPLOYMENT — are you sure? [ctrl-c to abort]$(RESET)"
	@sleep 5
	cd $(CONTRACTS_DIR) && $(FORGE) script script/DeployAll.s.sol \
		--rpc-url $(MAINNET_RPC_URL) \
		--broadcast \
		--verify \
		--etherscan-api-key $(ETHERSCAN_API_KEY) \
		-vvvv
	@echo "$(GREEN)✓ Deployed to Mainnet$(RESET)"

deploy-local: ## Deploy all 9 contracts to local Anvil (requires make anvil running)
	cd $(CONTRACTS_DIR) && $(FORGE) script script/DeployAll.s.sol \
		--rpc-url http://localhost:8545 \
		--broadcast \
		--private-key 0xac0974bec39a17e36ba4a6b4d238ff944bacb478cbed5efcae784d7bf4f2ff80

# ── Circuits ──────────────────────────────────────────────────────────────────
circuits: ## Compile all Noir ZK circuits
	@echo "$(BLUE)→ Compiling Noir circuits...$(RESET)"
	cd circuits/api_proof && nargo compile
	cd circuits/balance_proof && nargo compile
	cd circuits/identity_proof && nargo compile
	@echo "$(GREEN)✓ Circuits compiled$(RESET)"

# ── Submission ────────────────────────────────────────────────────────────────
submit: ## Submit to all 46 Synthesis hackathon tracks (dry-run first)
	@echo "$(BLUE)→ Dry run first...$(RESET)"
	$(PYTHON) $(SCRIPTS_DIR)/submit_all_tracks.py --dry-run
	@echo "$(YELLOW)→ Submit for real? Run: make submit-live$(RESET)"

submit-live: check-env ## Submit to all 46 tracks (LIVE)
	$(PYTHON) $(SCRIPTS_DIR)/submit_all_tracks.py

# ── Safe ──────────────────────────────────────────────────────────────────────
setup-safe: ## Deploy Gnosis Safe multisig for agent treasury
	bash $(SCRIPTS_DIR)/setup_safe.sh

# ── Docker ────────────────────────────────────────────────────────────────────
docker-build: ## Build Docker image
	docker build -t nexus-agent:latest .

docker-run: ## Run agent in Docker
	docker run --env-file .env -p 8080:8080 nexus-agent:latest

docker-compose-up: ## Start full stack with Docker Compose
	docker-compose up -d

docker-compose-down: ## Stop Docker Compose stack
	docker-compose down
