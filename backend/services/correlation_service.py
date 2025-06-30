from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import uuid
import logging
import json
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np

from app.models.alert import Alert, AlertCorrelation
from app.core.config import settings

logger = logging.getLogger(__name__)

class CorrelationService:
    def __init__(self, db: Session):
        self.db = db
        self.threshold = settings.CORRELATION_THRESHOLD
        self.time_window = settings.CORRELATION_TIME_WINDOW
    
    async def find_correlations(self, new_alert: Alert) -> Optional[Dict[str, Any]]:
        """Find correlations for a new alert"""
        try:
            # Get recent alerts within time window
            time_threshold = datetime.utcnow() - timedelta(seconds=self.time_window)
            recent_alerts = self.db.query(Alert).filter(
                Alert.created_at >= time_threshold,
                Alert.id != new_alert.id,
                Alert.status == "open"
            ).all()
            
            if not recent_alerts:
                logger.info(f"No recent alerts found for correlation with {new_alert.alert_id}")
                return None
            
            # Find best correlation
            best_correlation = await self._find_best_correlation(new_alert, recent_alerts)
            
            if best_correlation:
                # Update or create correlation group
                correlation_result = await self._update_correlation_group(
                    new_alert, best_correlation
                )
                return correlation_result
            
            logger.info(f"No strong correlations found for alert {new_alert.alert_id}")
            return None
            
        except Exception as e:
            logger.error(f"Failed to find correlations for alert {new_alert.alert_id}: {e}")
            return None
    
    async def _find_best_correlation(self, new_alert: Alert, 
                                   candidate_alerts: List[Alert]) -> Optional[Dict[str, Any]]:
        """Find the best correlation among candidate alerts"""
        try:
            best_score = 0.0
            best_match = None
            
            # Prepare new alert features
            new_alert_features = self._extract_alert_features(new_alert)
            
            for candidate in candidate_alerts:
                # Calculate similarity score
                candidate_features = self._extract_alert_features(candidate)
                similarity_score = self._calculate_similarity(
                    new_alert_features, candidate_features
                )
                
                if similarity_score > best_score and similarity_score >= self.threshold:
                    best_score = similarity_score
                    best_match = candidate
            
            if best_match:
                return {
                    "alert": best_match,
                    "score": best_score,
                    "correlation_id": best_match.correlation_id
                }
            
            return None
            
        except Exception as e:
            logger.error(f"Failed to find best correlation: {e}")
            return None
    
    def _extract_alert_features(self, alert: Alert) -> Dict[str, Any]:
        """Extract features from alert for correlation analysis"""
        features = {
            "source": alert.source,
            "severity": alert.severity,
            "alert_type": alert.alert_type,
            "title": alert.title or "",
            "description": alert.description or "",
            "message": alert.message or "",
        }
        
        # Extract features from raw_data
        if alert.raw_data:
            # Add specific fields based on alert type
            if alert.alert_type == "logs":
                features["log_level"] = alert.raw_data.get("level", "")
                features["service"] = alert.raw_data.get("service", "")
            elif alert.alert_type == "metrics":
                features["metric_name"] = alert.raw_data.get("metric", "")
                features["threshold"] = alert.raw_data.get("threshold", "")
            elif alert.alert_type == "traces":
                features["trace_service"] = alert.raw_data.get("service", "")
                features["operation"] = alert.raw_data.get("operation", "")
            
            # Generic fields
            features["host"] = alert.raw_data.get("host", "")
            features["environment"] = alert.raw_data.get("environment", "")
        
        return features
    
    def _calculate_similarity(self, features1: Dict[str, Any], 
                            features2: Dict[str, Any]) -> float:
        """Calculate similarity score between two sets of features"""
        try:
            # Categorical similarity
            categorical_score = self._calculate_categorical_similarity(features1, features2)
            
            # Text similarity
            text_score = self._calculate_text_similarity(features1, features2)
            
            # Weighted combination
            final_score = (categorical_score * 0.6) + (text_score * 0.4)
            
            return final_score
            
        except Exception as e:
            logger.error(f"Failed to calculate similarity: {e}")
            return 0.0
    
    def _calculate_categorical_similarity(self, features1: Dict[str, Any], 
                                        features2: Dict[str, Any]) -> float:
        """Calculate similarity for categorical features"""
        categorical_fields = ["source", "severity", "alert_type", "log_level", 
                            "service", "host", "environment"]
        
        matches = 0
        total = 0
        
        for field in categorical_fields:
            if field in features1 and field in features2:
                total += 1
                if features1[field] == features2[field]:
                    matches += 1
        
        return matches / total if total > 0 else 0.0
    
    def _calculate_text_similarity(self, features1: Dict[str, Any], 
                                 features2: Dict[str, Any]) -> float:
        """Calculate similarity for text features"""
        text_fields = ["title", "description", "message"]
        
        # Combine text features
        text1 = " ".join([str(features1.get(field, "")) for field in text_fields])
        text2 = " ".join([str(features2.get(field, "")) for field in text_fields])
        
        if not text1.strip() or not text2.strip():
            return 0.0
        
        try:
            # Use TF-IDF vectorization and cosine similarity
            vectorizer = TfidfVectorizer(stop_words='english', max_features=1000)
            tfidf_matrix = vectorizer.fit_transform([text1, text2])
            similarity_matrix = cosine_similarity(tfidf_matrix)
            
            return similarity_matrix[0][1]
            
        except Exception as e:
            logger.error(f"Failed to calculate text similarity: {e}")
            return 0.0
    
    async def _update_correlation_group(self, new_alert: Alert, 
                                      correlation_match: Dict[str, Any]) -> Dict[str, Any]:
        """Update or create correlation group"""
        try:
            correlation_id = correlation_match.get("correlation_id")
            
            if not correlation_id:
                # Create new correlation group
                correlation_id = str(uuid.uuid4())
                
                # Update the matched alert with new correlation ID
                matched_alert = correlation_match["alert"]
                matched_alert.correlation_id = correlation_id
                matched_alert.correlation_score = correlation_match["score"]
                
                # Create correlation record
                correlation_record = AlertCorrelation(
                    correlation_id=correlation_id,
                    alert_count=2,
                    confidence_score=correlation_match["score"],
                    correlation_method="similarity",
                    start_time=min(new_alert.created_at, matched_alert.created_at),
                    end_time=max(new_alert.created_at, matched_alert.created_at)
                )
                
                self.db.add(correlation_record)
            else:
                # Update existing correlation group
                correlation_record = self.db.query(AlertCorrelation).filter(
                    AlertCorrelation.correlation_id == correlation_id
                ).first()
                
                if correlation_record:
                    correlation_record.alert_count += 1
                    correlation_record.end_time = max(
                        correlation_record.end_time, new_alert.created_at
                    )
                    # Update confidence score (average)
                    correlation_record.confidence_score = (
                        correlation_record.confidence_score + correlation_match["score"]
                    ) / 2
            
            # Update new alert
            new_alert.correlation_id = correlation_id
            new_alert.correlation_score = correlation_match["score"]
            
            self.db.commit()
            
            logger.info(f"Alert {new_alert.alert_id} added to correlation group {correlation_id}")
            
            return {
                "correlation_id": correlation_id,
                "confidence_score": correlation_match["score"],
                "alert_count": correlation_record.alert_count if correlation_record else 2
            }
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to update correlation group: {e}")
            raise
    
    async def get_correlation_groups(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get all correlation groups with their alerts"""
        try:
            correlations = self.db.query(AlertCorrelation).order_by(
                AlertCorrelation.created_at.desc()
            ).limit(limit).all()
            
            result = []
            for correlation in correlations:
                alerts = self.db.query(Alert).filter(
                    Alert.correlation_id == correlation.correlation_id
                ).all()
                
                result.append({
                    "correlation_id": correlation.correlation_id,
                    "alert_count": correlation.alert_count,
                    "confidence_score": correlation.confidence_score,
                    "correlation_method": correlation.correlation_method,
                    "start_time": correlation.start_time,
                    "end_time": correlation.end_time,
                    "alerts": [alert.alert_id for alert in alerts]
                })
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to get correlation groups: {e}")
            return []
    
    async def force_correlate_alerts(self, alert_ids: List[str]) -> Optional[str]:
        """Manually correlate a group of alerts"""
        try:
            # Get alerts
            alerts = self.db.query(Alert).filter(Alert.alert_id.in_(alert_ids)).all()
            
            if len(alerts) < 2:
                return None
            
            # Generate new correlation ID
            correlation_id = str(uuid.uuid4())
            
            # Update all alerts
            for alert in alerts:
                alert.correlation_id = correlation_id
                alert.correlation_score = 1.0  # Manual correlation
            
            # Create correlation record
            correlation_record = AlertCorrelation(
                correlation_id=correlation_id,
                alert_count=len(alerts),
                confidence_score=1.0,
                correlation_method="manual",
                start_time=min(alert.created_at for alert in alerts),
                end_time=max(alert.created_at for alert in alerts)
            )
            
            self.db.add(correlation_record)
            self.db.commit()
            
            logger.info(f"Manually correlated {len(alerts)} alerts with ID {correlation_id}")
            return correlation_id
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to force correlate alerts: {e}")
            return None
