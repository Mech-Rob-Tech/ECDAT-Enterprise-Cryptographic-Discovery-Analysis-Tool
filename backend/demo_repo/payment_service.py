import hashlib
import ssl

from cryptography.hazmat.primitives.asymmetric import rsa, ec
from cryptography.hazmat.primitives.ciphers.aead import AESGCM


private_key = rsa.generate_private_key(
    public_exponent=65537,
    key_size=2048
)

signing_key = ec.generate_private_key(
    ec.SECP256R1()
)

aes = AESGCM(b"0" * 32)

password_hash = hashlib.sha256(
    b"password"
).digest()

legacy_hash = hashlib.md5(
    b"legacy"
).digest()

context = ssl.SSLContext(
    ssl.PROTOCOL_TLS_CLIENT
)