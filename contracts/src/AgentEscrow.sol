// SPDX-License-Identifier: MIT
pragma solidity ^0.8.28;

/**
 * @title AgentEscrow
 * @notice ZK-verified escrow for AI agent jobs. Trustless AI labor market.
 *
 * Flow:
 *   1. Hirer creates job: createJob(agent, deliverableHash, deadlineDuration, desc)
 *      → 2% of payment goes to insurance pool, remainder locked for agent.
 *   2. Agent completes work, generates Noir ZK proof of delivery.
 *   3. Agent calls: claimPayment(jobId, noirProof, publicInputs)
 *      → NexusArbiter verifies proof onchain.
 *   4. Payment releases to agent (minus 10% if delivered late).
 *
 * Insurance pool absorbs:
 *   - 10% late-delivery penalty from agent
 *   - 10% of un-delivered job value when hirer cancels after grace period
 *   - Arbiter-disputed shortfalls
 *
 * This is the missing primitive for a trustless AI labor market:
 * like Upwork but fully onchain — no platform, no middleman, ZK-verified.
 *
 * Mock arbiter mode: when arbiter == address(0) any non-empty proof passes.
 */

interface INexusArbiter {
    function verifyDelivery(
        bytes32 escrowId,
        bytes calldata noirProof,
        bytes32[] calldata publicInputs
    ) external returns (bool);
}

