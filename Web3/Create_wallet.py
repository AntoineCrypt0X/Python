from eth_account import Account


def create_eth_wallet():
    # Create a new account
    acct = Account.create()

    # Extracting private key and public key
    private_key = acct.privateKey.hex()
    public_key = acct.address

    return private_key, public_key


# Generate wallet
private_key, public_key = create_eth_wallet()

# Output the keys
print("Private Key:", private_key)
print("Public Key:", public_key)