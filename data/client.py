import json
import socket
import time
import logging
from typing import Optional, Any, Dict, List
from dataclasses import dataclass

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
from core.message_framing import MessageFraming

logger = logging.getLogger(__name__)

class DatabaseConstants:
    DEFAULT_RETRY_ATTEMPTS = 3
    DEFAULT_RETRY_DELAY = 1.0
    DEFAULT_TIMEOUT = 10.0
    RECV_BUFFER_SIZE = 4096
    DEFAULT_DATABASE = "siem"
    SECURITY_EVENTS_COLLECTION = "security_events"

DEFAULT_RETRY_ATTEMPTS = DatabaseConstants.DEFAULT_RETRY_ATTEMPTS
DEFAULT_RETRY_DELAY = DatabaseConstants.DEFAULT_RETRY_DELAY
DEFAULT_TIMEOUT = DatabaseConstants.DEFAULT_TIMEOUT

@dataclass
class DatabaseConfig:
    host: str
    port: int
    database: str = "siem"
    timeout: float = DEFAULT_TIMEOUT
    retry_attempts: int = DEFAULT_RETRY_ATTEMPTS
    retry_delay: float = DEFAULT_RETRY_DELAY


class DatabaseError(Exception):
    pass


class ConnectionError(DatabaseError):
    pass


class QueryError(DatabaseError):
    pass


class ResponseSizeError(DatabaseError):
    pass


class TimeoutError(DatabaseError):
    pass


