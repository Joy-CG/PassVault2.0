"""
generator.py — Cryptographically secure password generator.

Uses secrets.choice() instead of random.choice().
The secrets module is backed by the OS CSPRNG (os.urandom),
making it safe for generating passwords and keys — unlike
the random module which is designed for simulations, not security.
"""

import secrets
import string

# Character pools
LOWERCASE  = string.ascii_lowercase          # a-z
UPPERCASE  = string.ascii_uppercase          # A-Z
DIGITS     = string.digits                   # 0-9
SYMBOLS    = "!@#$%^&*()_+-=[]{}|;:,.<>?"   # common symbols (avoids quotes)


def generate_password(
    length: int = 16,
    use_upper: bool = True,
    use_digits: bool = True,
    use_symbols: bool = True,
) -> str:
    """
    Generate a cryptographically secure random password.

    Algorithm:
      1. Build the character pool from enabled categories.
      2. Guarantee at least one character from each enabled category
         (so the password always meets common complexity requirements).
      3. Fill remaining slots from the full pool.
      4. Shuffle with secrets.SystemRandom to avoid positional bias.

    Args:
        length:      Total password length (min 4, max 128).
        use_upper:   Include uppercase letters.
        use_digits:  Include digits.
        use_symbols: Include symbol characters.

    Returns:
        A random password string of the requested length.

    Raises:
        ValueError: If length < number of required character categories,
                    or if no character categories are selected.
    """
    if length < 4:
        length = 4
    if length > 128:
        length = 128

    # Build pool and mandatory characters
    pool      = LOWERCASE  # always include lowercase
    mandatory = [secrets.choice(LOWERCASE)]

    if use_upper:
        pool += UPPERCASE
        mandatory.append(secrets.choice(UPPERCASE))

    if use_digits:
        pool += DIGITS
        mandatory.append(secrets.choice(DIGITS))

    if use_symbols:
        pool += SYMBOLS
        mandatory.append(secrets.choice(SYMBOLS))

    if not pool:
        raise ValueError("At least one character category must be selected.")

    # Fill remaining slots
    remaining = [secrets.choice(pool) for _ in range(length - len(mandatory))]

    # Combine and shuffle
    password_chars = mandatory + remaining
    secrets.SystemRandom().shuffle(password_chars)

    return "".join(password_chars)


def estimate_entropy(length: int, pool_size: int) -> float:
    """
    Return the entropy in bits: log2(pool_size ^ length).
    Higher is better. 60+ bits is reasonable; 80+ is strong; 100+ is excellent.
    """
    import math
    return length * math.log2(pool_size)


def pool_size(use_upper: bool, use_digits: bool, use_symbols: bool) -> int:
    size = 26  # lowercase always included
    if use_upper:   size += 26
    if use_digits:  size += 10
    if use_symbols: size += len(SYMBOLS)
    return size
