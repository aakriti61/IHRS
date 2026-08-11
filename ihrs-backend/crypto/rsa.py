"""
RSA-512 implemented from scratch.
No cryptography libraries used — pure Python.

Purpose in IHRS: each Hospital has an RSA keypair.
The AES key used to encrypt a HealthRecord is encrypted
with the hospital's RSA public key, and only that hospital's
RSA private key can decrypt it back.

WARNING (for viva): 512-bit RSA is cryptographically broken
in the real world (factorable within hours on modern hardware).
It is used here ONLY because this is a college project meant
to demonstrate the algorithm from scratch — pure-Python modular
exponentiation and primality testing get too slow at real-world
key sizes like 2048-bit. Production systems must use 2048+ bit
keys via a proper library.
"""

import random

KEY_BITS = 512          # total bit-length of modulus n
PRIME_BITS = KEY_BITS // 2   # each of p, q is half that
PUBLIC_EXPONENT = 65537      # conventional choice, prime, few 1-bits (fast to exponentiate)


# ─────────────────────────────────────────────
# Miller-Rabin primality test
# ─────────────────────────────────────────────
def is_prime(n: int, rounds: int = 20) -> bool:
    """
    Probabilistic primality test.
    Returns False if n is DEFINITELY composite.
    Returns True if n is PROBABLY prime — error probability
    is at most 4^(-rounds), i.e. with rounds=20 the chance
    of a false positive is astronomically small (~1 in 10^12).
    """
    if n < 2:
        return False
    # quick check against small primes to reject obvious composites fast
    small_primes = [2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37]
    for p in small_primes:
        if n == p:
            return True
        if n % p == 0:
            return False

    # write n - 1 as 2^r * d with d odd
    r, d = 0, n - 1
    while d % 2 == 0:
        r += 1
        d //= 2

    for _ in range(rounds):
        a = random.randrange(2, n - 1)
        x = pow(a, d, n)   # a^d mod n
        if x == 1 or x == n - 1:
            continue  # this round says "probably prime", try next round
        for _ in range(r - 1):
            x = pow(x, 2, n)
            if x == n - 1:
                break
        else:
            # loop completed without breaking → n is definitely composite
            return False
    return True


def generate_prime(bits: int) -> int:
    """
    Generates a random prime number with exactly `bits` bits.
    Keeps generating random odd candidates until Miller-Rabin
    says one is (probably) prime.
    """
    while True:
        candidate = random.getrandbits(bits)
        candidate |= (1 << (bits - 1))  # force the top bit → guarantees exactly `bits` bits
        candidate |= 1                  # force odd (even numbers > 2 are never prime)
        if is_prime(candidate):
            return candidate


