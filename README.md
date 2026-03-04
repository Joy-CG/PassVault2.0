# 🔐 PassVault 2.0 — Secure Local Password Manager

A desktop password manager built with Python and Tkinter.  
Designed as a cybersecurity portfolio project covering encryption, key derivation, breach detection, and secure local storage.

---

## What's New in 2.0

-  **Argon2id** replaces PBKDF2 for significantly stronger key derivation
-  **HaveIBeenPwned integration** — check passwords against 10+ billion breached credentials
---

## Features

- **Master password** — your single key to unlock everything
- **AES encryption** — all passwords encrypted at rest with Fernet (AES-128-CBC + HMAC-SHA256)
- **Argon2id key derivation** — memory-hard algorithm, resistant to GPU and side-channel attacks
- **Breach detection** — check any saved password against HIBP's database using k-anonymity
- **Live search** — filter entries by site or username in real time
- **Full CRUD** — add, edit, delete entries
- **Copy to clipboard** — one click to copy any password

---

## Setup

### 1. Install dependencies
```bash
pip install -r requirements.txt
```

> `tkinter` ships with standard Python on Windows, macOS, and most Linux distros.  
> If missing on Linux: `sudo apt install python3-tk`

### 2. Run
```bash
python main.py
```

On first launch you'll be prompted to create a master password (min. 8 characters).  
This generates `vault.salt` and `vault.enc` in the same directory.

---

## Security Design

| Concept | Implementation |
|---|---|
| Key derivation | Argon2id — memory-hard, side-channel resistant |
| Argon2id parameters | `time_cost=3` · `memory_cost=64MB` · `parallelism=2` |
| Encryption | Fernet (AES-128-CBC + HMAC-SHA256) |
| Salt | 16 random bytes, generated once, stored in `vault.salt` |
| Master password | **Never stored** — wrong password → `InvalidToken` exception |
| Entry IDs | 8 random bytes (`os.urandom`) |
| Breach checking | HIBP k-anonymity — only first 5 chars of SHA1 hash sent over network |

### Why Argon2id over PBKDF2?

PBKDF2 is CPU-bound, meaning attackers with GPUs or ASICs can brute-force it cheaply. Argon2id is **memory-hard** — it requires a large amount of RAM per attempt, making large-scale cracking attacks orders of magnitude more expensive. It won the [Password Hashing Competition](https://www.password-hashing.net/) in 2015 and is the current OWASP recommended algorithm.

---

## File Structure

```
PassVault-Argon2ID/
├── main.py          # Entry point
├── vault.py         # Encryption, Argon2id key derivation, storage
├── ui.py            # Tkinter GUI (login + vault screen + HIBP checker)
├── breach.py        # HaveIBeenPwned k-anonymity integration
├── generator.py     # Password generator
├── requirements.txt
├── vault.salt       # Generated on first run (not secret, but don't share it)
└── vault.enc        # Encrypted vault (safe to back up, useless without master pw)
```

---

## Usage

### Checking a password for breaches
Click the **Check Breach** button next to any saved entry. PassVault will query HIBP and report:
- ✅ **Not found** — password has not appeared in any known breach
- ⚠️ **Compromised** — password found in N breached records — you should change it immediately

---

## Requirements

```
argon2-cffi
cryptography
requests
```

---

## Author- Cortland Gann

Built as part of a SOC/Blue Team cybersecurity portfolio.  
Demonstrates: symmetric encryption, memory-hard key derivation, secure API design (k-anonymity), and desktop application development.

---

## License
