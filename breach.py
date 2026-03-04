"""
breach.py — HaveIBeenPwned password breach checker.

Uses the k-anonymity model:
  1. SHA-1 hash the password locally
  2. Send only the first 5 characters of the hash to the API
  3. API returns all hashes starting with those 5 chars
  4. Check if the full hash appears in the results — locally, never sent

The actual password NEVER leaves the machine.
API docs: https://haveibeenpwned.com/API/v3#SearchingPwnedPasswordsByRange
"""

import hashlib
import urllib.request
import urllib.error


def check_breach(password: str) -> tuple[bool, int]:
    """
    Check if a password has appeared in known data breaches.

    Args:
        password: The plaintext password to check.

    Returns:
        (found: bool, count: int)
        - found: True if the password appears in breach data
        - count: number of times seen in breaches (0 if not found)

    Raises:
        ConnectionError: if the API cannot be reached
    """
    # Step 1: SHA-1 hash the password
    sha1 = hashlib.sha1(password.encode("utf-8")).hexdigest().upper()
    prefix = sha1[:5]
    suffix = sha1[5:]

    # Step 2: Send only the first 5 chars
    url = f"https://api.pwnedpasswords.com/range/{prefix}"
    try:
        req = urllib.request.Request(
            url,
            headers={
                "User-Agent":     "PassVault-BreachChecker/1.0",
                "Add-Padding":    "true",   # Prevents traffic analysis
            }
        )
        with urllib.request.urlopen(req, timeout=8) as resp:
            body = resp.read().decode("utf-8")
    except urllib.error.URLError as e:
        raise ConnectionError(f"Could not reach HaveIBeenPwned API: {e}")

    # Step 3: Check if our suffix appears in the response
    for line in body.splitlines():
        parts = line.split(":")
        if len(parts) != 2:
            continue
        response_suffix, count_str = parts
        if response_suffix.strip() == suffix:
            return True, int(count_str.strip())

    return False, 0


def breach_summary(found: bool, count: int) -> tuple[str, str]:
    """
    Return a (message, severity) tuple for display in the UI.
    severity is one of: 'safe', 'warning', 'danger'
    """
    if not found:
        return "Not found in any known breaches.", "safe"
    if count < 10:
        return f"Found {count}x in breach data. Consider changing this password.", "warning"
    if count < 1000:
        return f"Found {count:,}x in breach data. Change this password.", "danger"
    return f"Found {count:,}x in breach data. This password is severely compromised.", "danger"
