# AI-Driven Observability for Automated Root Cause Analysis

A comprehensive system for automated root cause analysis in modern IT systems using Generative AI.

## 🌟 Features

### Backend (FastAPI)
- **Alert Processing**: Receive and process alerts in JSON format from monitoring tools
- **Intelligent Correlation**: Group related alerts using ML-based correlation algorithms
- **AI-Powered RCA**: Generate root cause analysis using Llama3 via Ollama
- **Vector Storage**: Store historical RCA data for pattern recognition with ChromaDB
- **RESTful API**: Comprehensive API for all operations

### Frontend (Streamlit)
- **Interactive Dashboard**: Real-time overview of RCAs and alerts
- **Search & Filter**: Advanced search capabilities for RCA records
- **Status Management**: Update RCA status (open, in_progress, closed)
- **Feedback System**: Rate RCA accuracy and provide feedback
- **Analytics**: Track accuracy trends and performance metrics

### Key Capabilities
- **Alert Correlation**: Automatically group related alerts using similarity algorithms
- **Historical Context**: Leverage past RCAs to improve new analyses
- **Accuracy Tracking**: Monitor and improve RCA accuracy with user feedback
- **Multi-source Support**: Handle alerts from various monitoring tools
- **Real-time Processing**: Process alerts and generate RCAs in real-time

## 🏗️ Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Monitoring    │    │   Streamlit     │    │     FastAPI     │
│     Tools       │───▶│   Frontend      │───▶│     Backend     │
│                 │    │                 │    │                 │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                                         │
                       ┌─────────────────┐              │
                       │   PostgreSQL    │◄─────────────┤
                       │    Database     │              │
                       └─────────────────┘              │
                                                         │
                       ┌─────────────────┐              │
                       │    ChromaDB     │◄─────────────┤
                       │  Vector Store   │              │
                       └─────────────────┘              │
                                                         │
                       ┌─────────────────┐              │
                       │     Ollama      │◄─────────────┘
                       │   (Llama3)      │
                       └─────────────────┘
```

## 🚀 Quick Start

### Prerequisites
- **OS**: Ubuntu 20.04+ (other Linux distributions may work)
- **Python**: 3.12.3+
- **PostgreSQL**: 12+
- **Git**: For cloning the repository
- **curl**: For downloading Ollama

### 1. Clone Repository
```bash
git clone <repository-url>
cd ai-observability-rca
```

### 2. Setup Database
```bash
# Install PostgreSQL and setup database
python scripts/setup_db.py
```

### 3. Install Ollama and Llama3
```bash
# Make scripts executable
chmod +x scripts/install_ollama.sh
chmod +x scripts/start_services.sh

# Install Ollama and download Llama3 model
./scripts/install_ollama.sh
```

### 4. Configure Environment
```bash
# Copy environment template
cp backend/.env.example backend/.env

# Edit configuration (update database credentials if needed)
nano backend/.env
```

### 5. Install Dependencies
```bash
# Backend dependencies
cd backend
pip install -r requirements.txt
cd ..

# Frontend dependencies
cd frontend
pip install -r requirements.txt
cd ..
```

### 6. Start All Services
```bash
# Start all services (Ollama, Backend API, Frontend)
./scripts/start_services.sh
```

### 7. Access the Application
- **Frontend Dashboard**: http://localhost:8501
- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs

## 📋 Detailed Setup

### Backend Setup

1. **Navigate to backend directory**:
   ```bash
   cd backend
   ```

2. **Create virtual environment** (recommended):
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Linux/Mac
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment**:
   ```bash
   cp .env.example .env
   # Edit .env with your database credentials
   ```
   ### Database Setup (Manual)

If the automated setup doesn't work:

1. **Install PostgreSQL**:
   ```bash
   sudo apt update
   sudo apt install postgresql postgresql-contrib
   ```

2. **Create database and user**:
   ```bash
   sudo -u postgres createdb ai_observability
   sudo -u postgres createuser --createdb --pwprompt ai_user
   ```

## 🔧 Configuration

### Environment Variables

Edit `backend/.env`:

```bash
# Database Configuration
DATABASE_URL=postgresql://ai_user:password@localhost:5432/ai_observability
DB_HOST=localhost
DB_PORT=5432
DB_NAME=ai_observability
DB_USER=ai_user
DB_PASSWORD=your_password

