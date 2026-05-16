"""Symmetric encryption for OAuth tokens stored at rest."""

from functools import lru_cache

from cryptography.fernet import Fernet

from app.config import get_settings


@lru_cache
def _cipher() -> Fernet:
    settings = get_settings()
    if not settings.token_encryption_key:
        raise RuntimeError(
            "TOKEN_ENCRYPTION_KEY not configured — generate with Fernet.generate_key()",
        )
    return Fernet(settings.token_encryption_key.encode())


def encrypt(plaintext: str) -> str:
    return _cipher().encrypt(plaintext.encode()).decode()


def decrypt(ciphertext: str) -> str:
    return _cipher().decrypt(ciphertext.encode()).decode()
