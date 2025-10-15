import base64
import hashlib
from cryptography.fernet import Fernet

from app.core.config import settings


def get_encryption_key():
    key = getattr(settings, "ENCRYPTION_KEY", None)
    if key:
        return key.encode() if isinstance(key, str) else key
    
    k = hashlib.sha256(settings.SECRET_KEY.encode()).digest()
    return base64.urlsafe_b64encode(k)


class FieldEncryptor:
    def __init__(self):
        key = get_encryption_key()
        self.fernet = Fernet(key)

    def encrypt(self, plaintext: str) -> str:
        if not plaintext:
            return plaintext
        return self.fernet.encrypt(plaintext.encode()).decode()

    def decrypt(self, ciphertext: str) -> str:
        if not ciphertext:
            return ciphertext
        try:
            return self.fernet.decrypt(ciphertext.encode()).decode()
        except:
            return ciphertext


encryptor = FieldEncryptor()
