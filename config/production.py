"""
Production Configuration for AI Observability RCA
This file contains production-specific settings and optimizations.
"""

import os
from typing import List

class ProductionConfig:
    """Production configuration settings"""
    
    # Database Configuration
    DATABASE_URL = os.getenv(
        "DATABASE_URL", 
        "postgresql://ai_user:secure_password@db-server:5432/ai_observability_prod"
    )
    DB_POOL_SIZE = int(os.getenv("DB_POOL_SIZE", "20"))
    DB_MAX_OVERFLOW = int(os.getenv("DB_MAX_OVERFLOW", "30"))
    DB_POOL_TIMEOUT = int(os.getenv("DB_POOL_TIMEOUT", "30"))
    
    # Redis Configuration (for caching and sessions)
    REDIS_URL = os.getenv("REDIS_URL", "redis://redis-server:6379/0")
    REDIS_PASSWORD = os.getenv("REDIS_PASSWORD", "")
    
    # Ollama Configuration
    OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://ollama-server:11434")
    OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3")
    OLLAMA_TIMEOUT = int(os.getenv("OLLAMA_TIMEOUT", "300"))  # 5 minutes
    OLLAMA_RETRIES = int(os.getenv("OLLAMA_RETRIES", "3"))
    
    # ChromaDB Configuration
    CHROMA_DB_PATH = os.getenv("CHROMA_DB_PATH", "/data/chroma_db")
    CHROMA_DB_HOST = os.getenv("CHROMA_DB_HOST", "")  # For server mode
    CHROMA_DB_PORT = int(os.getenv("CHROMA_DB_PORT", "8000"))
    
    # API Configuration
    API_HOST = os.getenv("API_HOST", "0.0.0.0")
    API_PORT = int(os.getenv("API_PORT", "8000"))
    DEBUG = os.getenv("DEBUG", "False").lower() == "true"
    
    # Security Configuration
    SECRET_KEY = os.getenv("SECRET_KEY", "your-super-secret-key-change-in-production")
    API_KEY_REQUIRED = os.getenv("API_KEY_REQUIRED", "True").lower() == "true"
    VALID_API_KEYS = os.getenv("VALID_API_KEYS", "").split(",") if os.getenv("VALID_API_KEYS") else []
    
    # CORS Configuration
    ALLOWED_ORIGINS = os.getenv(
        "ALLOWED_ORIGINS", 
        "https://rca.yourdomain.com,https://monitoring.yourdomain.com"
    ).split(",")
    
    # Rate Limiting
    RATE_LIMIT_ENABLED = os.getenv("RATE_LIMIT_ENABLED", "True").lower() == "true"
    RATE_LIMIT_REQUESTS_PER_MINUTE = int(os.getenv("RATE_LIMIT_REQUESTS_PER_MINUTE", "100"))
    RATE_LIMIT_BURST_SIZE = int(os.getenv("RATE_LIMIT_BURST_SIZE", "20"))
    
    # Logging Configuration
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
    LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    LOG_FILE = os.getenv("LOG_FILE", "/var/log/ai_observability/app.log")
    LOG_MAX_SIZE = int(os.getenv("LOG_MAX_SIZE", "10485760"))  # 10MB
    LOG_BACKUP_COUNT = int(os.getenv("LOG_BACKUP_COUNT", "5"))
    
    # Monitoring and Observability
    ENABLE_METRICS = os.getenv("ENABLE_METRICS", "True").lower() == "true"
    METRICS_PORT = int(os.getenv("METRICS_PORT", "9090"))
    HEALTH_CHECK_TIMEOUT = int(os.getenv("HEALTH_CHECK_TIMEOUT", "30"))
    
    # Performance Tuning
    WORKER_PROCESSES = int(os.getenv("WORKER_PROCESSES", "4"))
    WORKER_CONNECTIONS = int(os.getenv("WORKER_CONNECTIONS", "1000"))
    KEEP_ALIVE = int(os.getenv("KEEP_ALIVE", "2"))
    
    # Alert Processing Configuration
    CORRELATION_THRESHOLD = float(os.getenv("CORRELATION_THRESHOLD", "0.75"))
    CORRELATION_TIME_WINDOW = int(os.getenv("CORRELATION_TIME_WINDOW", "300"))  # 5 minutes
    MAX_ALERTS_PER_CORRELATION = int(os.getenv("MAX_ALERTS_PER_CORRELATION", "50"))
    
    # RCA Configuration
    RCA_GENERATION_TIMEOUT = int(os.getenv("RCA_GENERATION_TIMEOUT", "180"))  # 3 minutes
    MAX_HISTORICAL_CONTEXT = int(os.getenv("MAX_HISTORICAL_CONTEXT", "10"))
    RCA_CACHE_TTL = int(os.getenv("RCA_CACHE_TTL", "3600"))  # 1 hour
    
    # Vector Store Configuration
    VECTOR_STORE_BATCH_SIZE = int(os.getenv("VECTOR_STORE_BATCH_SIZE", "100"))
    VECTOR_STORE_INDEX_REBUILD_INTERVAL = int(os.getenv("VECTOR_STORE_INDEX_REBUILD_INTERVAL", "86400"))  # 24 hours
    
    # Backup and Recovery
    BACKUP_ENABLED = os.getenv("BACKUP_ENABLED", "True").lower() == "true"
    BACKUP_SCHEDULE = os.getenv("BACKUP_SCHEDULE", "0 2 * * *")  # Daily at 2 AM
    BACKUP_RETENTION_DAYS = int(os.getenv("BACKUP_RETENTION_DAYS", "30"))
    BACKUP_S3_BUCKET = os.getenv("BACKUP_S3_BUCKET", "")
    
    # Email Notifications
    SMTP_HOST = os.getenv("SMTP_HOST", "")
    SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
    SMTP_USERNAME = os.getenv("SMTP_USERNAME", "")
    SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")
    SMTP_USE_TLS = os.getenv("SMTP_USE_TLS", "True").lower() == "true"
    
    # Notification Settings
    ALERT_NOTIFICATION_THRESHOLD = os.getenv("ALERT_NOTIFICATION_THRESHOLD", "high")
    RCA_NOTIFICATION_RECIPIENTS = os.getenv("RCA_NOTIFICATION_RECIPIENTS", "").split(",")
    
    # Integration Settings
    WEBHOOK_ENDPOINTS = os.getenv("WEBHOOK_ENDPOINTS", "").split(",") if os.getenv("WEBHOOK_ENDPOINTS") else []
    SLACK_WEBHOOK_URL = os.getenv("SLACK_WEBHOOK_URL", "")
    TEAMS_WEBHOOK_URL = os.getenv("TEAMS_WEBHOOK_URL", "")
    
    # Feature Flags
    ENABLE_EXPERIMENTAL_FEATURES = os.getenv("ENABLE_EXPERIMENTAL_FEATURES", "False").lower() == "true"
    ENABLE_ADVANCED_CORRELATION = os.getenv("ENABLE_ADVANCED_CORRELATION", "True").lower() == "true"
    ENABLE_AUTO_RCA_GENERATION = os.getenv("ENABLE_AUTO_RCA_GENERATION", "True").lower() == "true"

