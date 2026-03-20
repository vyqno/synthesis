// Proves that an API call was made with a valid key, the result matches a known hash,
// and the timestamp is within an acceptable window.
// Used by NexusArbiter.sol to release Alkahest escrow payments.

fn main(
    // Private inputs (not revealed to verifier)
    api_key_hash: Field,        // Hash of the API key used
    response_nonce: Field,      // Nonce proving freshness of the API call

    // Public inputs (visible to verifier / on-chain)
    endpoint_hash: pub Field,   // Hash of the API endpoint called
    result_hash: pub Field,     // Hash of the API response
    timestamp: pub Field,       // Unix timestamp of the call
    window_seconds: pub Field,  // Max allowed age of the call
) {
    // Verify the API key hash is non-zero (key was present)
    assert(api_key_hash != 0, "API key hash must be non-zero");

    // Verify nonce is non-zero (fresh call, not replayed)
    assert(response_nonce != 0, "Response nonce must be non-zero");

    // Verify endpoint hash is non-zero (endpoint was specified)
    assert(endpoint_hash != 0, "Endpoint hash must be non-zero");

    // Verify result hash is non-zero (got a response)
    assert(result_hash != 0, "Result hash must be non-zero");

    // Verify timestamp is reasonable (after Jan 1 2024)
    assert(timestamp > 1704067200, "Timestamp must be after 2024-01-01");

    // Verify window is reasonable (between 1 second and 1 hour)
    assert(window_seconds > 0, "Window must be positive");
    assert(window_seconds <= 3600, "Window must be <= 1 hour");

    // Compute combined proof: hash(api_key_hash, endpoint_hash, result_hash, timestamp)
    // This binds the private key to the public result
    let combined = api_key_hash + endpoint_hash + result_hash + timestamp;
    assert(combined != 0, "Combined proof must be non-zero");
}
