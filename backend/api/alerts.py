from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime

from app.core.database import get_db
from app.models.schemas import (
    AlertCreate, AlertResponse, AlertUpdate, AlertSearchRequest,
    CorrelationRequest, CorrelationResponse
)
from app.services.alert_service import AlertService
from app.services.correlation_service import CorrelationService
from app.utils.logger import setup_logger

logger = setup_logger(__name__)

router = APIRouter()

@router.post("/", response_model=AlertResponse, status_code=status.HTTP_201_CREATED)
async def create_alert(
    alert_data: AlertCreate,
    db: Session = Depends(get_db)
):
    """Create a new alert"""
    try:
        alert_service = AlertService(db)
        alert = await alert_service.create_alert(alert_data)
        return alert
    except Exception as e:
        logger.error(f"Error creating alert: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create alert: {str(e)}"
        )

@router.get("/", response_model=List[AlertResponse])
async def get_alerts(
    status: Optional[List[str]] = Query(None),
    severity: Optional[List[str]] = Query(None),
    source: Optional[List[str]] = Query(None),
    alert_type: Optional[List[str]] = Query(None),
    correlation_id: Optional[str] = Query(None),
    limit: int = Query(100, le=1000),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db)
):
    """Get alerts with filtering and pagination"""
    try:
        search_params = AlertSearchRequest(
            status=status,
            severity=severity,
            source=source,
            alert_type=alert_type,
            correlation_id=correlation_id,
            limit=limit,
            offset=offset
        )
        
        alert_service = AlertService(db)
        alerts = await alert_service.get_alerts(search_params)
        return alerts
    except Exception as e:
        logger.error(f"Error getting alerts: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get alerts: {str(e)}"
        )

@router.get("/{alert_id}", response_model=AlertResponse)
async def get_alert(
    alert_id: str,
    db: Session = Depends(get_db)
):
    """Get alert by ID"""
    try:
        alert_service = AlertService(db)
        alert = await alert_service.get_alert(alert_id)
        if not alert:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Alert not found: {alert_id}"
            )
        return alert
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting alert {alert_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get alert: {str(e)}"
        )

@router.put("/{alert_id}", response_model=AlertResponse)
async def update_alert(
    alert_id: str,
    update_data: AlertUpdate,
    db: Session = Depends(get_db)
):
    """Update alert"""
    try:
        alert_service = AlertService(db)
        alert = await alert_service.update_alert(alert_id, update_data)
        if not alert:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Alert not found: {alert_id}"
            )
        return alert
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating alert {alert_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update alert: {str(e)}"
        )

@router.delete("/{alert_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_alert(
    alert_id: str,
    db: Session = Depends(get_db)
):
    """Delete alert"""
    try:
        alert_service = AlertService(db)
        success = await alert_service.delete_alert(alert_id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Alert not found: {alert_id}"
            )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting alert {alert_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete alert: {str(e)}"
        )

@router.post("/bulk", response_model=List[AlertResponse])
async def create_bulk_alerts(
    alerts_data: List[AlertCreate],
    db: Session = Depends(get_db)
):
    """Create multiple alerts in bulk"""
    try:
        alert_service = AlertService(db)
        alerts = await alert_service.bulk_create_alerts(alerts_data)
        return alerts
    except Exception as e:
        logger.error(f"Error creating bulk alerts: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create bulk alerts: {str(e)}"
        )

@router.get("/correlation/{correlation_id}", response_model=List[AlertResponse])
async def get_alerts_by_correlation(
    correlation_id: str,
    db: Session = Depends(get_db)
):
    """Get all alerts for a specific correlation ID"""
    try:
        alert_service = AlertService(db)
        alerts = await alert_service.get_alerts_by_correlation(correlation_id)
        return alerts
    except Exception as e:
        logger.error(f"Error getting alerts for correlation {correlation_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get alerts for correlation: {str(e)}"
        )

@router.post("/correlate", response_model=CorrelationResponse)
async def force_correlate_alerts(
    correlation_request: CorrelationRequest,
    db: Session = Depends(get_db)
):
    """Manually correlate a group of alerts"""
    try:
        correlation_service = CorrelationService(db)
        correlation_id = await correlation_service.force_correlate_alerts(
            correlation_request.alert_ids
        )
        
        if not correlation_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to correlate alerts. Need at least 2 valid alerts."
            )
        
        return CorrelationResponse(
            correlation_id=correlation_id,
            alert_count=len(correlation_request.alert_ids),
            confidence_score=1.0,
            correlation_method="manual",
            created_at=datetime.utcnow()
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error correlating alerts: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to correlate alerts: {str(e)}"
        )

@router.get("/correlations/groups")
async def get_correlation_groups(
    limit: int = Query(100, le=1000),
    db: Session = Depends(get_db)
):
    """Get all correlation groups"""
    try:
        correlation_service = CorrelationService(db)
        groups = await correlation_service.get_correlation_groups(limit)
        return groups
    except Exception as e:
        logger.error(f"Error getting correlation groups: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get correlation groups: {str(e)}"
        )

@router.get("/stats/summary")
async def get_alert_statistics(
    db: Session = Depends(get_db)
):
    """Get alert statistics and metrics"""
    try:
        alert_service = AlertService(db)
        stats = await alert_service.get_alert_statistics()
        return stats
    except Exception as e:
        logger.error(f"Error getting alert statistics: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get alert statistics: {str(e)}"
        )

@router.get("/uncorrelated", response_model=List[AlertResponse])
async def get_uncorrelated_alerts(
    limit: int = Query(100, le=1000),
    db: Session = Depends(get_db)
):
    """Get alerts that haven't been correlated yet"""
    try:
        alert_service = AlertService(db)
        alerts = await alert_service.get_uncorrelated_alerts(limit)
        return alerts
    except Exception as e:
        logger.error(f"Error getting uncorrelated alerts: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get uncorrelated alerts: {str(e)}"
        )