class SecurityConfig:
    """Security-specific configuration"""
    
    # SSL/TLS Configuration
    SSL_ENABLED = os.getenv("SSL_ENABLED", "True").lower() == "true"
    SSL_CERT_PATH = os.getenv("SSL_CERT_PATH", "/etc/ssl/certs/ai_observability.crt")
    SSL_KEY_PATH = os.getenv("SSL_KEY_PATH", "/etc/ssl/private/ai_observability.key")
    
    # Authentication
    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "your-jwt-secret-key")
    JWT_EXPIRATION_HOURS = int(os.getenv("JWT_EXPIRATION_HOURS", "24"))
    
    # Password Policy
    MIN_PASSWORD_LENGTH = int(os.getenv("MIN_PASSWORD_LENGTH", "12"))
    REQUIRE_SPECIAL_CHARS = os.getenv("REQUIRE_SPECIAL_CHARS", "True").lower() == "true"
    REQUIRE_NUMBERS = os.getenv("REQUIRE_NUMBERS", "True").lower() == "true"
    
    # Session Security
    SESSION_TIMEOUT_MINUTES = int(os.getenv("SESSION_TIMEOUT_MINUTES", "60"))
    MAX_LOGIN_ATTEMPTS = int(os.getenv("MAX_LOGIN_ATTEMPTS", "5"))
    LOCKOUT_DURATION_MINUTES = int(os.getenv("LOCKOUT_DURATION_MINUTES", "30"))
    
    # Data Encryption
    ENCRYPTION_KEY = os.getenv("ENCRYPTION_KEY", "")
    ENCRYPT_SENSITIVE_DATA = os.getenv("ENCRYPT_SENSITIVE_DATA", "True").lower() == "true"

