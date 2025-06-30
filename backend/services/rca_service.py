from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
import uuid
import logging
import asyncio

from app.models.rca import RCA, RCAAccuracy
from app.models.alert import Alert
from app.models.schemas import (
    RCACreate, RCAUpdate, RCASearchRequest, RCAGenerateRequest,
    FeedbackRequest
)
from app.services.llm_service import LLMService
from app.services.alert_service import AlertService
from app.core.vector_store import get_vector_store

logger = logging.getLogger(__name__)

class RCAService:
    def __init__(self, db: Session):
        self.db = db
        self.llm_service = LLMService()
        self.alert_service = AlertService(db)
        self.vector_store = get_vector_store()
    
    async def generate_rca(self, request: RCAGenerateRequest) -> Dict[str, Any]:
        """Generate RCA for correlated alerts"""
        try:
            # Get alerts for correlation ID
            alerts = await self.alert_service.get_alerts_by_correlation(
                request.correlation_id
            )
            
            if not alerts:
                raise ValueError(f"No alerts found for correlation ID: {request.correlation_id}")
            
            # Generate RCA ID
            rca_id = str(uuid.uuid4())
            
            # Create initial RCA record
            db_rca = RCA(
                rca_id=rca_id,
                correlation_id=request.correlation_id,
                title=request.title or f"RCA for {len(alerts)} correlated alerts",
                priority=request.priority,
                status="in_progress",
                assigned_to=request.assigned_to,
                summary="RCA generation in progress..."
            )
            
            self.db.add(db_rca)
            self.db.commit()
            self.db.refresh(db_rca)
            
            # Generate RCA analysis asynchronously
            asyncio.create_task(
                self._generate_rca_analysis(db_rca, alerts, request.use_historical_context)
            )
            
            logger.info(f"RCA generation started for correlation {request.correlation_id}")
            
            return {
                "rca_id": rca_id,
                "status": "in_progress",
                "message": "RCA generation started",
                "estimated_completion_time": 120  # seconds
            }
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to start RCA generation: {e}")
            raise
    
    async def _generate_rca_analysis(self, rca: RCA, alerts: List[Alert], 
                                   use_historical_context: bool):
        """Generate the actual RCA analysis"""
        try:
            # Generate analysis using LLM
            analysis = await self.llm_service.generate_rca(
                alerts, use_historical_context
            )
            
            # Update RCA record with analysis
            rca.root_cause = analysis.get("root_cause")
            rca.solution = analysis.get("solution")
            rca.impact_analysis = analysis.get("impact_analysis")
            rca.confidence_score = analysis.get("confidence_score")
            rca.llm_analysis = analysis
            rca.affected_systems = analysis.get("affected_systems", [])
            rca.business_impact = analysis.get("business_impact")
            rca.status = "open"
            
            # Generate summary
            summary = await self.llm_service.generate_summary(analysis)
            rca.summary = summary
            
            self.db.commit()
            
            # Store in vector database for future reference
            await self._store_rca_in_vector_db(rca, alerts)
            
            logger.info(f"RCA analysis completed for {rca.rca_id}")
            
        except Exception as e:
            logger.error(f"Failed to generate RCA analysis for {rca.rca_id}: {e}")
            # Update RCA with error status
            rca.status = "open"
            rca.summary = f"RCA generation failed: {str(e)}"
            rca.root_cause = "Automatic analysis failed"
            rca.solution = "Manual analysis required"
            rca.confidence_score = 0.0
            self.db.commit()
    
    async def get_rca(self, rca_id: str) -> Optional[RCA]:
        """Get RCA by ID"""
        return self.db.query(RCA).filter(RCA.rca_id == rca_id).first()
    
    async def get_rcas(self, search_params: RCASearchRequest) -> List[RCA]:
        """Get RCAs with filtering and pagination"""
        try:
            query = self.db.query(RCA)
            
            # Apply filters
            if search_params.status:
                query = query.filter(RCA.status.in_(search_params.status))
            
            if search_params.priority:
                query = query.filter(RCA.priority.in_(search_params.priority))
            
            if search_params.assigned_to:
                query = query.filter(RCA.assigned_to == search_params.assigned_to)
            
            if search_params.team:
                query = query.filter(RCA.team == search_params.team)
            
            if search_params.start_date:
                query = query.filter(RCA.created_at >= search_params.start_date)
            
            if search_params.end_date:
                query = query.filter(RCA.created_at <= search_params.end_date)
            
            if search_params.has_feedback is not None:
                if search_params.has_feedback:
                    query = query.filter(RCA.user_feedback.isnot(None))
                else:
                    query = query.filter(RCA.user_feedback.is_(None))
            
            if search_params.min_accuracy:
                query = query.filter(RCA.accuracy_rating >= search_params.min_accuracy)
            
            # Apply pagination
            query = query.offset(search_params.offset).limit(search_params.limit)
            
            # Order by creation time (newest first)
            query = query.order_by(RCA.created_at.desc())
            
            return query.all()
            
        except Exception as e:
            logger.error(f"Failed to get RCAs: {e}")
            return []
    
    async def update_rca(self, rca_id: str, update_data: RCAUpdate) -> Optional[RCA]:
        """Update RCA"""
        try:
            db_rca = await self.get_rca(rca_id)
            if not db_rca:
                return None
            
            # Update fields
            for field, value in update_data.dict(exclude_unset=True).items():
                if field == "status" and value == "closed":
                    db_rca.resolved_at = datetime.utcnow()
                    # Calculate resolution time
                    if db_rca.created_at:
                        resolution_time = (datetime.utcnow() - db_rca.created_at).total_seconds() / 60
                        db_rca.resolution_time = int(resolution_time)
                
                setattr(db_rca, field, value)
            
            db_rca.updated_at = datetime.utcnow()
            
            self.db.commit()
            self.db.refresh(db_rca)
            
            logger.info(f"RCA updated successfully: {rca_id}")
            return db_rca
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to update RCA {rca_id}: {e}")
            raise
    
    async def submit_feedback(self, feedback_request: FeedbackRequest) -> Dict[str, Any]:
        """Submit feedback for RCA accuracy"""
        try:
            db_rca = await self.get_rca(feedback_request.rca_id)
            if not db_rca:
                raise ValueError(f"RCA not found: {feedback_request.rca_id}")
            
            # Update RCA with feedback
            db_rca.is_accurate = feedback_request.is_accurate
            db_rca.accuracy_rating = feedback_request.accuracy_rating
            
            # Store feedback details
            feedback_data = {
                "is_accurate": feedback_request.is_accurate,
                "accuracy_rating": feedback_request.accuracy_rating,
                "feedback_text": feedback_request.feedback_text,
                "user_id": feedback_request.user_id,
                "user_role": feedback_request.user_role,
                "timestamp": datetime.utcnow().isoformat()
            }
            
            # Append to existing feedback or create new
            if db_rca.user_feedback:
                if isinstance(db_rca.user_feedback, list):
                    db_rca.user_feedback.append(feedback_data)
                else:
                    db_rca.user_feedback = [db_rca.user_feedback, feedback_data]
            else:
                db_rca.user_feedback = feedback_data
            
            # Create accuracy record
            accuracy_record = RCAAccuracy(
                rca_id=feedback_request.rca_id,
                predicted_accuracy=db_rca.confidence_score or 0.5,
                actual_accuracy=feedback_request.accuracy_rating,
                feedback_type="positive" if feedback_request.is_accurate else "negative",
                feedback_text=feedback_request.feedback_text,
                user_id=feedback_request.user_id,
                user_role=feedback_request.user_role
            )
            
            self.db.add(accuracy_record)
            self.db.commit()
            
            # If feedback suggests improvement, generate improved analysis
            improved_analysis = None
            if not feedback_request.is_accurate and feedback_request.feedback_text:
                try:
                    improved_analysis = await self.llm_service.improve_analysis(
                        db_rca.llm_analysis or {}, feedback_request.feedback_text
                    )
                except Exception as e:
                    logger.error(f"Failed to generate improved analysis: {e}")
            
            logger.info(f"Feedback submitted for RCA {feedback_request.rca_id}")
            
            return {
                "message": "Feedback submitted successfully",
                "updated_accuracy": feedback_request.accuracy_rating,
                "improved_analysis_available": improved_analysis is not None
            }
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to submit feedback: {e}")
            raise
    
    async def get_rca_statistics(self) -> Dict[str, Any]:
        """Get RCA statistics and metrics"""
        try:
            total_rcas = self.db.query(RCA).count()
            open_rcas = self.db.query(RCA).filter(RCA.status == "open").count()
            in_progress_rcas = self.db.query(RCA).filter(RCA.status == "in_progress").count()
            closed_rcas = self.db.query(RCA).filter(RCA.status == "closed").count()
            
            # Accuracy metrics
            rcas_with_feedback = self.db.query(RCA).filter(
                RCA.accuracy_rating.isnot(None)
            ).all()
            
            avg_accuracy = 0.0
            if rcas_with_feedback:
                total_accuracy = sum(rca.accuracy_rating for rca in rcas_with_feedback)
                avg_accuracy = total_accuracy / len(rcas_with_feedback)
            
            # Resolution time metrics
            resolved_rcas = self.db.query(RCA).filter(
                RCA.resolution_time.isnot(None)
            ).all()
            
            avg_resolution_time = 0.0
            if resolved_rcas:
                total_time = sum(rca.resolution_time for rca in resolved_rcas)
                avg_resolution_time = total_time / len(resolved_rcas)
            
            # Recent activity (last 24 hours)
            recent_threshold = datetime.utcnow() - timedelta(hours=24)
            recent_rcas = self.db.query(RCA).filter(
                RCA.created_at >= recent_threshold
            ).count()
            
            return {
                "total_rcas": total_rcas,
                "open_rcas": open_rcas,
                "in_progress_rcas": in_progress_rcas,
                "closed_rcas": closed_rcas,
                "rcas_with_feedback": len(rcas_with_feedback),
                "average_accuracy": round(avg_accuracy, 2),
                "average_resolution_time": round(avg_resolution_time, 2),
                "recent_rcas": recent_rcas
            }
            
        except Exception as e:
            logger.error(f"Failed to get RCA statistics: {e}")
            return {}
    
    async def _store_rca_in_vector_db(self, rca: RCA, alerts: List[Alert]):
        """Store RCA in vector database for future similarity matching"""
        try:
            # Prepare alert patterns
            alert_patterns = []
            for alert in alerts:
                pattern = f"{alert.source} {alert.alert_type} {alert.severity} {alert.title}"
                alert_patterns.append(pattern)
            
            # Prepare RCA data
            rca_data = {
                "root_cause": rca.root_cause,
                "solution": rca.solution,
                "impact": rca.impact_analysis,
                "status": rca.status,
                "confidence_score": rca.confidence_score
            }
            
            # Store in vector database
            await self.vector_store.store_rca(rca.rca_id, rca_data, alert_patterns)
            
            logger.info(f"RCA {rca.rca_id} stored in vector database")
            
        except Exception as e:
            logger.error(f"Failed to store RCA in vector database: {e}")
    
    async def delete_rca(self, rca_id: str) -> bool:
        """Delete RCA"""
        try:
            db_rca = await self.get_rca(rca_id)
            if not db_rca:
                return False
            
            # Delete related accuracy records
            self.db.query(RCAAccuracy).filter(
                RCAAccuracy.rca_id == rca_id
            ).delete()
            
            # Delete RCA
            self.db.delete(db_rca)
            self.db.commit()
            
            logger.info(f"RCA deleted successfully: {rca_id}")
            return True
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to delete RCA {rca_id}: {e}")
            return False
