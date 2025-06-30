from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime

from app.core.database import get_db
from app.models.schemas import (
    RCAResponse, RCAUpdate, RCASearchRequest, RCAGenerateRequest,
    RCAGenerateResponse, FeedbackRequest, FeedbackResponse,
    AccuracyMetrics, PerformanceMetrics
)
from app.services.rca_service import RCAService
from app.utils.logger import setup_logger

logger = setup_logger(__name__)

router = APIRouter()

@router.post("/generate", response_model=RCAGenerateResponse)
async def generate_rca(
    request: RCAGenerateRequest,
    db: Session = Depends(get_db)
):
    """Generate RCA for correlated alerts"""
    try:
        rca_service = RCAService(db)
        result = await rca_service.generate_rca(request)
        return result
    except ValueError as e:
        logger.error(f"Invalid request for RCA generation: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error generating RCA: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate RCA: {str(e)}"
        )

@router.get("/", response_model=List[RCAResponse])
async def get_rcas(
    status: Optional[List[str]] = Query(None),
    priority: Optional[List[str]] = Query(None),
    assigned_to: Optional[str] = Query(None),
    team: Optional[str] = Query(None),
    has_feedback: Optional[bool] = Query(None),
    min_accuracy: Optional[float] = Query(None),
    limit: int = Query(100, le=1000),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db)
):
    """Get RCAs with filtering and pagination"""
    try:
        search_params = RCASearchRequest(
            status=status,
            priority=priority,
            assigned_to=assigned_to,
            team=team,
            has_feedback=has_feedback,
            min_accuracy=min_accuracy,
            limit=limit,
            offset=offset
        )
        
        rca_service = RCAService(db)
        rcas = await rca_service.get_rcas(search_params)
        return rcas
    except Exception as e:
        logger.error(f"Error getting RCAs: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get RCAs: {str(e)}"
        )

@router.get("/{rca_id}", response_model=RCAResponse)
async def get_rca(
    rca_id: str,
    db: Session = Depends(get_db)
):
    """Get RCA by ID"""
    try:
        rca_service = RCAService(db)
        rca = await rca_service.get_rca(rca_id)
        if not rca:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"RCA not found: {rca_id}"
            )
        return rca
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting RCA {rca_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get RCA: {str(e)}"
        )

@router.put("/{rca_id}", response_model=RCAResponse)
async def update_rca(
    rca_id: str,
    update_data: RCAUpdate,
    db: Session = Depends(get_db)
):
    """Update RCA"""
    try:
        rca_service = RCAService(db)
        rca = await rca_service.update_rca(rca_id, update_data)
        if not rca:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"RCA not found: {rca_id}"
            )
        return rca
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating RCA {rca_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update RCA: {str(e)}"
        )

@router.delete("/{rca_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_rca(
    rca_id: str,
    db: Session = Depends(get_db)
):
    """Delete RCA"""
    try:
        rca_service = RCAService(db)
        success = await rca_service.delete_rca(rca_id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"RCA not found: {rca_id}"
            )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting RCA {rca_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete RCA: {str(e)}"
        )

