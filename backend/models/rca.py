from sqlalchemy import Column, Integer, String, DateTime, Text, JSON, Float, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base

class RCA(Base):
    __tablename__ = "rca_analyses"
    
    id = Column(Integer, primary_key=True, index=True)
    rca_id = Column(String, unique=True, index=True)
    correlation_id = Column(String, index=True)
    
    # RCA Status
    status = Column(String, default="in_progress", index=True)  # open, in_progress, closed
    priority = Column(String, default="medium", index=True)  # low, medium, high, critical
    
    # RCA Content
    title = Column(String)
    summary = Column(Text)
    root_cause = Column(Text)
    solution = Column(Text)
    impact_analysis = Column(Text)
    
    # AI Analysis
    llm_analysis = Column(JSON)
    confidence_score = Column(Float)
    historical_context = Column(JSON)
    
    # Feedback and Accuracy
    user_feedback = Column(JSON, nullable=True)
    accuracy_rating = Column(Float, nullable=True)  # 0.0 to 1.0
    is_accurate = Column(Boolean, nullable=True)
    
    # Metrics
    resolution_time = Column(Integer, nullable=True)  # minutes
    affected_systems = Column(JSON)
    business_impact = Column(String)
    
    # Assignee
    assigned_to = Column(String, nullable=True)
    team = Column(String, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    resolved_at = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    alerts = relationship("Alert", back_populates="rca_analyses")
    
class RCAAccuracy(Base):
    __tablename__ = "rca_accuracy"
    
    id = Column(Integer, primary_key=True, index=True)
    rca_id = Column(String, ForeignKey("rca_analyses.rca_id"), index=True)
    
    # Accuracy metrics
    predicted_accuracy = Column(Float)
    actual_accuracy = Column(Float, nullable=True)
    feedback_type = Column(String)  # positive, negative, neutral
    
    # Feedback details
    feedback_text = Column(Text, nullable=True)
    corrected_analysis = Column(Text, nullable=True)
    
    # User information
    user_id = Column(String, nullable=True)
    user_role = Column(String, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

class RCATemplate(Base):
    __tablename__ = "rca_templates"
    
    id = Column(Integer, primary_key=True, index=True)
    template_id = Column(String, unique=True, index=True)
    
    # Template details
    name = Column(String)
    description = Column(Text)
    category = Column(String)
    
    # Template content
    template_data = Column(JSON)
    prompt_template = Column(Text)
    
    # Usage statistics
    usage_count = Column(Integer, default=0)
    success_rate = Column(Float, default=0.0)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