# ─────────────────────────────────────────────
# Extended Euclidean Algorithm
# Finds gcd(a, b) AND the coefficients x, y such that
# a*x + b*y = gcd(a, b)   (Bezout's identity)
# We use this to find the modular inverse of e mod phi(n).
# ─────────────────────────────────────────────
def extended_gcd(a: int, b: int):
    """Returns (gcd, x, y) such that a*x + b*y = gcd"""
    if b == 0:
        return (a, 1, 0)
    gcd, x1, y1 = extended_gcd(b, a % b)
    x = y1
    y = x1 - (a // b) * y1
    return (gcd, x, y)


def mod_inverse(e: int, phi: int) -> int:
    """
    Finds d such that (e * d) mod phi == 1.
    This is the private exponent.
    Raises an error if no inverse exists (e and phi not coprime).
    """
    gcd, x, _ = extended_gcd(e, phi)
    if gcd != 1:
        raise ValueError("e and phi(n) are not coprime — no modular inverse exists")
    return x % phi


# ─────────────────────────────────────────────
# Keypair generation
# ─────────────────────────────────────────────
def generate_rsa_keypair(bits: int = KEY_BITS):
    """
    Generates an RSA keypair.
    Returns: (public_key, private_key)
             public_key  = (e, n)
             private_key = (d, n)
    """
    half = bits // 2

    p = generate_prime(half)
    q = generate_prime(half)
    while p == q:  # extremely unlikely, but must never happen
        q = generate_prime(half)

    n = p * q
    phi = (p - 1) * (q - 1)

    e = PUBLIC_EXPONENT
    # in the rare case 65537 isn't coprime with phi, fall back to searching
    if extended_gcd(e, phi)[0] != 1:
        e = 3
        while extended_gcd(e, phi)[0] != 1:
            e += 2

    d = mod_inverse(e, phi)

    public_key = (e, n)
    private_key = (d, n)
    return public_key, private_key


# ─────────────────────────────────────────────
# Encrypt / decrypt
# RSA encrypts INTEGERS smaller than n, not raw bytes directly.
# Since we're using RSA only to wrap a 16-byte AES key, the
# integer will always be small enough to fit under a 512-bit n.
# ─────────────────────────────────────────────
def rsa_encrypt(plaintext_bytes: bytes, public_key) -> bytes:
    """
    Encrypts bytes (expected: a 16-byte AES key) using RSA public key.
    plaintext_bytes must convert to an integer smaller than n.
    """
    e, n = public_key
    plaintext_int = int.from_bytes(plaintext_bytes, byteorder="big")

    if plaintext_int >= n:
        raise ValueError("Plaintext too large for this RSA key size")

    ciphertext_int = pow(plaintext_int, e, n)

    # n is a KEY_BITS-bit number → convert back to fixed-length bytes
    byte_len = (n.bit_length() + 7) // 8
    return ciphertext_int.to_bytes(byte_len, byteorder="big")


def rsa_decrypt(ciphertext_bytes: bytes, private_key) -> bytes:
    """
    Decrypts bytes back to the original plaintext (the AES key)
    using the RSA private key.
    """
    d, n = private_key
    ciphertext_int = int.from_bytes(ciphertext_bytes, byteorder="big")

    plaintext_int = pow(ciphertext_int, d, n)

    # AES-128 key is always exactly 16 bytes
    return plaintext_int.to_bytes(16, byteorder="big")


# ─────────────────────────────────────────────
# Self-test
# Run: python crypto/rsa.py
# ─────────────────────────────────────────────
if __name__ == "__main__":
    import os
    import time

    print("Generating 512-bit RSA keypair... (may take a few seconds)")
    start = time.time()
    public_key, private_key = generate_rsa_keypair()
    elapsed = time.time() - start
    print(f"✅ Keypair generated in {elapsed:.2f}s")

    e, n = public_key
    d, _ = private_key
    print(f"n bit length: {n.bit_length()} (should be close to 512)")
    print(f"e = {e}")

    # Simulate what actually happens in IHRS: encrypting a 16-byte AES key
    aes_key = os.urandom(16)
    print(f"\nOriginal AES key: {aes_key.hex()}")

    encrypted_key = rsa_encrypt(aes_key, public_key)
    print(f"RSA-encrypted:    {encrypted_key.hex()}")

    decrypted_key = rsa_decrypt(encrypted_key, private_key)
    print(f"RSA-decrypted:    {decrypted_key.hex()}")

    assert decrypted_key == aes_key, "RSA round-trip FAILED — do not proceed"
    print("\n✅ RSA encrypt/decrypt round-trip works — AES key survives intact")

    # Sanity check: encrypting the same key twice should give the SAME
    # ciphertext (unlike AES-CBC) — RSA here is deterministic since we're
    # not using padding schemes like OAEP. Worth knowing for viva:
    # this is why RSA is only used to wrap a one-time AES key, never to
    # encrypt large or repeated data directly.
    encrypted_again = rsa_encrypt(aes_key, public_key)
    assert encrypted_again == encrypted_key
    print("✅ Confirmed: RSA here is deterministic (no OAEP padding) — expected for this project")