import json
import csv
import io
import logging
from typing import Optional, Any, Dict, List

from data.repository import EventRepository, _aggregate_dashboard_data, _empty_dashboard_data

logger = logging.getLogger(__name__)

SECURITY_EVENT_FIELDS = [
    "_id", "timestamp", "hostname", "source", "event_type",
    "severity", "user", "process", "command", "raw_log"
]

class EventService:
    def __init__(self, repository: EventRepository):
        self.repository = repository
    
    def search(
        self,
        filters: Optional[Dict[str, Any]] = None,
        page: int = 1,
        page_size: int = 50
    ) -> Dict[str, Any]:
        page = max(1, page)
        page_size = min(max(1, page_size), 100)
        
        filters = filters or {}
        
        filtered_events = self.repository.find_filtered(
            query=filters.get("query"),
            hostname=filters.get("hostname"),
            start_date=filters.get("start_date"),
            end_date=filters.get("end_date"),
            severity=filters.get("severity"),
            event_type=filters.get("event_type")
        )
        
        filtered_events.sort(
            key=lambda e: e.get("timestamp", ""),
            reverse=True
        )
        
        total = len(filtered_events)
        total_pages = (total + page_size - 1) // page_size if page_size > 0 else 0
        start_idx = (page - 1) * page_size
        end_idx = start_idx + page_size
        
        paginated_events = filtered_events[start_idx:end_idx]
        
        logger.debug(f"Search returned {total} events, showing page {page}/{total_pages}")
        
        return {
            "events": paginated_events,
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": total_pages
        }
    
    def get_dashboard_data(self) -> Dict[str, Any]:
        try:
            events = self.repository.find_for_dashboard()
            return _aggregate_dashboard_data(events)
        except Exception as e:
            logger.error(
                f"Failed to retrieve dashboard data: {type(e).__name__}: {e}",
                exc_info=True
            )
            return _empty_dashboard_data(error=str(e))
    
    def export(
        self,
        filters: Optional[Dict[str, Any]] = None,
        format: str = "json"
    ) -> str:
        if format.lower() not in ("json", "csv"):
            raise ValueError(f"Invalid export format: {format}. Supported formats: json, csv")
        
        filters = filters or {}
        
        filtered_events = self.repository.find_filtered(
            query=filters.get("query"),
            hostname=filters.get("hostname"),
            start_date=filters.get("start_date"),
            end_date=filters.get("end_date"),
            severity=filters.get("severity"),
            event_type=filters.get("event_type")
        )
        
        filtered_events.sort(
            key=lambda e: e.get("timestamp", ""),
            reverse=True
        )
        
        logger.debug(f"Exporting {len(filtered_events)} events in {format} format")
        
        if format.lower() == "csv":
            return format_events_as_csv(filtered_events)
        else:
            return format_events_as_json(filtered_events)


def format_events_as_json(events: List[Dict[str, Any]]) -> str:
    return json.dumps(events, indent=2, default=str)


def format_events_as_csv(events: List[Dict[str, Any]]) -> str:
    output = io.StringIO()
    writer = csv.DictWriter(
        output,
        fieldnames=SECURITY_EVENT_FIELDS,
        extrasaction='ignore'
    )
    writer.writeheader()
    
    for event in events:
        row = {field: event.get(field, "") for field in SECURITY_EVENT_FIELDS}
        row = {k: (v if v is not None else "") for k, v in row.items()}
        writer.writerow(row)
    
    return output.getvalue()