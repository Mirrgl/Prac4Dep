from dataclasses import dataclass
from typing import Optional, Dict, Any


@dataclass
class SecurityEvent:
    id: Optional[int]
    timestamp: str
    hostname: str
    source: str
    event_type: str
    severity: str
    user: Optional[str] = None
    process: Optional[str] = None
    command: Optional[str] = None
    raw_log: str = ""
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SecurityEvent":
        return cls(
            id=data.get("_id"),
            timestamp=data.get("timestamp", ""),
            hostname=data.get("hostname", ""),
            source=data.get("source", ""),
            event_type=data.get("event_type", ""),
            severity=data.get("severity", ""),
            user=data.get("user"),
            process=data.get("process"),
            command=data.get("command"),
            raw_log=data.get("raw_log", "")
        )
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "_id": self.id,
            "timestamp": self.timestamp,
            "hostname": self.hostname,
            "source": self.source,
            "event_type": self.event_type,
            "severity": self.severity,
            "user": self.user,
            "process": self.process,
            "command": self.command,
            "raw_log": self.raw_log
        }
