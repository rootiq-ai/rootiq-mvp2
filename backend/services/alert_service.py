from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
import uuid
import logging

from app.models.alert import Alert, AlertCorrelation
from app.models.schemas import AlertCreate, AlertUpdate, AlertSearchRequest
from app.services.correlation_service import CorrelationService

logger = logging.getLogger(__name__)

class AlertService:
    def __init__(self, db: Session):
        self.db = db
        self.correlation_service = CorrelationService(db)
    
    async def create_alert(self, alert_data: AlertCreate) -> Alert:
        """Create a new alert and trigger correlation analysis"""
        try:
            # Generate unique alert ID if not provided
            if not alert_data.alert_id:
                alert_data.alert_id = str(uuid.uuid4())
            
            # Create alert instance
            db_alert = Alert(
                alert_id=alert_data.alert_id,
                source=alert_data.source,
                severity=alert_data.severity,
                title=alert_data.title,
                description=alert_data.description,
                message=alert_data.message,
                alert_type=alert_data.alert_type,
                raw_data=alert_data.raw_data,
                alert_timestamp=alert_data.alert_timestamp or datetime.utcnow(),
                status="open"
            )
            
            self.db.add(db_alert)
            self.db.commit()
            self.db.refresh(db_alert)
            
            # Trigger correlation analysis
            await self._trigger_correlation(db_alert)
            
            logger.info(f"Alert created successfully: {db_alert.alert_id}")
            return db_alert
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to create alert: {e}")
            raise
    
    async def get_alert(self, alert_id: str) -> Optional[Alert]:
        """Get alert by ID"""
        return self.db.query(Alert).filter(Alert.alert_id == alert_id).first()
    
    async def get_alerts(self, search_params: AlertSearchRequest) -> List[Alert]:
        """Get alerts with filtering and pagination"""
        try:
            query = self.db.query(Alert)
            
            # Apply filters
            if search_params.status:
                query = query.filter(Alert.status.in_(search_params.status))
            
            if search_params.severity:
                query = query.filter(Alert.severity.in_(search_params.severity))
            
            if search_params.source:
                query = query.filter(Alert.source.in_(search_params.source))
            
            if search_params.alert_type:
                query = query.filter(Alert.alert_type.in_(search_params.alert_type))
            
            if search_params.correlation_id:
                query = query.filter(Alert.correlation_id == search_params.correlation_id)
            
            if search_params.start_date:
                query = query.filter(Alert.created_at >= search_params.start_date)
            
            if search_params.end_date:
                query = query.filter(Alert.created_at <= search_params.end_date)
            
            # Apply pagination
            query = query.offset(search_params.offset).limit(search_params.limit)
            
            # Order by creation time (newest first)
            query = query.order_by(Alert.created_at.desc())
            
            return query.all()
            
        except Exception as e:
            logger.error(f"Failed to get alerts: {e}")
            return []
    
    async def update_alert(self, alert_id: str, update_data: AlertUpdate) -> Optional[Alert]:
        """Update alert"""
        try:
            db_alert = await self.get_alert(alert_id)
            if not db_alert:
                return None
            
            # Update fields
            for field, value in update_data.dict(exclude_unset=True).items():
                setattr(db_alert, field, value)
            
            db_alert.updated_at = datetime.utcnow()
            
            self.db.commit()
            self.db.refresh(db_alert)
            
            logger.info(f"Alert updated successfully: {alert_id}")
            return db_alert
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to update alert {alert_id}: {e}")
            raise
    
    async def delete_alert(self, alert_id: str) -> bool:
        """Delete alert"""
        try:
            db_alert = await self.get_alert(alert_id)
            if not db_alert:
                return False
            
            self.db.delete(db_alert)
            self.db.commit()
            
            logger.info(f"Alert deleted successfully: {alert_id}")
            return True
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to delete alert {alert_id}: {e}")
            return False
    
    async def get_alerts_by_correlation(self, correlation_id: str) -> List[Alert]:
        """Get all alerts for a specific correlation ID"""
        return self.db.query(Alert).filter(
            Alert.correlation_id == correlation_id
        ).order_by(Alert.created_at.desc()).all()
    
    async def get_alert_statistics(self) -> Dict[str, Any]:
        """Get alert statistics"""
        try:
            total_alerts = self.db.query(Alert).count()
            open_alerts = self.db.query(Alert).filter(Alert.status == "open").count()
            resolved_alerts = self.db.query(Alert).filter(Alert.status == "resolved").count()
            
            # Recent alerts (last 24 hours)
            recent_threshold = datetime.utcnow() - timedelta(hours=24)
            recent_alerts = self.db.query(Alert).filter(
                Alert.created_at >= recent_threshold
            ).count()
            
            # Severity distribution
            severity_stats = {}
            for severity in ["low", "medium", "high", "critical"]:
                count = self.db.query(Alert).filter(Alert.severity == severity).count()
                severity_stats[severity] = count
            
            # Source distribution
            source_stats = self.db.query(Alert.source, self.db.func.count(Alert.id)).group_by(
                Alert.source
            ).all()
            
            return {
                "total_alerts": total_alerts,
                "open_alerts": open_alerts,
                "resolved_alerts": resolved_alerts,
                "recent_alerts": recent_alerts,
                "severity_distribution": severity_stats,
                "source_distribution": dict(source_stats)
            }
            
        except Exception as e:
            logger.error(f"Failed to get alert statistics: {e}")
            return {}
    
    async def _trigger_correlation(self, alert: Alert):
        """Trigger correlation analysis for new alert"""
        try:
            # Find potential correlations
            correlation_result = await self.correlation_service.find_correlations(alert)
            
            if correlation_result:
                # Update alert with correlation info
                alert.correlation_id = correlation_result["correlation_id"]
                alert.correlation_score = correlation_result["confidence_score"]
                self.db.commit()
                
                logger.info(f"Alert {alert.alert_id} correlated with ID: {correlation_result['correlation_id']}")
            
        except Exception as e:
            logger.error(f"Failed to trigger correlation for alert {alert.alert_id}: {e}")
    
    async def bulk_create_alerts(self, alerts_data: List[AlertCreate]) -> List[Alert]:
        """Create multiple alerts in bulk"""
        try:
            created_alerts = []
            
            for alert_data in alerts_data:
                alert = await self.create_alert(alert_data)
                created_alerts.append(alert)
            
            logger.info(f"Bulk created {len(created_alerts)} alerts")
            return created_alerts
            
        except Exception as e:
            logger.error(f"Failed to bulk create alerts: {e}")
            raise
    
    async def get_uncorrelated_alerts(self, limit: int = 100) -> List[Alert]:
        """Get alerts that haven't been correlated yet"""
        return self.db.query(Alert).filter(
            Alert.correlation_id.is_(None),
            Alert.status == "open"
        ).order_by(Alert.created_at.desc()).limit(limit).all()
