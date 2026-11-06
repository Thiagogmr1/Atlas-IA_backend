import base64
import hashlib
import os
from typing import Optional

from cryptography.hazmat.primitives.ciphers.aead import AESGCM

from app.core.config import settings


class TokenEncryptionError(Exception):
    """Exceção para falhas na criptografia ou descriptografia de tokens."""
    pass


def _derive_key(key: Optional[str] = None) -> bytes:
    """Gera uma chave determinística de exatamente 32 bytes (256 bits) para o AES-256-GCM."""
    raw_key = key or settings.token_encryption_key or "default_fallback_32_bytes_key!"
    return hashlib.sha256(raw_key.encode("utf-8")).digest()


def encrypt_token(plain_token: str, key: Optional[str] = None) -> str:
    """Criptografa o token utilizando AES-256-GCM com nonce aleatório de 12 bytes.
    
    O resultado retornado é seguro, autenticado e codificado em base64 URL-safe.
    """
    if not plain_token:
        raise TokenEncryptionError("Token não pode estar vazio para criptografia.")

    try:
        derived_key = _derive_key(key)
        aesgcm = AESGCM(derived_key)
        nonce = os.urandom(12)  # Padrão recomendado de 12 bytes para GCM
        ciphertext = aesgcm.encrypt(nonce, plain_token.encode("utf-8"), None)
        # Concatena nonce + ciphertext para armazenamento conjunto
        payload = nonce + ciphertext
        return base64.urlsafe_b64encode(payload).decode("utf-8")
    except Exception as exc:
        raise TokenEncryptionError("Falha na criptografia do token.") from exc


def decrypt_token(encrypted_token_b64: str, key: Optional[str] = None) -> str:
    """Descriptografa o token criptografado com AES-256-GCM.
    
    Verifica a integridade e autenticidade da tag GCM antes de descriptografar.
    """
    if not encrypted_token_b64:
        raise TokenEncryptionError("Payload criptografado não pode estar vazio.")

    try:
        derived_key = _derive_key(key)
        aesgcm = AESGCM(derived_key)
        raw_payload = base64.urlsafe_b64decode(encrypted_token_b64.encode("utf-8"))

        if len(raw_payload) < 28:  # 12 bytes nonce + mínimo 16 bytes tag de autenticação
            raise TokenEncryptionError("Payload criptografado inválido ou truncado.")

        nonce = raw_payload[:12]
        ciphertext = raw_payload[12:]

        decrypted_bytes = aesgcm.decrypt(nonce, ciphertext, None)
        return decrypted_bytes.decode("utf-8")
    except Exception as exc:
        raise TokenEncryptionError("Falha na autenticação ou descriptografia do token.") from exc
