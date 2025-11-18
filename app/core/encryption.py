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
        """
        Decrypt a ciphertext string.
        
        Returns original ciphertext if decryption fails (graceful degradation).
        """
        if not ciphertext:
            return ciphertext
        try:
            return self.fernet.decrypt(ciphertext.encode()).decode()
        except (ValueError, TypeError) as e:
            # Invalid token format or encoding issue
            return ciphertext
        except Exception as e:
            # Fernet InvalidToken or other crypto errors
            # Log this in production for debugging
            return ciphertext


encryptor = FieldEncryptor()
