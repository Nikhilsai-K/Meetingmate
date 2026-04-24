"""AES-GCM helpers for encrypting integration credentials at rest.

The master key comes from env (`INTEGRATION_CREDENTIAL_AES_KEY`) — must be 32 hex chars
(interpreted as 16 raw bytes) minimum; in production we use a 32-byte key from KMS.
"""

from __future__ import annotations

import os

from cryptography.hazmat.primitives.ciphers.aead import AESGCM


def _derive_key(hex_key: str) -> bytes:
    raw = bytes.fromhex(hex_key)
    if len(raw) not in (16, 24, 32):
        raise ValueError("INTEGRATION_CREDENTIAL_AES_KEY must decode to 16/24/32 bytes")
    return raw


def encrypt(plaintext: bytes, hex_key: str) -> bytes:
    aes = AESGCM(_derive_key(hex_key))
    nonce = os.urandom(12)
    ct = aes.encrypt(nonce, plaintext, associated_data=None)
    return nonce + ct


def decrypt(blob: bytes, hex_key: str) -> bytes:
    aes = AESGCM(_derive_key(hex_key))
    nonce, ct = blob[:12], blob[12:]
    return aes.decrypt(nonce, ct, associated_data=None)