# Ollama Configuration
OLLAMA_HOST=http://localhost:11434
OLLAMA_MODEL=llama3

# ChromaDB Configuration
CHROMA_DB_PATH=./chroma_db

# API Configuration
API_HOST=0.0.0.0
API_PORT=8000
DEBUG=True

# CORS Configuration
ALLOWED_ORIGINS=["http://localhost:8501"],"http://127.0.0.1:8501"]
```

5. **Run backend**:
   ```bash
   python run.py
   ```

### Frontend Setup

1. **Navigate to frontend directory**:
   ```bash
   cd frontend
   ```

2. **Create virtual environment** (recommended):
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Linux/Mac
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Run frontend**:
   ```bash
   streamlit run app.py
   ```

### Database Setup (Manual)

If the automated setup doesn't work:

1. **Install PostgreSQL**:
   ```bash
   sudo apt update
   sudo apt install postgresql postgresql-contrib
   ```

2. **Create database and user**:
   ```bash
   sudo -u postgres createdb ai_observability
   sudo -u postgres createuser --createdb --pwprompt ai_user
   ```

3. **Update environment variables** in `backend/.env`

### Ollama Setup (Manual)

If the automated installation doesn't work:

1. **Install Ollama**:
   ```bash
   curl -fsSL https://ollama.ai/install.sh | sh
   ```
2. **Start Ollama**:
   ```bash
   ollama serve
   ```
3. **Download Llama3**:
   ```bash
   ollama pull llama3
   ```


### Advanced Configuration

- **Correlation Threshold**: Adjust `CORRELATION_THRESHOLD` (default: 0.7)
- **Time Window**: Modify `CORRELATION_TIME_WINDOW` in seconds (default: 300)
- **RCA Timeout**: Set `RCA_GENERATION_TIMEOUT` (default: 120 seconds)

## 📚 API Documentation

### Core Endpoints

#### Alerts
- `POST /api/alerts/` - Create new alert
- `GET /api/alerts/` - Retrieve alerts with filters
- `GET /api/alerts/{alert_id}` - Get specific alert
- `PUT /api/alerts/{alert_id}` - Update alert
- `DELETE /api/alerts/{alert_id}` - Delete alert

#### RCA
- `POST /api/rca/generate` - Generate RCA for correlation
- `GET /api/rca/` - Retrieve RCAs with filters
- `GET /api/rca/{rca_id}` - Get specific RCA
- `PUT /api/rca/{rca_id}` - Update RCA
- `PUT /api/rca/{rca_id}/status` - Update RCA status
- `POST /api/rca/{rca_id}/feedback` - Submit feedback

#### System
- `GET /api/health` - Basic health check
- `GET /api/health/detailed` - Detailed health status

### Example Alert Submission

```bash
curl -X POST "http://localhost:8000/api/alerts/" \
     -H "Content-Type: application/json" \
     -d '{
       "alert_id": "alert-001",
       "source": "prometheus",
       "severity": "high",
       "title": "High CPU Usage",
       "message": "CPU usage is above 90%",
       "alert_type": "metrics",
       "raw_data": {
         "cpu_usage": 95.2,
         "host": "web-server-01"
       }
     }'
```

### Example RCA Generation

```bash
curl -X POST "http://localhost:8000/api/rca/generate" \
     -H "Content-Type: application/json" \
     -d '{
       "correlation_id": "corr-123",
       "title": "CPU Usage Investigation",
       "priority": "high",
       "use_historical_context": true
     }'
