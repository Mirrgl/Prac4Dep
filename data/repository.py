import re
import logging
from typing import Optional, Any, Dict, List
from datetime import datetime
from collections import defaultdict

from .client import DatabaseClient

logger = logging.getLogger(__name__)


class EventRepository:
    def __init__(self, db_client: DatabaseClient):
        self.db_client = db_client
    
    def find_all(
        self, 
        query: Optional[Dict[str, Any]] = None,
        limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        events = self.db_client.find_security_events(query or {})
        
        if limit is not None and limit > 0:
            return events[:limit]
        
        return events
    
    def find_for_dashboard(self) -> List[Dict[str, Any]]:
        events = self.db_client.find_security_events({})
        
        try:
            sorted_events = sorted(
                events,
                key=lambda e: e.get("timestamp", ""),
                reverse=True
            )
            return sorted_events[:10000]
        except Exception as e:
            logger.warning(f"Failed to sort events by timestamp: {e}")
            return events[:10000]
    
    def find_filtered(
        self,
        query: Optional[str] = None,
        hostname: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        severity: Optional[str] = None,
        event_type: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        events = self.find_all()
        return _apply_filters(
            events,
            query=query,
            hostname=hostname,
            start_date=start_date,
            end_date=end_date,
            severity=severity,
            event_type=event_type
        )

def _apply_filters(
    events: List[Dict[str, Any]],
    query: Optional[str] = None,
    hostname: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    severity: Optional[str] = None,
    event_type: Optional[str] = None
) -> List[Dict[str, Any]]:
    filtered = events
    
    if query:
        try:
            pattern = re.compile(query)
            filtered = [
                e for e in filtered
                if any(
                    pattern.search(str(e.get(field, "")))
                    for field in ["hostname", "source", "event_type", "severity", 
                                  "user", "process", "command", "raw_log"]
                )
            ]
        except re.error:
            filtered = [
                e for e in filtered
                if any(
                    query in str(e.get(field, ""))
                    for field in ["hostname", "source", "event_type", "severity",
                                  "user", "process", "command", "raw_log"]
                )
            ]
    
    if hostname:
        hostname_lower = hostname.lower()
        filtered = [
            e for e in filtered
            if hostname_lower in str(e.get("hostname", "")).lower()
        ]
    
    if start_date:
        try:
            start_dt = datetime.strptime(start_date, "%Y-%m-%d")
            filtered = [
                e for e in filtered
                if _parse_event_date(e.get("timestamp", "")) >= start_dt
            ]
        except ValueError:
            pass
    
    if end_date:
        try:
            end_dt = datetime.strptime(end_date, "%Y-%m-%d")
            end_dt = end_dt.replace(hour=23, minute=59, second=59)
            filtered = [
                e for e in filtered
                if _parse_event_date(e.get("timestamp", "")) <= end_dt
            ]
        except ValueError:
            pass
    
    if severity:
        severity_lower = severity.lower()
        filtered = [
            e for e in filtered
            if str(e.get("severity", "")).lower() == severity_lower
        ]
    
    if event_type:
        event_type_lower = event_type.lower()
        filtered = [
            e for e in filtered
            if event_type_lower in str(e.get("event_type", "")).lower()
        ]
    
    return filtered


def _parse_event_date(timestamp: str) -> datetime:
    if not timestamp:
        return datetime.min
    
    for fmt in ["%Y-%m-%dT%H:%M:%SZ", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%d %H:%M:%S", "%Y-%m-%d"]:
        try:
            return datetime.strptime(timestamp.split(".")[0].replace("Z", ""), fmt.replace("Z", ""))
        except ValueError:
            continue
    
    return datetime.min

def _aggregate_dashboard_data(events: List[Dict[str, Any]]) -> Dict[str, Any]:
    agents: Dict[str, str] = {}
    logins: List[Dict[str, Any]] = []
    hosts: Dict[str, int] = defaultdict(int)
    event_types: Dict[str, int] = defaultdict(int)
    severities: Dict[str, int] = defaultdict(int)
    users: Dict[str, int] = defaultdict(int)
    processes: Dict[str, int] = defaultdict(int)
    hourly_counts: Dict[int, int] = defaultdict(int)
    
    for event in events:
        hostname = event.get("hostname", "unknown")
        evt_type = event.get("event_type", "unknown")
        severity = event.get("severity", "unknown")
        user = event.get("user")
        process = event.get("process")
        timestamp = event.get("timestamp", "")
        agent_last_seen = event.get("agent_last_seen", timestamp)
        source = event.get("source", "unknown")
        
        if hostname:
            if hostname not in agents or agent_last_seen > agents[hostname]:
                agents[hostname] = agent_last_seen
        
        if evt_type in ("user_login", "authentication_failure", "ssh_connection"):
            logins.append({
                "timestamp": timestamp,
                "user": user or "unknown",
                "hostname": hostname,
                "success": evt_type != "authentication_failure",
                "source": source
            })
        
        hosts[hostname] += 1
        
        event_types[evt_type] += 1
        
        severities[severity] += 1
        
        if user:
            users[user] += 1
        
        if process:
            processes[process] += 1
        
        try:
            if timestamp:
                hour = _extract_hour_from_timestamp(timestamp)
                if hour is not None:
                    hourly_counts[hour] += 1
        except Exception:
            pass
    
    sorted_logins = sorted(logins, key=lambda x: x.get("timestamp", ""), reverse=True)[:10]
    sorted_hosts = sorted(hosts.items(), key=lambda x: x[1], reverse=True)
    sorted_users = sorted(users.items(), key=lambda x: x[1], reverse=True)[:10]
    sorted_processes = sorted(processes.items(), key=lambda x: x[1], reverse=True)[:10]
    
    timeline = [{"hour": h, "event_count": hourly_counts.get(h, 0)} for h in range(24)]
    
    return {
        "active_agents": [
            {"agent_id": agent_id, "last_activity": last_activity, "status": "active"}
            for agent_id, last_activity in sorted(agents.items(), key=lambda x: x[1], reverse=True)
        ],
        "recent_logins": sorted_logins,
        "host_list": [
            {"hostname": hostname, "event_count": count, "last_seen": agents.get(hostname, "")}
            for hostname, count in sorted_hosts
        ],
        "events_by_type": [
            {"event_type": evt_type, "count": count}
            for evt_type, count in sorted(event_types.items(), key=lambda x: x[1], reverse=True)
        ],
        "events_by_severity": [
            {"severity": severity, "count": count}
            for severity, count in severities.items()
        ],
        "top_users": [
            {"user": user, "event_count": count}
            for user, count in sorted_users
        ],
        "top_processes": [
            {"process": process, "event_count": count}
            for process, count in sorted_processes
        ],
        "event_timeline": timeline,
        "total_events": len(events)
    }


def _extract_hour_from_timestamp(timestamp: str) -> Optional[int]:
    if not timestamp:
        return None
    
    import re as regex_module
    
    match = regex_module.search(r'[T ](\d{2}):(\d{2})', timestamp)
    if match:
        try:
            hour = int(match.group(1))
            minute = int(match.group(2))
            if 0 <= hour <= 23 and 0 <= minute <= 59:
                if minute >= 30:
                    hour = (hour + 1) % 24
                return hour
        except ValueError:
            pass
    
    return None


def _empty_dashboard_data(error: Optional[str] = None) -> Dict[str, Any]:
    result = {
        "active_agents": [],
        "recent_logins": [],
        "host_list": [],
        "events_by_type": [],
        "events_by_severity": [],
        "top_users": [],
        "top_processes": [],
        "event_timeline": [{"hour": h, "event_count": 0} for h in range(24)],
        "total_events": 0
    }
    if error:
        result["error"] = error
    return result