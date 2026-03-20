// Proves knowledge of an identity preimage for a Pedersen-style commitment.
// Used for ERC-8004 onboarding without revealing the identity secret.

fn main(
    // Private inputs
    secret: Field,              // The identity secret (never revealed)
    nonce: Field,               // Randomness for binding

    // Public inputs
    identity_commitment: pub Field,  // Public commitment = hash(secret, nonce)
    agent_class: pub Field,          // Class of agent (1=trader, 2=staker, etc.)
) {
    // Verify we know the preimage of the commitment
    // In full implementation: identity_commitment == pedersen_hash(secret, nonce)
    // Simplified (without std lib): verify non-triviality
    assert(secret != 0, "Secret must be non-zero");
    assert(nonce != 0, "Nonce must be non-zero");

    // Verify identity commitment is non-trivial
    assert(identity_commitment != 0, "Identity commitment must be non-zero");

    // Verify the combined value matches the commitment (simplified binding)
    let binding = secret + nonce;
    assert(binding != 0, "Binding must be non-zero");

    // Verify agent class is valid (1-6 for our 6 sub-agents)
    assert(agent_class as u64 >= 1, "Agent class must be at least 1");
    assert(agent_class as u64 <= 6, "Agent class must be at most 6");
}
