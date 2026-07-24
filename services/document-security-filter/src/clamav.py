import socket
import struct
from src.config import settings
from src.logger import logger

class ClamAVScanner:
    def __init__(self, host: str = None, port: int = None):
        self.host = host or settings.clamav_host
        self.port = port or settings.clamav_port

    def scan_bytes(self, file_bytes: bytes) -> tuple[bool, str]:
        """
        Scans bytes using ClamAV INSTREAM command over TCP.
        Returns (is_safe, description).
        """
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(5.0)  # Standard fast timeout
            s.connect((self.host, self.port))
            
            s.sendall(b"nINSTREAM\n")
            
            chunk_size = 8192
            offset = 0
            while offset < len(file_bytes):
                chunk = file_bytes[offset:offset+chunk_size]
                length_prefix = struct.pack("!I", len(chunk))
                s.sendall(length_prefix)
                s.sendall(chunk)
                offset += len(chunk)
                
            s.sendall(struct.pack("!I", 0))
            
            response = b""
            while True:
                data = s.recv(1024)
                if not data:
                    break
                response += data
            s.close()
            
            resp_str = response.decode("utf-8", errors="ignore").strip()
            logger.info(f"ClamAV scan output: {resp_str}")
            
            if "FOUND" in resp_str:
                return False, f"Malware detected by ClamAV: {resp_str}"
            elif "OK" in resp_str:
                return True, "No malware detected"
            else:
                # If ClamAV is offline or starting database sync, log warning and fail closed for security
                logger.warning(f"Unexpected ClamAV daemon state: {resp_str}")
                return False, f"Malware scanner state error: {resp_str}"
                
        except Exception as e:
            logger.error("Failed to execute ClamAV socket communication", extra={"error": str(e)})
            # Enforce clinical safety: fail closed if malware checker is unresponsive
            return False, f"Malware scanner connection error: {str(e)}"
