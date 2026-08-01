import hashlib
import hmac

from src.config import settings


def compute_entry_hash(prev_hash: str, event_id: str, document_id: str, service_name: str, event_type: str, payload_json: str, timestamp: str) -> str:
    """Computes SHA-256 hash chaining for an audit log entry."""
    data_str = f"{prev_hash}|{event_id}|{document_id}|{service_name}|{event_type}|{payload_json}|{timestamp}"
    return hashlib.sha256(data_str.encode("utf-8")).hexdigest()


def compute_hmac_signature(entry_hash: str) -> str:
    """Computes HMAC-SHA256 signature using master KMS key."""
    key_bytes = settings.hmac_secret_key.encode("utf-8")
    return hmac.new(key_bytes, entry_hash.encode("utf-8"), hashlib.sha256).hexdigest()


def verify_entry_hmac(entry_hash: str, signature: str) -> bool:
    """Verifies that an entry HMAC signature matches master KMS key."""
    expected = compute_hmac_signature(entry_hash)
    return hmac.compare_digest(expected, signature)
