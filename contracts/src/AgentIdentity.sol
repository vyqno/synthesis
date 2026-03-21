// SPDX-License-Identifier: MIT
pragma solidity ^0.8.28;

/**
 * @title AgentIdentity
 * @notice ERC-8004 style on-chain agent identity registry.
 *         Stores agent metadata, links to ERC-8183 root identities,
 *         and maintains a reputation score updatable by authorized updaters.
 */
contract AgentIdentity {
    // -------------------------------------------------------------------------
    // Types
    // -------------------------------------------------------------------------

    struct Identity {
        uint256 agentId;
        string name;
        string ensName;
        address operator;
        uint256 reputationScore; // 0–100
        bytes selfCredential;    // ERC-8183 self-signed credential blob
        bool registered;
    }

    struct Primitive {
        string primitiveType;
        address primitiveAddress;
    }

    // -------------------------------------------------------------------------
    // State
    // -------------------------------------------------------------------------

    uint256 public nextAgentId;

    // agentId => Identity
    mapping(uint256 => Identity) public identities;

    // agentId => list of linked primitives
    mapping(uint256 => Primitive[]) public primitives;

    // operator address => agentId (for reverse lookup)
    mapping(address => uint256) public agentIdByAddress;

    // authorized reputation updaters
    mapping(address => bool) public reputationUpdaters;

    address public owner;

    // -------------------------------------------------------------------------
    // Events
    // -------------------------------------------------------------------------

    event IdentityRegistered(uint256 indexed agentId, string name, address indexed operator);
    event ReputationUpdated(uint256 indexed agentId, uint256 oldScore, uint256 newScore);
    event PrimitiveLinked(uint256 indexed agentId, string primitiveType, address primitiveAddress);
    event UpdaterSet(address indexed updater, bool authorized);

    // -------------------------------------------------------------------------
    // Modifiers
    // -------------------------------------------------------------------------

    modifier onlyOwner() {
        require(msg.sender == owner, "Not owner");
        _;
    }

    modifier onlyUpdater() {
        require(reputationUpdaters[msg.sender] || msg.sender == owner, "Not authorized updater");
        _;
    }

    modifier agentExists(uint256 agentId) {
        require(identities[agentId].registered, "Agent not registered");
        _;
    }

    // -------------------------------------------------------------------------
    // Constructor
    // -------------------------------------------------------------------------

    constructor() {
        owner = msg.sender;
        reputationUpdaters[msg.sender] = true;
        nextAgentId = 1;
    }

    // -------------------------------------------------------------------------
    // Core functions
    // -------------------------------------------------------------------------

    /**
     * @notice Register a new agent identity.
     * @param name         Human-readable agent name.
     * @param ensName      ENS name (e.g. "nexus.eth").
     * @param selfCredential ERC-8183 self-signed credential blob.
     * @return agentId     The newly minted agent ID.
     */
    function registerIdentity(
        string calldata name,
        string calldata ensName,
        bytes calldata selfCredential
    ) external returns (uint256 agentId) {
        require(bytes(name).length > 0, "Name required");
        // One identity per operator address
        require(agentIdByAddress[msg.sender] == 0, "Already registered");

        agentId = nextAgentId++;

        identities[agentId] = Identity({
            agentId: agentId,
            name: name,
            ensName: ensName,
            operator: msg.sender,
            reputationScore: 50, // default neutral score
            selfCredential: selfCredential,
            registered: true
        });

        agentIdByAddress[msg.sender] = agentId;

        emit IdentityRegistered(agentId, name, msg.sender);
    }

    /**
     * @notice Link a primitive (e.g. treasury, arbiter) to an agent identity.
     * @param agentId          The agent to link to.
     * @param primitiveType    Human-readable type string (e.g. "treasury", "arbiter").
     * @param primitiveAddress Contract address of the primitive.
     */
    function linkPrimitive(
        uint256 agentId,
        string calldata primitiveType,
        address primitiveAddress
    ) external agentExists(agentId) {
        require(
            msg.sender == identities[agentId].operator || msg.sender == owner,
            "Not operator"
        );
        require(primitiveAddress != address(0), "Zero address");

        primitives[agentId].push(Primitive({
            primitiveType: primitiveType,
            primitiveAddress: primitiveAddress
        }));

        emit PrimitiveLinked(agentId, primitiveType, primitiveAddress);
    }

    /**
     * @notice Get the reputation score for an agent.
     * @param agentId The agent ID.
     * @return score  Reputation score (0–100).
     */
    function getReputation(uint256 agentId) external view agentExists(agentId) returns (uint256 score) {
        return identities[agentId].reputationScore;
    }

    /**
     * @notice Update the reputation score for an agent.
     *         Only callable by authorized updaters.
     * @param agentId  The agent ID.
     * @param newScore New reputation score (0–100).
     */
    function updateReputation(uint256 agentId, uint256 newScore) external onlyUpdater agentExists(agentId) {
        require(newScore <= 100, "Score exceeds 100");
        uint256 oldScore = identities[agentId].reputationScore;
        identities[agentId].reputationScore = newScore;
        emit ReputationUpdated(agentId, oldScore, newScore);
    }

    /**
     * @notice Reverse lookup: get agent ID by operator address.
     * @param agent Operator address.
     * @return      Agent ID, or 0 if not registered.
     */
    function getAgentIdByAddress(address agent) external view returns (uint256) {
        return agentIdByAddress[agent];
    }

    /**
     * @notice Get full identity metadata.
     */
    function getIdentity(uint256 agentId)
        external
        view
        agentExists(agentId)
        returns (
            string memory name,
            string memory ensName,
            address operator,
            uint256 reputationScore,
            bytes memory selfCredential
        )
    {
        Identity storage id = identities[agentId];
        return (id.name, id.ensName, id.operator, id.reputationScore, id.selfCredential);
    }

    /**
     * @notice Get all primitives linked to an agent.
     */
    function getPrimitives(uint256 agentId)
        external
        view
        agentExists(agentId)
        returns (Primitive[] memory)
    {
        return primitives[agentId];
    }

    // -------------------------------------------------------------------------
    // Admin
    // -------------------------------------------------------------------------

    /// @notice Grant or revoke reputation update privileges for an address.
    function setUpdater(address updater, bool authorized) external onlyOwner {
        reputationUpdaters[updater] = authorized;
        emit UpdaterSet(updater, authorized);
    }
}
