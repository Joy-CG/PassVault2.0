"""
vault.py — Encryption, key derivation, and vault persistence.

Security design:
  - Master password is NEVER stored anywhere.
  - Random 16-byte salt generated once, saved alongside the vault.
  - Argon2id derives a 32-byte key from master password + salt.
    Winner of the Password Hashing Competition (2015), recommended by OWASP.
    Memory-hard: attacker needs 64MB RAM per guess — GPU attacks far more
    expensive than against PBKDF2 or bcrypt.
  - Fernet (AES-128-CBC + HMAC-SHA256) encrypts the vault JSON blob.
  - Wrong password -> InvalidToken -> login rejected.

Argon2id parameters (OWASP 2023 minimums):
  time_cost:    3 iterations
  memory_cost:  64 MB (65536 KiB)
  parallelism:  4 threads
  hash_len:     32 bytes
"""

import json
import os
import base64
from cryptography.fernet import Fernet, InvalidToken
from argon2.low_level import hash_secret_raw, Type

VAULT_FILE = "vault.enc"
SALT_FILE  = "vault.salt"

ARGON2_TIME_COST   = 3
ARGON2_MEMORY_COST = 65536   # 64 MB
ARGON2_PARALLELISM = 4
ARGON2_HASH_LEN    = 32


def _derive_key(master_password: str, salt: bytes) -> bytes:
    """
    Derive a Fernet key using Argon2id.
    Memory-hard: requires 64MB RAM per attempt, defeating GPU brute force.
    """
    raw_key = hash_secret_raw(
        secret=master_password.encode(),
        salt=salt,
        time_cost=ARGON2_TIME_COST,
        memory_cost=ARGON2_MEMORY_COST,
        parallelism=ARGON2_PARALLELISM,
        hash_len=ARGON2_HASH_LEN,
        type=Type.ID,
    )
    return base64.urlsafe_b64encode(raw_key)


def _get_or_create_salt() -> bytes:
    if os.path.exists(SALT_FILE):
        with open(SALT_FILE, "rb") as f:
            return f.read()
    salt = os.urandom(16)
    with open(SALT_FILE, "wb") as f:
        f.write(salt)
    return salt


class Vault:
    def __init__(self):
        self._entries: list[dict] = []
        self._fernet: Fernet | None = None

    def create(self, master_password: str) -> None:
        salt = _get_or_create_salt()
        key = _derive_key(master_password, salt)
        self._fernet = Fernet(key)
        self._entries = []
        self.save()

    def unlock(self, master_password: str) -> bool:
        if not os.path.exists(VAULT_FILE):
            return False
        salt = _get_or_create_salt()
        key = _derive_key(master_password, salt)
        fernet = Fernet(key)
        try:
            with open(VAULT_FILE, "rb") as f:
                cipher_blob = f.read()
            plain = fernet.decrypt(cipher_blob)
            self._entries = json.loads(plain.decode())
            self._fernet = fernet
            return True
        except (InvalidToken, json.JSONDecodeError):
            return False

    def lock(self) -> None:
        self._entries = []
        self._fernet = None

    @property
    def is_unlocked(self) -> bool:
        return self._fernet is not None

    def vault_exists(self) -> bool:
        return os.path.exists(VAULT_FILE)

    def save(self) -> None:
        if not self._fernet:
            raise RuntimeError("Vault is locked.")
        plain = json.dumps(self._entries, indent=2).encode()
        cipher_blob = self._fernet.encrypt(plain)
        with open(VAULT_FILE, "wb") as f:
            f.write(cipher_blob)

    def add_entry(self, site: str, username: str, password: str, notes: str = "") -> dict:
        entry = {
            "id":       os.urandom(8).hex(),
            "site":     site.strip(),
            "username": username.strip(),
            "password": password,
            "notes":    notes.strip(),
        }
        self._entries.append(entry)
        self.save()
        return entry

    def update_entry(self, entry_id: str, site: str, username: str,
                     password: str, notes: str = "") -> bool:
        for e in self._entries:
            if e["id"] == entry_id:
                e.update(site=site.strip(), username=username.strip(),
                         password=password, notes=notes.strip())
                self.save()
                return True
        return False

    def delete_entry(self, entry_id: str) -> bool:
        before = len(self._entries)
        self._entries = [e for e in self._entries if e["id"] != entry_id]
        if len(self._entries) < before:
            self.save()
            return True
        return False

    def search(self, query: str) -> list[dict]:
        q = query.lower().strip()
        if not q:
            return list(self._entries)
        return [
            e for e in self._entries
            if q in e["site"].lower() or q in e["username"].lower()
        ]

    def all_entries(self) -> list[dict]:
        return list(self._entries)