class DatabaseClient:
    SECURITY_EVENTS_COLLECTION = "security_events"
    
    def __init__(self, config: DatabaseConfig):
        self.config = config
        self._socket: Optional[socket.socket] = None
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
        return False
    
    def _connect(self) -> socket.socket:
        last_error: Optional[Exception] = None
        
        for attempt in range(self.config.retry_attempts):
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(self.config.timeout)
                sock.connect((self.config.host, self.config.port))
                logger.debug(f"Connected to database at {self.config.host}:{self.config.port}")
                return sock
            except socket.error as e:
                last_error = e
                logger.warning(
                    f"Connection attempt {attempt + 1}/{self.config.retry_attempts} failed: {e}"
                )
                if attempt < self.config.retry_attempts - 1:
                    time.sleep(self.config.retry_delay)
        
        raise ConnectionError(
            f"Failed to connect to database at {self.config.host}:{self.config.port} "
            f"after {self.config.retry_attempts} attempts: {last_error}"
        )
    
    def _send_request(self, request: Dict[str, Any], operation_context: str = "") -> Dict[str, Any]:
        sock = None
        last_error: Optional[Exception] = None
        
        for attempt in range(self.config.retry_attempts):
            try:
                sock = self._connect()
                
                request_json = json.dumps(request)
                
                request_size = len(request_json.encode('utf-8'))
                if request_size > MessageFraming.MAX_MESSAGE_SIZE:
                    raise ResponseSizeError(
                        f"Request size ({request_size} bytes) exceeds maximum allowed size "
                        f"({MessageFraming.MAX_MESSAGE_SIZE} bytes). Operation: {operation_context}"
                    )
                
                framed_message = MessageFraming.frame_message(request_json)
                sock.sendall(framed_message)
                
                response_data = b""
                while not MessageFraming.has_complete_message(response_data):
                    chunk = sock.recv(4096)
                    if not chunk:
                        raise QueryError(
                            f"Connection closed by server before complete response. "
                            f"Operation: {operation_context}"
                        )
                    response_data += chunk
                    
                    if len(response_data) > MessageFraming.MAX_MESSAGE_SIZE:
                        raise ResponseSizeError(
                            f"Response size exceeds maximum allowed size "
                            f"({MessageFraming.MAX_MESSAGE_SIZE} bytes). "
                            f"Operation: {operation_context}"
                        )
                
                try:
                    response_json, _ = MessageFraming.extract_message(response_data)
                except ValueError as e:
                    if "exceeds maximum allowed size" in str(e):
                        raise ResponseSizeError(
                            f"Response size validation failed: {e}. "
                            f"Operation: {operation_context}"
                        )
                    raise QueryError(
                        f"Message framing error: {e}. Operation: {operation_context}"
                    )
                
                response = json.loads(response_json)
                
                logger.debug(
                    f"Database operation successful. Operation: {operation_context}, "
                    f"Response size: {len(response_data)} bytes"
                )
                
                return response
                
            except socket.timeout:
                last_error = TimeoutError(
                    f"Database query timed out after {self.config.timeout} seconds. "
                    f"Operation: {operation_context}"
                )
                logger.warning(
                    f"Timeout on attempt {attempt + 1}/{self.config.retry_attempts}: "
                    f"{operation_context}"
                )
                if attempt < self.config.retry_attempts - 1:
                    time.sleep(self.config.retry_delay)
                else:
                    raise last_error
                    
            except (ConnectionError, ResponseSizeError) as e:
                logger.error(f"Non-retryable error: {e}")
                raise
                
            except json.JSONDecodeError as e:
                last_error = QueryError(
                    f"Invalid JSON response from database: {e}. "
                    f"Operation: {operation_context}"
                )
                logger.warning(
                    f"JSON decode error on attempt {attempt + 1}/{self.config.retry_attempts}: "
                    f"{operation_context}"
                )
                if attempt < self.config.retry_attempts - 1:
                    time.sleep(self.config.retry_delay)
                else:
                    raise last_error
                    
            except Exception as e:
                if isinstance(e, (QueryError, TimeoutError)):
                    last_error = e
                else:
                    last_error = QueryError(
                        f"Database query failed: {e}. Operation: {operation_context}"
                    )
                logger.warning(
                    f"Error on attempt {attempt + 1}/{self.config.retry_attempts}: {e}"
                )
                if attempt < self.config.retry_attempts - 1:
                    time.sleep(self.config.retry_delay)
                else:
                    raise last_error
            finally:
                if sock:
                    try:
                        sock.close()
                    except Exception:
                        pass
        
        if last_error:
            raise last_error
        raise QueryError(f"Database query failed after retries. Operation: {operation_context}")
    
    def _create_find_request(
        self,
        collection: str,
        query: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        return {
            "database": self.config.database,
            "operation": "find",
            "collection": collection,
            "query": query or {}
        }
    
    def find(
        self,
        collection: str,
        query: Optional[Dict[str, Any]] = None,
        timeout: Optional[float] = None
    ) -> List[Dict[str, Any]]:
        original_timeout = self.config.timeout
        if timeout is not None:
            self.config.timeout = timeout
        
        try:
            request = self._create_find_request(collection, query)
            operation_context = f"find(collection={collection}, query={query})"
            response = self._send_request(request, operation_context)
            
            if response.get("status") == "error":
                error_msg = response.get("message", "Unknown error")
                raise QueryError(
                    f"Database returned error: {error_msg}. Operation: {operation_context}"
                )
            
            data = response.get("data", [])
            logger.info(
                f"Query successful: {len(data)} documents returned. "
                f"Operation: {operation_context}"
            )
            return data
        finally:
            self.config.timeout = original_timeout
    
    def find_security_events(
        self,
        query: Optional[Dict[str, Any]] = None,
        timeout: Optional[float] = None
    ) -> List[Dict[str, Any]]:
        return self.find(self.SECURITY_EVENTS_COLLECTION, query, timeout)
    
    def close(self):
        if self._socket:
            try:
                self._socket.shutdown(socket.SHUT_RDWR)
            except Exception:
                pass
            try:
                self._socket.close()
            except Exception:
                pass
            self._socket = None
            logger.debug("Database connection closed")


def create_client_from_config(host: str, port: int, database: str = "siem") -> DatabaseClient:
    config = DatabaseConfig(host=host, port=port, database=database)
    return DatabaseClient(config)