contract AgentEscrow {
    // -----------------------------------------------------------------------
    // Constants
    // -----------------------------------------------------------------------

    uint256 public constant INSURANCE_FEE_BPS    = 200;  // 2% of job value
    uint256 public constant DEADLINE_PENALTY_BPS = 1000; // 10% penalty for late delivery
    uint256 public constant CANCEL_REFUND_BPS    = 9000; // hirer gets 90% on expired cancel
    uint256 public constant BPS_BASE             = 10000;

    uint256 public constant MIN_DEADLINE = 1 hours;
    uint256 public constant MAX_DEADLINE = 30 days;
    uint256 public constant CANCEL_GRACE = 1 days; // extra grace after deadline before cancel

    // -----------------------------------------------------------------------
    // Types
    // -----------------------------------------------------------------------

    enum JobStatus { Open, Disputed, Cancelled, Paid }

    struct Job {
        address hirer;
        address agent;
        uint256 payment;         // ETH locked for agent (after insurance deducted)
        uint256 insuranceFee;    // ETH taken for insurance pool
        bytes32 deliverableHash; // keccak256 of expected deliverable specification
        uint256 deadline;        // unix timestamp for delivery
        JobStatus status;
        bytes32 proofHash;       // set when agent submits valid proof
        string  jobDescription;
    }

    // -----------------------------------------------------------------------
    // State
    // -----------------------------------------------------------------------

    address public owner;
    INexusArbiter public arbiter;

    uint256 public insurancePool;

    mapping(bytes32 => Job) public jobs;
    bytes32[] public jobIds;

    // Agent performance tracking (feeds into NexusReputationStaking)
    mapping(address => uint256) public agentJobsCompleted;
    mapping(address => uint256) public agentJobsFailed;
    mapping(address => uint256) public agentTotalEarned;

    bool private _locked;

    // -----------------------------------------------------------------------
    // Events
    // -----------------------------------------------------------------------

    event JobCreated(
        bytes32 indexed jobId,
        address indexed hirer,
        address indexed agent,
        uint256 payment,
        uint256 deadline
    );
    event JobCompleted(bytes32 indexed jobId, address indexed agent, uint256 payout);
    event JobDisputed(bytes32 indexed jobId, address indexed disputer);
    event JobCancelled(bytes32 indexed jobId, uint256 refund);
    event DisputeResolved(bytes32 indexed jobId, address recipient, uint256 amount);
    event InsuranceFunded(uint256 amount);

    // -----------------------------------------------------------------------
    // Modifiers
    // -----------------------------------------------------------------------

    modifier onlyOwner() {
        require(msg.sender == owner, "Not owner");
        _;
    }

    modifier nonReentrant() {
        require(!_locked, "Reentrant call");
        _locked = true;
        _;
        _locked = false;
    }

    // -----------------------------------------------------------------------
    // Constructor
    // -----------------------------------------------------------------------

    constructor(address _arbiter) {
        owner   = msg.sender;
        arbiter = INexusArbiter(_arbiter);
    }

    // -----------------------------------------------------------------------
    // Job lifecycle
    // -----------------------------------------------------------------------

    /**
     * @notice Hirer creates a job and locks ETH payment.
     * @param agent            Address of the agent expected to complete the job.
     * @param deliverableHash  keccak256 of the deliverable specification / commitment.
     * @param deadlineDuration Seconds from now until the delivery deadline.
     * @param jobDescription   Human-readable job description (stored on-chain).
     * @return jobId           Unique identifier for this job.
     */
    function createJob(
        address agent,
        bytes32 deliverableHash,
        uint256 deadlineDuration,
        string calldata jobDescription
    ) external payable nonReentrant returns (bytes32 jobId) {
        require(msg.value > 0, "No payment attached");
        require(agent != address(0), "Zero agent address");
        require(
            deadlineDuration >= MIN_DEADLINE && deadlineDuration <= MAX_DEADLINE,
            "Invalid deadline duration"
        );

        uint256 insuranceFee = (msg.value * INSURANCE_FEE_BPS) / BPS_BASE;
        uint256 agentPayment = msg.value - insuranceFee;
        insurancePool += insuranceFee;

        jobId = keccak256(abi.encodePacked(msg.sender, agent, block.timestamp, deliverableHash));

        jobs[jobId] = Job({
            hirer:           msg.sender,
            agent:           agent,
            payment:         agentPayment,
            insuranceFee:    insuranceFee,
            deliverableHash: deliverableHash,
            deadline:        block.timestamp + deadlineDuration,
            status:          JobStatus.Open,
            proofHash:       bytes32(0),
            jobDescription:  jobDescription
        });

        jobIds.push(jobId);
        emit JobCreated(jobId, msg.sender, agent, agentPayment, block.timestamp + deadlineDuration);
    }

    /**
     * @notice Agent submits a ZK proof of delivery to claim payment.
     *         Proof is verified by the NexusArbiter contract (or bypassed in mock mode).
     *         A 10% penalty applies to deliveries made after the deadline.
     * @param jobId        The job being completed.
     * @param noirProof    Serialised Noir proof bytes.
     * @param publicInputs Public inputs to the circuit.
     */
    function claimPayment(
        bytes32 jobId,
        bytes calldata noirProof,
        bytes32[] calldata publicInputs
    ) external nonReentrant {
        Job storage job = jobs[jobId];
        require(job.status == JobStatus.Open, "Job not open");
        require(msg.sender == job.agent, "Not the assigned agent");

        // Verify ZK proof
        bool verified;
        if (address(arbiter) != address(0)) {
            verified = arbiter.verifyDelivery(jobId, noirProof, publicInputs);
        } else {
            // Mock mode: any non-empty proof passes
            verified = noirProof.length > 0;
        }
        require(verified, "Proof verification failed");

        uint256 payout = job.payment;

        // Late delivery penalty
        if (block.timestamp > job.deadline) {
            uint256 penalty = (payout * DEADLINE_PENALTY_BPS) / BPS_BASE;
            payout         -= penalty;
            insurancePool  += penalty;
        }

        job.status    = JobStatus.Paid;
        job.proofHash = keccak256(noirProof);

        agentJobsCompleted[msg.sender]++;
        agentTotalEarned[msg.sender] += payout;

        (bool ok,) = msg.sender.call{value: payout}("");
        require(ok, "Payment transfer failed");

        emit JobCompleted(jobId, msg.sender, payout);
    }

    /**
     * @notice Hirer opens a dispute if they believe delivery was fraudulent/incomplete.
     *         Pauses the job; owner resolves via resolveDispute().
     */
    function disputeJob(bytes32 jobId) external {
        Job storage job = jobs[jobId];
        require(msg.sender == job.hirer, "Not the hirer");
        require(job.status == JobStatus.Open, "Job not open");
        job.status = JobStatus.Disputed;
        emit JobDisputed(jobId, msg.sender);
    }

    /**
     * @notice Cancel a job that has passed its deadline without delivery.
     *         Hirer receives 90% refund; 10% goes to insurance pool.
     *         Requires CANCEL_GRACE (1 day) extra buffer past deadline.
     */
    function cancelExpired(bytes32 jobId) external nonReentrant {
        Job storage job = jobs[jobId];
        require(job.status == JobStatus.Open, "Job not open");
        require(block.timestamp > job.deadline + CANCEL_GRACE, "Not yet expired");

        job.status = JobStatus.Cancelled;
        agentJobsFailed[job.agent]++;

        uint256 refund    = (job.payment * CANCEL_REFUND_BPS) / BPS_BASE;
        uint256 toInsure  = job.payment - refund;
        insurancePool    += toInsure;

        (bool ok,) = job.hirer.call{value: refund}("");
        require(ok, "Refund failed");

        emit JobCancelled(jobId, refund);
    }

    /**
     * @notice Owner resolves a disputed job.
     *         Funds go to the winning party; insurance covers any shortfall.
     * @param jobId     The disputed job.
     * @param agentWins If true, agent is paid; otherwise hirer is refunded.
     */
    function resolveDispute(bytes32 jobId, bool agentWins) external onlyOwner nonReentrant {
        Job storage job = jobs[jobId];
        require(job.status == JobStatus.Disputed, "Not disputed");
        job.status = JobStatus.Paid;

        address recipient = agentWins ? job.agent : job.hirer;
        uint256 amount    = job.payment;

        // Safety: if contract balance is insufficient, draw from insurance pool
        uint256 available = address(this).balance;
        if (amount > available) {
            uint256 shortfall = amount - available;
            require(shortfall <= insurancePool, "Insurance insufficient");
            insurancePool -= shortfall;
        }

        if (agentWins) {
            agentJobsCompleted[job.agent]++;
            agentTotalEarned[job.agent] += amount;
        } else {
            agentJobsFailed[job.agent]++;
        }

        (bool ok,) = recipient.call{value: amount}("");
        require(ok, "Resolution transfer failed");

        emit DisputeResolved(jobId, recipient, amount);
    }

    // -----------------------------------------------------------------------
    // View helpers
    // -----------------------------------------------------------------------

    function getJob(bytes32 jobId) external view returns (Job memory) {
        return jobs[jobId];
    }

    function getJobCount() external view returns (uint256) {
        return jobIds.length;
    }

    function getAgentStats(address agent)
        external
        view
        returns (uint256 completed, uint256 failed, uint256 totalEarned)
    {
        return (agentJobsCompleted[agent], agentJobsFailed[agent], agentTotalEarned[agent]);
    }

    // -----------------------------------------------------------------------
    // Admin
    // -----------------------------------------------------------------------

    /// @notice Update the NexusArbiter contract used to verify ZK delivery proofs.
    function setArbiter(address _arbiter) external onlyOwner {
        arbiter = INexusArbiter(_arbiter);
    }

    /// @notice Accept direct ETH to top up the insurance pool.
    receive() external payable {
        insurancePool += msg.value;
        emit InsuranceFunded(msg.value);
    }
}
