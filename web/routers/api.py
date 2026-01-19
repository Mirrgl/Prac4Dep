import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import Response

from ..dependencies import require_auth, get_event_service
from ...services.event_service import EventService
from ...data.client import ConnectionError, QueryError, DatabaseError


logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["api"])

def _get_dashboard_field(
    event_service: EventService,
    field: str,
    default=None
):
    try:
        dashboard_data = event_service.get_dashboard_data()
        
        if "error" in dashboard_data:
            error_msg = dashboard_data["error"]
            logger.error(f"Dashboard data retrieval failed for field '{field}': {error_msg}")
            return {"data": default if default else [], "error": error_msg}
        
        return dashboard_data.get(field, default if default else [])
    except ConnectionError as e:
        logger.error(f"Database connection error fetching {field}: {e}")
        return {"data": default if default else [], "error": f"Database connection failed: {e}"}
    except QueryError as e:
        logger.error(f"Database query error fetching {field}: {e}")
        return {"data": default if default else [], "error": f"Query failed: {e}"}
    except DatabaseError as e:
        logger.error(f"Database error fetching {field}: {e}")
        return {"data": default if default else [], "error": f"Database error: {e}"}
    except Exception as e:
        logger.error(f"Unexpected error fetching {field}: {e}", exc_info=True)
        return {"data": default if default else [], "error": str(e)}


@router.get("/dashboard/active-agents")
async def get_active_agents(
    username: str = Depends(require_auth),
    event_service: EventService = Depends(get_event_service)
):
    logger.debug(f"User {username} requesting active agents data")
    result = _get_dashboard_field(event_service, "active_agents")
    return {"agents": result} if isinstance(result, list) else {"agents": [], **result}


@router.get("/dashboard/recent-logins")
async def get_recent_logins(
    username: str = Depends(require_auth),
    event_service: EventService = Depends(get_event_service)
):
    logger.debug(f"User {username} requesting recent logins data")
    result = _get_dashboard_field(event_service, "recent_logins")
    return {"logins": result} if isinstance(result, list) else {"logins": [], **result}


@router.get("/dashboard/hosts")
async def get_hosts(
    username: str = Depends(require_auth),
    event_service: EventService = Depends(get_event_service)
):
    logger.debug(f"User {username} requesting hosts data")
    result = _get_dashboard_field(event_service, "host_list")
    return {"hosts": result} if isinstance(result, list) else {"hosts": [], **result}


@router.get("/dashboard/events-by-type")
async def get_events_by_type(
    username: str = Depends(require_auth),
    event_service: EventService = Depends(get_event_service)
):
    logger.debug(f"User {username} requesting events by type data")
    result = _get_dashboard_field(event_service, "events_by_type")
    return {"event_types": result} if isinstance(result, list) else {"event_types": [], **result}


@router.get("/dashboard/events-by-severity")
async def get_events_by_severity(
    username: str = Depends(require_auth),
    event_service: EventService = Depends(get_event_service)
):
    logger.debug(f"User {username} requesting events by severity data")
    result = _get_dashboard_field(event_service, "events_by_severity")
    return {"severities": result} if isinstance(result, list) else {"severities": [], **result}


@router.get("/dashboard/top-users")
async def get_top_users(
    username: str = Depends(require_auth),
    event_service: EventService = Depends(get_event_service)
):
    logger.debug(f"User {username} requesting top users data")
    result = _get_dashboard_field(event_service, "top_users")
    return {"users": result} if isinstance(result, list) else {"users": [], **result}


@router.get("/dashboard/top-processes")
async def get_top_processes(
    username: str = Depends(require_auth),
    event_service: EventService = Depends(get_event_service)
):
    logger.debug(f"User {username} requesting top processes data")
    result = _get_dashboard_field(event_service, "top_processes")
    return {"processes": result} if isinstance(result, list) else {"processes": [], **result}


@router.get("/dashboard/timeline")
async def get_event_timeline(
    username: str = Depends(require_auth),
    event_service: EventService = Depends(get_event_service)
):
    logger.debug(f"User {username} requesting event timeline data")
    default_timeline = [{"hour": h, "event_count": 0} for h in range(24)]
    result = _get_dashboard_field(event_service, "event_timeline", default_timeline)
    return {"timeline": result} if isinstance(result, list) else {"timeline": default_timeline, **result}

@router.get("/events")
async def search_events(
    query: Optional[str] = None,
    hostname: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    severity: Optional[str] = None,
    event_type: Optional[str] = None,
    page: int = 1,
    page_size: int = 50,
    username: str = Depends(require_auth),
    event_service: EventService = Depends(get_event_service)
):
    logger.debug(f"User {username} searching events with query={query}, hostname={hostname}, "
                 f"start_date={start_date}, end_date={end_date}, severity={severity}, "
                 f"event_type={event_type}, page={page}, page_size={page_size}")
    
    try:
        filters = {
            "query": query,
            "hostname": hostname,
            "start_date": start_date,
            "end_date": end_date,
            "severity": severity,
            "event_type": event_type,
        }
        
        result = event_service.search(filters=filters, page=page, page_size=page_size)
        
        logger.info(f"Search returned {result['total']} events, showing page {result['page']}/{result['total_pages']}")
        
        return result
        
    except ConnectionError as e:
        logger.error(f"Database connection error during event search: {e}")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Database connection failed: {e}"
        )
    except QueryError as e:
        logger.error(f"Database query error during event search: {e}")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Database query failed: {e}"
        )
    except DatabaseError as e:
        logger.error(f"Database error during event search: {e}")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Database error: {e}"
        )
    except Exception as e:
        logger.error(f"Unexpected error during event search: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Search failed: {e}"
        )


@router.get("/events/export")
async def export_events(
    format: str = "json",
    query: Optional[str] = None,
    hostname: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    severity: Optional[str] = None,
    event_type: Optional[str] = None,
    username: str = Depends(require_auth),
    event_service: EventService = Depends(get_event_service)
):
    logger.info(f"User {username} exporting events in {format} format with filters: "
                f"query={query}, hostname={hostname}, start_date={start_date}, "
                f"end_date={end_date}, severity={severity}, event_type={event_type}")
    
    if format.lower() not in ("json", "csv"):
        logger.warning(f"Invalid export format requested: {format}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid export format: {format}. Supported formats: json, csv"
        )
    
    try:
        filters = {
            "query": query,
            "hostname": hostname,
            "start_date": start_date,
            "end_date": end_date,
            "severity": severity,
            "event_type": event_type,
        }
        
        content = event_service.export(filters=filters, format=format)
        
        if format.lower() == "csv":
            media_type = "text/csv"
            filename = "events_export.csv"
        else:
            media_type = "application/json"
            filename = "events_export.json"
        
        return Response(
            content=content,
            media_type=media_type,
            headers={
                "Content-Disposition": f'attachment; filename="{filename}"'
            }
        )
        
    except ValueError as e:
        logger.warning(f"Invalid export request: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except ConnectionError as e:
        logger.error(f"Database connection error during export: {e}")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Database connection failed: {e}"
        )
    except QueryError as e:
        logger.error(f"Database query error during export: {e}")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Database query failed: {e}"
        )
    except DatabaseError as e:
        logger.error(f"Database error during export: {e}")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Database error: {e}"
        )
    except Exception as e:
        logger.error(f"Unexpected error during export: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Export failed: {str(e)}"
        )
