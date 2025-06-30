from sqlalchemy import Column, Integer, String, DateTime, Text, JSON, Float, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base

class Alert(Base):
    __tablename__ = "alerts"
    
    id = Column(Integer, primary_key=True, index=True)
    alert_id = Column(String, unique=True, index=True)
    source = Column(String, index=True)  # monitoring tool source
    severity = Column(String, index=True)
    status = Column(String, default="open", index=True)
    
    # Alert content
    title = Column(String)
    description = Column(Text)
    message = Column(Text)
    
    # Alert data (logs, traces, metrics, events)
    alert_type = Column(String)  # logs, traces, metrics, events
    raw_data = Column(JSON)
    
    # Correlation
    correlation_id = Column(String, index=True, nullable=True)
    correlation_score = Column(Float, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    alert_timestamp = Column(DateTime(timezone=True))
    
    # Relationships
    rca_analyses = relationship("RCA", back_populates="alerts")

class AlertCorrelation(Base):
    __tablename__ = "alert_correlations"
    
    id = Column(Integer, primary_key=True, index=True)
    correlation_id = Column(String, unique=True, index=True)
    
    # Correlation metadata
    alert_count = Column(Integer)
    confidence_score = Column(Float)
    correlation_method = Column(String)
    
    # Time window
    start_time = Column(DateTime(timezone=True))
    end_time = Column(DateTime(timezone=True))
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

class AlertPattern(Base):
    __tablename__ = "alert_patterns"
    
    id = Column(Integer, primary_key=True, index=True)
    pattern_id = Column(String, unique=True, index=True)
    
    # Pattern details
    pattern_name = Column(String)
    pattern_type = Column(String)
    pattern_data = Column(JSON)
    
    # Pattern statistics
    occurrence_count = Column(Integer, default=0)
    last_seen = Column(DateTime(timezone=True))
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