@router.put("/{rca_id}/status")
async def update_rca_status(
    rca_id: str,
    status: str,
    assigned_to: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Update RCA status"""
    try:
        valid_statuses = ["open", "in_progress", "closed"]
        if status not in valid_statuses:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid status. Must be one of: {valid_statuses}"
            )
        
        update_data = RCAUpdate(status=status)
        if assigned_to:
            update_data.assigned_to = assigned_to
        
        rca_service = RCAService(db)
        rca = await rca_service.update_rca(rca_id, update_data)
        if not rca:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"RCA not found: {rca_id}"
            )
        
        return {"message": f"RCA status updated to {status}", "rca_id": rca_id}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating RCA status {rca_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update RCA status: {str(e)}"
        )

@router.post("/{rca_id}/feedback", response_model=FeedbackResponse)
async def submit_feedback(
    rca_id: str,
    feedback: FeedbackRequest,
    db: Session = Depends(get_db)
):
    """Submit feedback for RCA accuracy"""
    try:
        # Ensure the rca_id in the path matches the request
        feedback.rca_id = rca_id
        
        rca_service = RCAService(db)
        result = await rca_service.submit_feedback(feedback)
        return result
    except ValueError as e:
        logger.error(f"Invalid feedback request for RCA {rca_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error submitting feedback for RCA {rca_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to submit feedback: {str(e)}"
        )

@router.get("/stats/summary")
async def get_rca_statistics(
    db: Session = Depends(get_db)
):
    """Get RCA statistics and metrics"""
    try:
        rca_service = RCAService(db)
        stats = await rca_service.get_rca_statistics()
        return stats
    except Exception as e:
        logger.error(f"Error getting RCA statistics: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get RCA statistics: {str(e)}"
        )

@router.get("/stats/accuracy", response_model=AccuracyMetrics)
async def get_accuracy_metrics(
    days: int = Query(30, ge=1, le=365),
    db: Session = Depends(get_db)
):
    """Get RCA accuracy metrics"""
    try:
        # Calculate accuracy metrics for the specified period
        from datetime import timedelta
        from app.models.rca import RCA
        
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)
        
        # Get RCAs with feedback in the specified period
        rcas_with_feedback = db.query(RCA).filter(
            RCA.created_at >= start_date,
            RCA.created_at <= end_date,
            RCA.accuracy_rating.isnot(None)
        ).all()
        
        total_rcas = db.query(RCA).filter(
            RCA.created_at >= start_date,
            RCA.created_at <= end_date
        ).count()
        
        avg_accuracy = 0.0
        if rcas_with_feedback:
            total_accuracy = sum(rca.accuracy_rating for rca in rcas_with_feedback)
            avg_accuracy = total_accuracy / len(rcas_with_feedback)
        
        # Generate accuracy trend (weekly buckets)
        accuracy_trend = []
        weeks = min(days // 7, 12)  # Max 12 weeks
        for i in range(weeks):
            week_start = start_date + timedelta(weeks=i)
            week_end = week_start + timedelta(weeks=1)
            
            week_rcas = [rca for rca in rcas_with_feedback 
                        if week_start <= rca.created_at < week_end]
            
            week_avg = 0.0
            if week_rcas:
                week_total = sum(rca.accuracy_rating for rca in week_rcas)
                week_avg = week_total / len(week_rcas)
            
            accuracy_trend.append({
                "week": week_start.strftime("%Y-%m-%d"),
                "accuracy": round(week_avg, 2),
                "count": len(week_rcas)
            })
        
        return AccuracyMetrics(
            total_rcas=total_rcas,
            with_feedback=len(rcas_with_feedback),
            average_accuracy=round(avg_accuracy, 2),
            accuracy_trend=accuracy_trend
        )
        
    except Exception as e:
        logger.error(f"Error getting accuracy metrics: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get accuracy metrics: {str(e)}"
        )

@router.get("/stats/performance", response_model=PerformanceMetrics)
async def get_performance_metrics(
    db: Session = Depends(get_db)
):
    """Get system performance metrics"""
    try:
        from app.models.rca import RCA
        from app.models.alert import Alert
        from app.services.llm_service import LLMService
        
        # Calculate metrics
        resolved_rcas = db.query(RCA).filter(
            RCA.resolution_time.isnot(None)
        ).all()
        
        avg_resolution_time = 0.0
        if resolved_rcas:
            total_time = sum(rca.resolution_time for rca in resolved_rcas)
            avg_resolution_time = total_time / len(resolved_rcas)
        
        total_alerts = db.query(Alert).count()
        
        # Estimate correlation accuracy (simplified)
        correlated_alerts = db.query(Alert).filter(
            Alert.correlation_id.isnot(None)
        ).count()
        correlation_accuracy = (correlated_alerts / total_alerts * 100) if total_alerts > 0 else 0
        
        # Test LLM connection
        llm_service = LLMService()
        system_uptime = 100.0  # Simplified - would be actual uptime calculation
        try:
            llm_connected = await llm_service.test_connection()
            if not llm_connected:
                system_uptime = 85.0  # Reduced if LLM not available
        except Exception:
            system_uptime = 85.0
        
        return PerformanceMetrics(
            average_resolution_time=round(avg_resolution_time, 2),
            total_alerts_processed=total_alerts,
            correlation_accuracy=round(correlation_accuracy, 2),
            system_uptime=round(system_uptime, 2)
        )
        
    except Exception as e:
        logger.error(f"Error getting performance metrics: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get performance metrics: {str(e)}"
        )
