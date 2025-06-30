from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from datetime import datetime
from enum import Enum

# Enums
class AlertStatus(str, Enum):
    OPEN = "open"
    ACKNOWLEDGED = "acknowledged"
    RESOLVED = "resolved"

class AlertSeverity(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class AlertType(str, Enum):
    LOGS = "logs"
    TRACES = "traces"
    METRICS = "metrics"
    EVENTS = "events"

class RCAStatus(str, Enum):
    OPEN = "open"
    IN_PROGRESS = "in_progress"
    CLOSED = "closed"

class RCAPriority(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

# Alert Schemas
class AlertBase(BaseModel):
    alert_id: str
    source: str
    severity: AlertSeverity
    title: str
    description: Optional[str] = None
    message: str
    alert_type: AlertType
    raw_data: Dict[str, Any]
    alert_timestamp: Optional[datetime] = None

class AlertCreate(AlertBase):
    pass

class AlertUpdate(BaseModel):
    status: Optional[AlertStatus] = None
    severity: Optional[AlertSeverity] = None
    description: Optional[str] = None
    correlation_id: Optional[str] = None

class AlertResponse(AlertBase):
    id: int
    status: AlertStatus
    correlation_id: Optional[str] = None
    correlation_score: Optional[float] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True

# RCA Schemas
class RCABase(BaseModel):
    title: str
    correlation_id: str
    priority: RCAPriority = RCAPriority.MEDIUM
    summary: Optional[str] = None
    assigned_to: Optional[str] = None
    team: Optional[str] = None

class RCACreate(RCABase):
    pass

class RCAUpdate(BaseModel):
    status: Optional[RCAStatus] = None
    priority: Optional[RCAPriority] = None
    title: Optional[str] = None
    summary: Optional[str] = None
    root_cause: Optional[str] = None
    solution: Optional[str] = None
    impact_analysis: Optional[str] = None
    assigned_to: Optional[str] = None
    team: Optional[str] = None
    user_feedback: Optional[Dict[str, Any]] = None
    accuracy_rating: Optional[float] = None

class RCAResponse(RCABase):
    id: int
    rca_id: str
    status: RCAStatus
    root_cause: Optional[str] = None
    solution: Optional[str] = None
    impact_analysis: Optional[str] = None
    confidence_score: Optional[float] = None
    accuracy_rating: Optional[float] = None
    is_accurate: Optional[bool] = None
    resolution_time: Optional[int] = None
    affected_systems: Optional[List[str]] = None
    business_impact: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    resolved_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True

# RCA Generation Request
class RCAGenerateRequest(BaseModel):
    correlation_id: str
    title: Optional[str] = None
    priority: RCAPriority = RCAPriority.MEDIUM
    use_historical_context: bool = True
    assigned_to: Optional[str] = None

class RCAGenerateResponse(BaseModel):
    rca_id: str
    status: str
    message: str
    estimated_completion_time: Optional[int] = None

# Alert Correlation Schemas
class CorrelationRequest(BaseModel):
    alert_ids: List[str]
    correlation_method: Optional[str] = "similarity"
    threshold: Optional[float] = 0.7

class CorrelationResponse(BaseModel):
    correlation_id: str
    alert_count: int
    confidence_score: float
    correlation_method: str
    created_at: datetime

# Search and Filter Schemas
class AlertSearchRequest(BaseModel):
    status: Optional[List[AlertStatus]] = None
    severity: Optional[List[AlertSeverity]] = None
    source: Optional[List[str]] = None
    alert_type: Optional[List[AlertType]] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    correlation_id: Optional[str] = None
    limit: int = Field(default=100, le=1000)
    offset: int = Field(default=0, ge=0)

class RCASearchRequest(BaseModel):
    status: Optional[List[RCAStatus]] = None
    priority: Optional[List[RCAPriority]] = None
    assigned_to: Optional[str] = None
    team: Optional[str] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    has_feedback: Optional[bool] = None
    min_accuracy: Optional[float] = None
    limit: int = Field(default=100, le=1000)
    offset: int = Field(default=0, ge=0)

# Analytics Schemas
class AccuracyMetrics(BaseModel):
    total_rcas: int
    with_feedback: int
    average_accuracy: float
    accuracy_trend: List[Dict[str, Any]]

class PerformanceMetrics(BaseModel):
    average_resolution_time: float
    total_alerts_processed: int
    correlation_accuracy: float
    system_uptime: float

# Feedback Schemas
class FeedbackRequest(BaseModel):
    rca_id: str
    is_accurate: bool
    accuracy_rating: float = Field(ge=0.0, le=1.0)
    feedback_text: Optional[str] = None
    corrected_analysis: Optional[str] = None
    user_id: Optional[str] = None
    user_role: Optional[str] = None

class FeedbackResponse(BaseModel):
    message: str
    updated_accuracy: Optional[float] = None
