import os
from cryptography.fernet import Fernet
from src.config import settings
from src.logger import logger

class EncryptedClinicalDocStore:
    def __init__(self, key: str = None, storage_dir: str = None):
        self.key = key or settings.encryption_key
        self.storage_dir = storage_dir or settings.storage_dir
        self.fernet = Fernet(self.key.encode("utf-8"))
        
        # Enforce folder layout
        os.makedirs(self.storage_dir, exist_ok=True)

    def write_encrypted_file(self, document_id: str, data: bytes) -> str:
        """
        Encrypts document bytes via AES-256 and writes to storage_dir.
        """
        encrypted_data = self.fernet.encrypt(data)
        file_name = f"{document_id}.enc"
        file_path = os.path.join(self.storage_dir, file_name)
        
        with open(file_path, "wb") as f:
            f.write(encrypted_data)
            
        logger.info(
            "Document encrypted and saved to Clinical Document Store.",
            extra={"document_id": document_id, "file_path": file_path}
        )
        return os.path.abspath(file_path)

    def read_decrypted_file(self, document_id: str) -> bytes:
        """
        Reads and decrypts document bytes from storage_dir.
        """
        file_name = f"{document_id}.enc"
        file_path = os.path.join(self.storage_dir, file_name)
        
        if not os.path.exists(file_path):
            logger.error(f"Document file not found: {file_path}")
            raise FileNotFoundError(f"Document {document_id} not found in store.")
            
        with open(file_path, "rb") as f:
            encrypted_data = f.read()
            
        try:
            return self.fernet.decrypt(encrypted_data)
        except Exception as e:
            logger.error(f"Cryptographic key mismatch or payload corruption for {document_id}")
            raise e

doc_store = EncryptedClinicalDocStore()
