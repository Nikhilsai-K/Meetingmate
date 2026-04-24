from meetingmate.core.crypto import decrypt, encrypt


def test_encrypt_decrypt_roundtrip() -> None:
    key = "0123456789abcdef0123456789abcdef"
    msg = b"hello secret token"
    blob = encrypt(msg, key)
    assert blob != msg
    assert decrypt(blob, key) == msg


def test_decrypt_fails_with_wrong_key() -> None:
    key_a = "0123456789abcdef0123456789abcdef"
    key_b = "fedcba9876543210fedcba9876543210"
    blob = encrypt(b"payload", key_a)
    try:
        decrypt(blob, key_b)
    except Exception:
        return
    raise AssertionError("expected decryption to fail with wrong key")
