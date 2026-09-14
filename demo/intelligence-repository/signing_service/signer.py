"""Intentional legacy RSA signing usage for ECDAT deterministic demo."""

from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import padding, rsa


def sign_payload(private_key: rsa.RSAPrivateKey, payload: bytes) -> bytes:
    return private_key.sign(
        payload,
        padding.PKCS1v15(),
        hashes.SHA256(),
    )