class MonitoringConfig:
    """Monitoring and observability configuration"""
    
    # Prometheus Metrics
    PROMETHEUS_ENABLED = os.getenv("PROMETHEUS_ENABLED", "True").lower() == "true"
    PROMETHEUS_PORT = int(os.getenv("PROMETHEUS_PORT", "9090"))
    
    # OpenTelemetry
    OTEL_ENABLED = os.getenv("OTEL_ENABLED", "False").lower() == "true"
    OTEL_ENDPOINT = os.getenv("OTEL_ENDPOINT", "http://jaeger:14268/api/traces")
    OTEL_SERVICE_NAME = os.getenv("OTEL_SERVICE_NAME", "ai-observability-rca")
    
    # Health Checks
    HEALTH_CHECK_INTERVAL = int(os.getenv("HEALTH_CHECK_INTERVAL", "30"))
    DEEP_HEALTH_CHECK_INTERVAL = int(os.getenv("DEEP_HEALTH_CHECK_INTERVAL", "300"))
    
    # Performance Monitoring
    ENABLE_PROFILING = os.getenv("ENABLE_PROFILING", "False").lower() == "true"
    PROFILING_SAMPLE_RATE = float(os.getenv("PROFILING_SAMPLE_RATE", "0.01"))

# Deployment-specific configurations
DEPLOYMENT_CONFIGS = {
    "kubernetes": {
        "HEALTH_CHECK_PATH": "/api/health",
        "READINESS_PROBE_PATH": "/api/health/detailed",
        "LIVENESS_PROBE_PATH": "/api/health",
        "METRICS_PATH": "/metrics",
        "GRACEFUL_SHUTDOWN_TIMEOUT": 30
    },
    "docker": {
        "CONTAINER_PORT": 8000,
        "HEALTH_CHECK_CMD": "curl -f http://localhost:8000/api/health || exit 1",
        "HEALTH_CHECK_INTERVAL": "30s",
        "HEALTH_CHECK_TIMEOUT": "10s",
        "HEALTH_CHECK_RETRIES": 3
    },
    "systemd": {
        "SERVICE_NAME": "ai-observability-rca",
        "SERVICE_DESCRIPTION": "AI Observability RCA Service",
        "RESTART_POLICY": "always",
        "RESTART_DELAY": "10s"
    }
}

# Environment-specific overrides
def get_config_for_environment(env: str = "production"):
    """Get configuration for specific environment"""
    
    base_config = ProductionConfig()
    
    if env == "staging":
        # Staging-specific overrides
        base_config.LOG_LEVEL = "DEBUG"
        base_config.RATE_LIMIT_REQUESTS_PER_MINUTE = 1000
        base_config.ENABLE_EXPERIMENTAL_FEATURES = True
    
    elif env == "development":
        # Development-specific overrides
        base_config.DEBUG = True
        base_config.LOG_LEVEL = "DEBUG"
        base_config.API_KEY_REQUIRED = False
        base_config.RATE_LIMIT_ENABLED = False
        base_config.SSL_ENABLED = False
    
    elif env == "testing":
        # Testing-specific overrides
        base_config.DATABASE_URL = "postgresql://test_user:test_pass@localhost:5432/ai_observability_test"
        base_config.CHROMA_DB_PATH = "/tmp/test_chroma_db"
        base_config.LOG_LEVEL = "WARNING"
        base_config.RCA_GENERATION_TIMEOUT = 60
    
    return base_config

# Configuration validation
def validate_config(config):
    """Validate configuration settings"""
    
    errors = []
    
    # Required settings
    if not config.SECRET_KEY or config.SECRET_KEY == "your-super-secret-key-change-in-production":
        errors.append("SECRET_KEY must be set and changed from default")
    
    if not config.DATABASE_URL:
        errors.append("DATABASE_URL is required")
    
    if config.API_KEY_REQUIRED and not config.VALID_API_KEYS:
        errors.append("VALID_API_KEYS must be set when API_KEY_REQUIRED is True")
    
    # Validation ranges
    if config.CORRELATION_THRESHOLD < 0 or config.CORRELATION_THRESHOLD > 1:
        errors.append("CORRELATION_THRESHOLD must be between 0 and 1")
    
    if config.RCA_GENERATION_TIMEOUT < 30:
        errors.append("RCA_GENERATION_TIMEOUT should be at least 30 seconds")
    
    if errors:
        raise ValueError("Configuration validation failed:\n" + "\n".join(errors))
    
    return True
