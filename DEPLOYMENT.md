# Deployment Guide

This guide covers various deployment options for the AI Observability RCA system.

## 📋 Table of Contents

1. [Prerequisites](#prerequisites)
2. [Development Deployment](#development-deployment)
3. [Production Deployment](#production-deployment)
4. [Cloud Deployment](#cloud-deployment)
5. [Kubernetes Deployment](#kubernetes-deployment)
6. [Monitoring & Observability](#monitoring--observability)
7. [Security Considerations](#security-considerations)
8. [Backup & Recovery](#backup--recovery)
9. [Troubleshooting](#troubleshooting)

## Prerequisites

### System Requirements

**Minimum (Development):**
- 4 GB RAM
- 2 CPU cores
- 20 GB disk space
- Ubuntu 20.04+ or similar Linux distribution

**Recommended (Production):**
- 16 GB RAM
- 8 CPU cores
- 100 GB SSD storage
- Ubuntu 22.04 LTS

### Software Dependencies

- Python 3.12.3+
- PostgreSQL 12+
- Git
- curl
- sudo access

## Development Deployment

### Quick Start (Single Machine)

1. **Clone and Setup:**
   ```bash
   git clone <repository-url>
   cd ai-observability-rca
   
   # Setup database
   python scripts/setup_db.py
   
   # Install Ollama and Llama3
   chmod +x scripts/install_ollama.sh
   ./scripts/install_ollama.sh
   
   # Configure environment
   cp backend/.env.example backend/.env
   # Edit backend/.env with your settings
   
   # Start all services
   chmod +x scripts/start_services.sh
   ./scripts/start_services.sh
   ```

2. **Verify Installation:**
   ```bash
   # Check service status
   ./scripts/start_services.sh status
   
   # Test endpoints
   curl http://localhost:8000/api/health
   curl http://localhost:8501  # Should return HTML
   ```

### Development with Virtual Environments

```bash
# Backend setup
cd backend
python -m venv venv
source venv/bin/activate  # Linux/Mac
pip install -r requirements.txt

# Frontend setup
cd ../frontend
python -m venv venv
source venv/bin/activate  # Linux/Mac
pip install -r requirements.txt
```

## Production Deployment

### 1. Server Preparation

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install dependencies
sudo apt install -y python3.12 python3.12-venv python3-pip postgresql postgresql-contrib nginx supervisor ufw

# Create application user
sudo useradd -m -s /bin/bash ai-rca
sudo usermod -aG sudo ai-rca
```

### 2. Database Setup

```bash
# Create database and user
sudo -u postgres createdb ai_observability_prod
sudo -u postgres createuser --createdb --pwprompt ai_rca_user

# Configure PostgreSQL
sudo vim /etc/postgresql/*/main/postgresql.conf
# Set: max_connections = 100, shared_buffers = 256MB

sudo vim /etc/postgresql/*/main/pg_hba.conf
# Add: local ai_observability_prod ai_rca_user md5

sudo systemctl restart postgresql
```

### 3. Application Deployment

```bash
# Switch to application user
sudo su - ai-rca

# Clone repository
git clone <repository-url> /opt/ai-observability-rca
cd /opt/ai-observability-rca

# Setup backend
cd backend
python3.12 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
pip install gunicorn  # Production WSGI server

# Setup frontend
cd ../frontend
python3.12 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Configure environment
cp backend/.env.example backend/.env.prod
# Edit with production settings
```

### 4. Production Configuration

Create `/opt/ai-observability-rca/backend/.env.prod`:

```bash
# Database
DATABASE_URL=postgresql://ai_rca_user:your_password@localhost:5432/ai_observability_prod

# Security
SECRET_KEY=your-super-secure-secret-key
API_KEY_REQUIRED=True
VALID_API_KEYS=api-key-1,api-key-2

# Performance
DEBUG=False
WORKER_PROCESSES=4
CORRELATION_THRESHOLD=0.8

# CORS
ALLOWED_ORIGINS=https://yourdomain.com

# Ollama
OLLAMA_HOST=http://localhost:11434
OLLAMA_MODEL=llama3

# Logging
LOG_LEVEL=INFO
LOG_FILE=/var/log/ai-observability/app.log
```

### 5. Process Management with Supervisor

Create `/etc/supervisor/conf.d/ai-rca-backend.conf`:

```ini
[program:ai-rca-backend]
command=/opt/ai-observability-rca/backend/venv/bin/gunicorn app.main:app --bind 127.0.0.1:8000 --workers 4 --worker-class uvicorn.workers.UvicornWorker
directory=/opt/ai-observability-rca/backend
user=ai-rca
autostart=true
autorestart=true
environment=PATH="/opt/ai-observability-rca/backend/venv/bin"
stdout_logfile=/var/log/ai-observability/backend.log
stderr_logfile=/var/log/ai-observability/backend-error.log
```

Create `/etc/supervisor/conf.d/ai-rca-frontend.conf`:

```ini
[program:ai-rca-frontend]
command=/opt/ai-observability-rca/frontend/venv/bin/streamlit run app.py --server.port 8501 --server.address 127.0.0.1 --server.headless true
directory=/opt/ai-observability-rca/frontend
user=ai-rca
autostart=true
autorestart=true
environment=PATH="/opt/ai-observability-rca/frontend/venv/bin"
stdout_logfile=/var/log/ai-observability/frontend.log
stderr_logfile=/var/log/ai-observability/frontend-error.log
```

Create `/etc/supervisor/conf.d/ollama.conf`:

```ini
[program:ollama]
command=/usr/local/bin/ollama serve
user=ai-rca
autostart=true
autorestart=true
stdout_logfile=/var/log/ai-observability/ollama.log
stderr_logfile=/var/log/ai-observability/ollama-error.log
environment=OLLAMA_HOST=0.0.0.0
```

### 6. Nginx Configuration

Create `/etc/nginx/sites-available/ai-rca`:

```nginx
upstream backend {
    server 127.0.0.1:8000;
}

upstream frontend {
    server 127.0.0.1:8501;
}

# Backend API
server {
    listen 80;
    server_name api.yourdomain.com;
    
    location / {
        proxy_pass http://backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # Timeouts for long-running RCA generation
        proxy_read_timeout 300s;
        proxy_connect_timeout 10s;
        proxy_send_timeout 300s;
    }
    
    # Health check endpoint
    location /health {
        proxy_pass http://backend/api/health;
        access_log off;
    }
}

# Frontend
server {
    listen 80;
    server_name rca.yourdomain.com;
    
    location / {
        proxy_pass http://frontend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # WebSocket support for Streamlit
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
    
    location ^~ /static {
        proxy_pass http://frontend/static/;
    }
    
    location ^~ /healthz {
        proxy_pass http://frontend/healthz;
        access_log off;
    }
}
```

### 7. SSL Configuration

```bash
# Install Certbot
sudo apt install certbot python3-certbot-nginx

# Get SSL certificates
sudo certbot --nginx -d api.yourdomain.com -d rca.yourdomain.com

# Auto-renewal
sudo crontab -e
# Add: 0 12 * * * /usr/bin/certbot renew --quiet
```

### 8. Firewall Setup

```bash
# Configure UFW
sudo ufw allow ssh
sudo ufw allow 'Nginx Full'
sudo ufw allow from 10.0.0.0/8 to any port 5432  # PostgreSQL (internal network only)
sudo ufw enable
```

### 9. Start Services

```bash
# Create log directory
sudo mkdir -p /var/log/ai-observability
sudo chown ai-rca:ai-rca /var/log/ai-observability

# Start services
sudo supervisorctl reread
sudo supervisorctl update
sudo supervisorctl start all

# Enable Nginx
sudo ln -s /etc/nginx/sites-available/ai-rca /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

## Cloud Deployment

### AWS Deployment

#### EC2 Instance Setup

1. **Launch EC2 Instance:**
   - AMI: Ubuntu 22.04 LTS
   - Instance Type: t3.large (minimum)
   - Security Groups: HTTP, HTTPS, SSH
   - Storage: 50GB GP3

2. **RDS for PostgreSQL:**
   ```bash
   # Create RDS instance
   aws rds create-db-instance \
     --db-instance-identifier ai-rca-prod \
     --db-instance-class db.t3.medium \
     --engine postgres \
     --master-username ai_rca_admin \
     --master-user-password your-secure-password \
     --allocated-storage 100 \
     --vpc-security-group-ids sg-xxxxxxxxx
   ```

3. **Application Load Balancer:**
   ```bash
   # Create target groups
   aws elbv2 create-target-group \
     --name ai-rca-backend \
     --protocol HTTP \
     --port 8000 \
     --vpc-id vpc-xxxxxxxxx \
     --health-check-path /api/health
   
   aws elbv2 create-target-group \
     --name ai-rca-frontend \
     --protocol HTTP \
     --port 8501 \
     --vpc-id vpc-xxxxxxxxx \
     --health-check-path /
   ```

#### S3 for Backups

```bash
# Create S3 bucket for backups
aws s3 mb s3://ai-rca-backups-your-org

# Setup backup script
cat > /opt/ai-observability-rca/scripts/backup_to_s3.sh << 'EOF'
#!/bin/bash
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="/tmp/ai_rca_backup_$DATE.sql"

# Database backup
pg_dump postgresql://user:pass@rds-endpoint:5432/ai_observability_prod > $BACKUP_FILE

# Upload to S3
aws s3 cp $BACKUP_FILE s3://ai-rca-backups-your-org/database/
rm $BACKUP_FILE

# Backup ChromaDB
tar -czf /tmp/chroma_backup_$DATE.tar.gz /opt/ai-observability-rca/chroma_db/
aws s3 cp /tmp/chroma_backup_$DATE.tar.gz s3://ai-rca-backups-your-org/chroma/
rm /tmp/chroma_backup_$DATE.tar.gz
EOF

chmod +x /opt/ai-observability-rca/scripts/backup_to_s3.sh

# Schedule backup
echo "0 2 * * * /opt/ai-observability-rca/scripts/backup_to_s3.sh" | crontab -
```

### Google Cloud Platform

```bash
# Create VM instance
gcloud compute instances create ai-rca-prod \
  --image-family=ubuntu-2204-lts \
  --image-project=ubuntu-os-cloud \
  --machine-type=e2-standard-4 \
  --boot-disk-size=50GB \
  --tags=http-server,https-server

# Create Cloud SQL instance
gcloud sql instances create ai-rca-db \
  --database-version=POSTGRES_14 \
  --tier=db-custom-2-8192 \
  --region=us-central1

# Create database
gcloud sql databases create ai_observability_prod --instance=ai-rca-db
```

### Azure

```bash
# Create resource group
az group create --name ai-rca-rg --location eastus

# Create VM
az vm create \
  --resource-group ai-rca-rg \
  --name ai-rca-vm \
  --image Ubuntu2204 \
  --admin-username azureuser \
  --size Standard_D4s_v3 \
  --generate-ssh-keys

# Create PostgreSQL server
az postgres server create \
  --resource-group ai-rca-rg \
  --name ai-rca-db-server \
  --location eastus \
  --admin-user ai_rca_admin \
  --admin-password your-secure-password \
  --sku-name GP_Gen5_2
```

## Kubernetes Deployment

### Namespace and ConfigMap

```yaml
# namespace.yaml
apiVersion: v1
kind: Namespace
metadata:
  name: ai-rca

---
# configmap.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: ai-rca-config
  namespace: ai-rca
data:
  POSTGRES_HOST: "postgresql-service"
  POSTGRES_DB: "ai_observability"
  OLLAMA_HOST: "http://ollama-service:11434"
  CHROMA_DB_PATH: "/data/chroma_db"
  API_HOST: "0.0.0.0"
  API_PORT: "8000"
  DEBUG: "False"
```

### PostgreSQL Deployment

```yaml
# postgresql.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: postgresql
  namespace: ai-rca
spec:
  replicas: 1
  selector:
    matchLabels:
      app: postgresql
  template:
    metadata:
      labels:
        app: postgresql
    spec:
      containers:
      - name: postgresql
        image: postgres:14
        env:
        - name: POSTGRES_DB
          value: ai_observability
        - name: POSTGRES_USER
          value: ai_rca_user
        - name: POSTGRES_PASSWORD
          valueFrom:
            secretKeyRef:
              name: ai-rca-secrets
              key: postgres-password
        ports:
        - containerPort: 5432
        volumeMounts:
        - name: postgres-data
          mountPath: /var/lib/postgresql/data
      volumes:
      - name: postgres-data
        persistentVolumeClaim:
          claimName: postgres-pvc

---
apiVersion: v1
kind: Service
metadata:
  name: postgresql-service
  namespace: ai-rca
spec:
  selector:
    app: postgresql
  ports:
  - port: 5432
    targetPort: 5432
```

### Ollama Deployment

```yaml
# ollama.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: ollama
  namespace: ai-rca
spec:
  replicas: 1
  selector:
    matchLabels:
      app: ollama
  template:
    metadata:
      labels:
        app: ollama
    spec:
      containers:
      - name: ollama
        image: ollama/ollama:latest
        ports:
        - containerPort: 11434
        volumeMounts:
        - name: ollama-data
          mountPath: /root/.ollama
        resources:
          requests:
            memory: "4Gi"
            cpu: "2"
          limits:
            memory: "8Gi"
            cpu: "4"
      volumes:
      - name: ollama-data
        persistentVolumeClaim:
          claimName: ollama-pvc

---
apiVersion: v1
kind: Service
metadata:
  name: ollama-service
  namespace: ai-rca
spec:
  selector:
    app: ollama
  ports:
  - port: 11434
    targetPort: 11434
```

### Backend Deployment

```yaml
# backend.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: ai-rca-backend
  namespace: ai-rca
spec:
  replicas: 3
  selector:
    matchLabels:
      app: ai-rca-backend
  template:
    metadata:
      labels:
        app: ai-rca-backend
    spec:
      containers:
      - name: backend
        image: your-registry/ai-rca-backend:latest
        ports:
        - containerPort: 8000
        env:
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: ai-rca-secrets
              key: database-url
        envFrom:
        - configMapRef:
            name: ai-rca-config
        volumeMounts:
        - name: chroma-data
          mountPath: /data/chroma_db
        livenessProbe:
          httpGet:
            path: /api/health
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /api/health/detailed
            port: 8000
          initialDelaySeconds: 5
          periodSeconds: 5
      volumes:
      - name: chroma-data
        persistentVolumeClaim:
          claimName: chroma-pvc

---
apiVersion: v1
kind: Service
metadata:
  name: ai-rca-backend-service
  namespace: ai-rca
spec:
  selector:
    app: ai-rca-backend
  ports:
  - port: 8000
    targetPort: 8000
  type: ClusterIP
```

### Ingress Configuration

```yaml
# ingress.yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: ai-rca-ingress
  namespace: ai-rca
  annotations:
    kubernetes.io/ingress.class: nginx
    cert-manager.io/cluster-issuer: letsencrypt-prod
    nginx.ingress.kubernetes.io/proxy-read-timeout: "300"
    nginx.ingress.kubernetes.io/proxy-send-timeout: "300"
spec:
  tls:
  - hosts:
    - api.yourdomain.com
    - rca.yourdomain.com
    secretName: ai-rca-tls
  rules:
  - host: api.yourdomain.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: ai-rca-backend-service
            port:
              number: 8000
  - host: rca.yourdomain.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: ai-rca-frontend-service
            port:
              number: 8501
```

## Monitoring & Observability

### Prometheus Configuration

```yaml
# prometheus-config.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: prometheus-config
  namespace: ai-rca
data:
  prometheus.yml: |
    global:
      scrape_interval: 15s
    scrape_configs:
    - job_name: 'ai-rca-backend'
      static_configs:
      - targets: ['ai-rca-backend-service:8000']
      metrics_path: /metrics
    - job_name: 'ai-rca-system'
      static_configs:
      - targets: ['node-exporter:9100']
```

### Grafana Dashboard

```json
{
  "dashboard": {
    "title": "AI Observability RCA",
    "panels": [
      {
        "title": "Request Rate",
        "type": "graph",
        "targets": [
          {
            "expr": "rate(http_requests_total{job=\"ai-rca-backend\"}[5m])"
          }
        ]
      },
      {
        "title": "Response Times",
        "type": "graph",
        "targets": [
          {
            "expr": "histogram_quantile(0.95, rate(http_request_duration_seconds_bucket{job=\"ai-rca-backend\"}[5m]))"
          }
        ]
      },
      {
        "title": "RCA Generation Time",
        "type": "graph",
        "targets": [
          {
            "expr": "rca_generation_duration_seconds"
          }
        ]
      }
    ]
  }
}
```

## Security Considerations

### 1. Network Security

```bash
# Firewall rules (iptables)
iptables -A INPUT -p tcp --dport 22 -j ACCEPT    # SSH
iptables -A INPUT -p tcp --dport 80 -j ACCEPT    # HTTP
iptables -A INPUT -p tcp --dport 443 -j ACCEPT   # HTTPS
iptables -A INPUT -p tcp --dport 5432 -s 10.0.0.0/8 -j ACCEPT  # PostgreSQL (internal only)
iptables -A INPUT -j DROP  # Drop all other traffic
```

### 2. API Security

```python
# backend/app/security.py
from fastapi import HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

security = HTTPBearer()

async def verify_api_key(credentials: HTTPAuthorizationCredentials = Depends(security)):
    if credentials.credentials not in settings.VALID_API_KEYS:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key"
        )
    return credentials.credentials
```

### 3. Database Security

```sql
-- Create read-only user for monitoring
CREATE USER monitoring_user WITH PASSWORD 'monitoring_password';
GRANT CONNECT ON DATABASE ai_observability TO monitoring_user;
GRANT USAGE ON SCHEMA public TO monitoring_user;
GRANT SELECT ON ALL TABLES IN SCHEMA public TO monitoring_user;

-- Row-level security example
ALTER TABLE rca_analyses ENABLE ROW LEVEL SECURITY;
CREATE POLICY rca_team_policy ON rca_analyses
  FOR ALL TO api_user
  USING (team = current_setting('app.current_team'));
```

## Backup & Recovery

### Automated Backup Script

```bash
#!/bin/bash
# backup.sh

set -e

DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/opt/backups"
S3_BUCKET="ai-rca-backups"

# Create backup directory
mkdir -p $BACKUP_DIR

# Database backup
echo "Creating database backup..."
pg_dump $DATABASE_URL > $BACKUP_DIR/db_backup_$DATE.sql
gzip $BACKUP_DIR/db_backup_$DATE.sql

# ChromaDB backup
echo "Creating ChromaDB backup..."
tar -czf $BACKUP_DIR/chroma_backup_$DATE.tar.gz /opt/ai-observability-rca/chroma_db/

# Application code backup
echo "Creating application backup..."
tar -czf $BACKUP_DIR/app_backup_$DATE.tar.gz /opt/ai-observability-rca/ --exclude=chroma_db --exclude=venv --exclude=__pycache__

# Upload to S3 (if configured)
if [ ! -z "$S3_BUCKET" ]; then
    echo "Uploading backups to S3..."
    aws s3 cp $BACKUP_DIR/db_backup_$DATE.sql.gz s3://$S3_BUCKET/database/
    aws s3 cp $BACKUP_DIR/chroma_backup_$DATE.tar.gz s3://$S3_BUCKET/chroma/
    aws s3 cp $BACKUP_DIR/app_backup_$DATE.tar.gz s3://$S3_BUCKET/application/
fi

# Cleanup old backups (keep 7 days)
find $BACKUP_DIR -name "*.gz" -mtime +7 -delete

echo "Backup completed successfully"
```

### Recovery Procedure

```bash
#!/bin/bash
# restore.sh

BACKUP_DATE=$1
BACKUP_DIR="/opt/backups"

if [ -z "$BACKUP_DATE" ]; then
    echo "Usage: $0 <backup_date>"
    echo "Example: $0 20241201_140000"
    exit 1
fi

# Stop services
sudo supervisorctl stop all

# Restore database
echo "Restoring database..."
gunzip -c $BACKUP_DIR/db_backup_$BACKUP_DATE.sql.gz | psql $DATABASE_URL

# Restore ChromaDB
echo "Restoring ChromaDB..."
rm -rf /opt/ai-observability-rca/chroma_db/
tar -xzf $BACKUP_DIR/chroma_backup_$BACKUP_DATE.tar.gz -C /

# Set permissions
chown -R ai-rca:ai-rca /opt/ai-observability-rca/

# Start services
sudo supervisorctl start all

echo "Restore completed successfully"
```

## Troubleshooting

### Common Issues

1. **High Memory Usage:**
   ```bash
   # Monitor memory
   free -h
   
   # Check ChromaDB size
   du -sh /opt/ai-observability-rca/chroma_db/
   
   # Restart services if needed
   sudo supervisorctl restart all
   ```

2. **Slow RCA Generation:**
   ```bash
   # Check Ollama model
   ollama list
   
   # Monitor GPU usage (if available)
   nvidia-smi
   
   # Check Ollama logs
   tail -f /var/log/ai-observability/ollama.log
   ```

3. **Database Connection Issues:**
   ```bash
   # Test database connection
   psql $DATABASE_URL -c "SELECT version();"
   
   # Check PostgreSQL status
   sudo systemctl status postgresql
   
   # View PostgreSQL logs
   sudo tail -f /var/log/postgresql/postgresql-*.log
   ```

### Performance Tuning

1. **PostgreSQL Optimization:**
   ```sql
   -- postgresql.conf
   shared_buffers = 256MB
   effective_cache_size = 1GB
   maintenance_work_mem = 64MB
   checkpoint_completion_target = 0.9
   wal_buffers = 16MB
   default_statistics_target = 100
   ```

2. **Application Tuning:**
   ```bash
   # Increase worker processes
   export WORKER_PROCESSES=8
   
   # Tune correlation parameters
   export CORRELATION_THRESHOLD=0.8
   export CORRELATION_TIME_WINDOW=600
   ```

### Log Analysis

```bash
# Search for errors
grep -i error /var/log/ai-observability/*.log

# Monitor real-time logs
tail -f /var/log/ai-observability/app.log | grep -i "rca\|correlation"

# Analyze performance
cat /var/log/ai-observability/app.log | grep "response_time" | awk '{print $NF}' | sort -n
```

### Health Check Commands

```bash
# System health
curl -s http://localhost:8000/api/health/detailed | jq

# Database health
psql $DATABASE_URL -c "SELECT COUNT(*) as total_alerts FROM alerts;"

# Ollama health
curl -s http://localhost:11434/api/tags | jq

# Service status
sudo supervisorctl status
```

This deployment guide provides comprehensive instructions for deploying the AI Observability RCA system in various environments, from development to production-grade cloud deployments.
