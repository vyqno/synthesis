// Proves that a private balance exceeds a public threshold,
// without revealing the actual balance.

fn main(
    // Private input
    private_balance: Field,     // Actual balance (secret)

    // Public inputs
    threshold: pub Field,       // Minimum required balance
    asset_hash: pub Field,      // Hash identifying the asset (e.g., wstETH)
) {
    // Verify balance is non-negative
    assert(private_balance as u64 >= 0, "Balance must be non-negative");

    // The core assertion: private_balance > threshold
    // We express this as: private_balance - threshold >= 1
    let diff = private_balance as u64 - threshold as u64;
    assert(diff >= 1, "Balance must exceed threshold");

    // Ensure we're talking about a valid asset
    assert(asset_hash != 0, "Asset hash must be non-zero");
}