```

## 🎯 Usage Examples

### 1. Alert Processing Workflow

1. **Monitoring tool sends alert** to `/api/alerts/`
2. **System correlates** alert with existing alerts
3. **User generates RCA** for correlated alerts
4. **AI analyzes** alerts and provides root cause
5. **User reviews** and provides feedback
6. **System learns** from feedback for future analyses

### 2. Dashboard Operations

1. **View Overview**: See all RCAs and alerts on dashboard
2. **Search & Filter**: Use advanced filters to find specific RCAs
3. **Manage Status**: Update RCA status (open → in_progress → closed)
4. **Provide Feedback**: Rate accuracy and add comments
5. **Generate Reports**: Export RCA data and reports

### 3. Monitoring Integration

```python
# Example integration with monitoring tool
import requests

def send_alert_to_rca_system(alert_data):
    url = "http://localhost:8000/api/alerts/"
    headers = {"Content-Type": "application/json"}
    
    response = requests.post(url, json=alert_data, headers=headers)
    return response.json()

# Alert from Prometheus
alert = {
    "alert_id": "prometheus-123",
    "source": "prometheus",
    "severity": "critical",
    "title": "Service Down",
    "message": "HTTP service is not responding",
    "alert_type": "metrics",
    "raw_data": {
        "job": "web-service",
        "instance": "10.0.1.100:8080"
    }
}

result = send_alert_to_rca_system(alert)
print(f"Alert created: {result}")
```

## 🔍 Troubleshooting

### Common Issues

1. **Database Connection Error**:
   ```bash
   # Check PostgreSQL status
   sudo systemctl status postgresql
   
   # Restart PostgreSQL
   sudo systemctl restart postgresql
   ```

2. **Ollama Not Responding**:
   ```bash
   # Check Ollama status
   ollama list
   
   # Restart Ollama
   pkill ollama
   ollama serve
   ```

3. **Backend API Error**:
   ```bash
   # Check backend logs
   tail -f /tmp/backend.log
   
   # Restart backend
   cd backend && python run.py
   ```

4. **Frontend Not Loading**:
   ```bash
   # Check frontend logs
   tail -f /tmp/frontend.log
   
   # Restart frontend
   cd frontend && streamlit run app.py
   ```

### Service Management

```bash
# Check service status
./scripts/start_services.sh status

# View logs
./scripts/start_services.sh logs backend
./scripts/start_services.sh logs frontend
./scripts/start_services.sh logs ollama

# Restart all services
./scripts/start_services.sh restart

# Stop all services
./scripts/start_services.sh stop
```

### Health Checks

```bash
# Check API health
curl http://localhost:8000/api/health

# Check detailed health
curl http://localhost:8000/api/health/detailed

# Check Ollama
curl http://localhost:11434/api/tags

# Check database connection
psql -h localhost -U ai_user -d ai_observability -c "SELECT version();"
```

## 🧪 Testing

### Run Sample Alert

Use the frontend to create a test alert:
1. Go to **Sidebar** → **Quick Actions** → **📥 Create Test Alert**
2. Fill in the form and submit
3. Check the dashboard for the new alert

### Generate Sample RCA

1. Create multiple test alerts
2. Wait for correlation (or force correlate)
3. Generate RCA from the dashboard
4. Review the AI-generated analysis

### API Testing

```bash
# Test health endpoint
curl http://localhost:8000/api/health

# Create test alert
curl -X POST http://localhost:8000/api/alerts/ \
  -H "Content-Type: application/json" \
  -d '{"alert_id":"test-1","source":"test","severity":"medium","title":"Test Alert","message":"Test message","alert_type":"logs","raw_data":{}}'

# Get alerts
curl http://localhost:8000/api/alerts/
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

- **Issues**: Create an issue on GitHub
- **Documentation**: Check this README and API docs
- **Logs**: Use `./scripts/start_services.sh logs [service]` for debugging

## 🔮 Future Enhancements

- **Multi-LLM Support**: Support for multiple LLM backends
- **Advanced Correlation**: More sophisticated correlation algorithms
- **Integration APIs**: Direct integrations with popular monitoring tools
- **Machine Learning**: Improved accuracy through ML feedback loops
- **Notification System**: Real-time notifications for critical RCAs
- **Multi-tenant Support**: Support for multiple organizations
- **Custom Plugins**: Extensible plugin system for custom logic

---

**Built with ❤️ using FastAPI, Streamlit, PostgreSQL, ChromaDB, and Llama3**
