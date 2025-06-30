#!/bin/bash

# AI Observability RCA - Service Startup Script
# This script starts all required services for the application

set -e

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Print functions
print_status() { echo -e "${GREEN}✅ $1${NC}"; }
print_warning() { echo -e "${YELLOW}⚠️ $1${NC}"; }
print_error() { echo -e "${RED}❌ $1${NC}"; }
print_info() { echo -e "${BLUE}ℹ️ $1${NC}"; }

# Configuration
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BACKEND_DIR="$PROJECT_ROOT/backend"
FRONTEND_DIR="$PROJECT_ROOT/frontend"
BACKEND_PORT=8000
FRONTEND_PORT=8501
OLLAMA_PORT=11434

# PID files
BACKEND_PID_FILE="/tmp/ai_observability_backend.pid"
FRONTEND_PID_FILE="/tmp/ai_observability_frontend.pid"
OLLAMA_PID_FILE="/tmp/ai_observability_ollama.pid"

echo "🚀 Starting AI Observability RCA Services"
echo "=========================================="
echo "📁 Project root: $PROJECT_ROOT"

# Function to check if port is in use
check_port() {
    local port=$1
    if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null; then
        return 0  # Port is in use
    else
        return 1  # Port is free
    fi
}

# Function to wait for service to be ready
wait_for_service() {
    local url=$1
    local service_name=$2
    local max_attempts=30
    local attempt=1
    
    print_info "Waiting for $service_name to be ready..."
    
    while [ $attempt -le $max_attempts ]; do
        if curl -s "$url" >/dev/null 2>&1; then
            print_status "$service_name is ready!"
            return 0
        fi
        
        echo -n "."
        sleep 1
        attempt=$((attempt + 1))
    done
    
    print_error "$service_name failed to start within $max_attempts seconds"
    return 1
}

# Function to start Ollama
start_ollama() {
    print_info "Starting Ollama service..."
    
    # Check if Ollama is installed
    if ! command -v ollama &> /dev/null; then
        print_error "Ollama not found. Please run scripts/install_ollama.sh first"
        return 1
    fi
    
    # Check if already running
    if check_port $OLLAMA_PORT; then
        print_status "Ollama already running on port $OLLAMA_PORT"
        return 0
    fi
    
    # Start Ollama
    print_info "Starting Ollama on port $OLLAMA_PORT..."
    nohup ollama serve > /tmp/ollama.log 2>&1 &
    OLLAMA_PID=$!
    echo $OLLAMA_PID > $OLLAMA_PID_FILE
    
    # Wait for Ollama to be ready
    if wait_for_service "http://localhost:$OLLAMA_PORT/api/tags" "Ollama"; then
        print_status "Ollama started successfully (PID: $OLLAMA_PID)"
        return 0
    else
        print_error "Failed to start Ollama"
        return 1
    fi
}

# Function to start backend
start_backend() {
    print_info "Starting Backend API..."
    
    # Check if backend directory exists
    if [ ! -d "$BACKEND_DIR" ]; then
        print_error "Backend directory not found: $BACKEND_DIR"
        return 1
    fi
    
    # Check if already running
    if check_port $BACKEND_PORT; then
        print_status "Backend already running on port $BACKEND_PORT"
        return 0
    fi
    
    # Change to backend directory
    cd "$BACKEND_DIR"
    
    # Check if virtual environment exists
    if [ -d "venv" ]; then
        print_info "Activating virtual environment..."
        source venv/bin/activate
    else
        print_warning "No virtual environment found. Using system Python."
    fi
    
    # Check if dependencies are installed
    if ! python -c "import fastapi" 2>/dev/null; then
        print_info "Installing backend dependencies..."
        pip install -r requirements.txt
    fi
    
    # Start backend
    print_info "Starting backend on port $BACKEND_PORT..."
    nohup python run.py > /tmp/backend.log 2>&1 &
    BACKEND_PID=$!
    echo $BACKEND_PID > $BACKEND_PID_FILE
    
    # Wait for backend to be ready
    if wait_for_service "http://localhost:$BACKEND_PORT/api/health" "Backend API"; then
        print_status "Backend started successfully (PID: $BACKEND_PID)"
        return 0
    else
        print_error "Failed to start backend"
        return 1
    fi
}

# Function to start frontend
start_frontend() {
    print_info "Starting Frontend..."
    
    # Check if frontend directory exists
    if [ ! -d "$FRONTEND_DIR" ]; then
        print_error "Frontend directory not found: $FRONTEND_DIR"
        return 1
    fi
    
    # Check if already running
    if check_port $FRONTEND_PORT; then
        print_status "Frontend already running on port $FRONTEND_PORT"
        return 0
    fi
    
    # Change to frontend directory
    cd "$FRONTEND_DIR"
    
    # Check if virtual environment exists
    if [ -d "venv" ]; then
        print_info "Activating virtual environment..."
        source venv/bin/activate
    else
        print_warning "No virtual environment found. Using system Python."
    fi
    
    # Check if dependencies are installed
    if ! python -c "import streamlit" 2>/dev/null; then
        print_info "Installing frontend dependencies..."
        pip install -r requirements.txt
    fi
    
    # Start frontend
    print_info "Starting frontend on port $FRONTEND_PORT..."
    nohup streamlit run app.py --server.port $FRONTEND_PORT --server.headless true > /tmp/frontend.log 2>&1 &
    FRONTEND_PID=$!
    echo $FRONTEND_PID > $FRONTEND_PID_FILE
    
    # Wait for frontend to be ready
    if wait_for_service "http://localhost:$FRONTEND_PORT" "Frontend"; then
        print_status "Frontend started successfully (PID: $FRONTEND_PID)"
        return 0
    else
        print_error "Failed to start frontend"
        return 1
    fi
}

# Function to check service health
check_health() {
    print_info "Checking service health..."
    
    # Check Ollama
    if curl -s "http://localhost:$OLLAMA_PORT/api/tags" >/dev/null; then
        print_status "Ollama: Healthy"
    else
        print_error "Ollama: Unhealthy"
    fi
    
    # Check Backend
    if curl -s "http://localhost:$BACKEND_PORT/api/health" >/dev/null; then
        print_status "Backend: Healthy"
    else
        print_error "Backend: Unhealthy"
    fi
    
    # Check Frontend
    if curl -s "http://localhost:$FRONTEND_PORT" >/dev/null; then
        print_status "Frontend: Healthy"
    else
        print_error "Frontend: Unhealthy"
    fi
}

# Function to stop services
stop_services() {
    print_info "Stopping all services..."
    
    # Stop frontend
    if [ -f "$FRONTEND_PID_FILE" ]; then
        FRONTEND_PID=$(cat $FRONTEND_PID_FILE)
        if kill -0 $FRONTEND_PID 2>/dev/null; then
            kill $FRONTEND_PID
            print_status "Frontend stopped"
        fi
        rm -f $FRONTEND_PID_FILE
    fi
    
    # Stop backend
    if [ -f "$BACKEND_PID_FILE" ]; then
        BACKEND_PID=$(cat $BACKEND_PID_FILE)
        if kill -0 $BACKEND_PID 2>/dev/null; then
            kill $BACKEND_PID
            print_status "Backend stopped"
        fi
        rm -f $BACKEND_PID_FILE
    fi
    
    # Stop Ollama
    if [ -f "$OLLAMA_PID_FILE" ]; then
        OLLAMA_PID=$(cat $OLLAMA_PID_FILE)
        if kill -0 $OLLAMA_PID 2>/dev/null; then
            kill $OLLAMA_PID
            print_status "Ollama stopped"
        fi
        rm -f $OLLAMA_PID_FILE
    fi
    
    # Kill any remaining processes
    pkill -f "ollama serve" 2>/dev/null || true
    pkill -f "streamlit run app.py" 2>/dev/null || true
    pkill -f "python run.py" 2>/dev/null || true
    
    print_status "All services stopped"
}

# Function to show service status
show_status() {
    print_info "Service Status:"
    echo "=============="
    
    # Ollama status
    if check_port $OLLAMA_PORT; then
        echo -e "Ollama:   ${GREEN}Running${NC} (http://localhost:$OLLAMA_PORT)"
    else
        echo -e "Ollama:   ${RED}Stopped${NC}"
    fi
    
    # Backend status
    if check_port $BACKEND_PORT; then
        echo -e "Backend:  ${GREEN}Running${NC} (http://localhost:$BACKEND_PORT)"
    else
        echo -e "Backend:  ${RED}Stopped${NC}"
    fi
    
    # Frontend status
    if check_port $FRONTEND_PORT; then
        echo -e "Frontend: ${GREEN}Running${NC} (http://localhost:$FRONTEND_PORT)"
    else
        echo -e "Frontend: ${RED}Stopped${NC}"
    fi
    
    echo ""
    echo "Log files:"
    echo "- Ollama:   /tmp/ollama.log"
    echo "- Backend:  /tmp/backend.log"
    echo "- Frontend: /tmp/frontend.log"
}

# Function to show logs
show_logs() {
    local service=$1
    
    case $service in
        "ollama")
            tail -f /tmp/ollama.log
            ;;
        "backend")
            tail -f /tmp/backend.log
            ;;
        "frontend")
            tail -f /tmp/frontend.log
            ;;
        *)
            print_error "Unknown service: $service"
            print_info "Available services: ollama, backend, frontend"
            ;;
    esac
}

# Main function
main() {
    case "${1:-start}" in
        "start")
            print_info "Starting all services..."
            
            # Start services in order
            start_ollama || exit 1
            start_backend || exit 1
            start_frontend || exit 1
            
            echo ""
            echo "=========================================="
            print_status "All services started successfully!"
            echo ""
            echo "🌐 Access the application:"
            echo "   Frontend: http://localhost:$FRONTEND_PORT"
            echo "   Backend API: http://localhost:$BACKEND_PORT"
            echo "   Ollama API: http://localhost:$OLLAMA_PORT"
            echo ""
            echo "📋 Management commands:"
            echo "   Status: $0 status"
            echo "   Stop: $0 stop"
            echo "   Health: $0 health"
            echo "   Logs: $0 logs [service]"
            echo "=========================================="
            ;;
        
        "stop")
            stop_services
            ;;
        
        "restart")
            stop_services
            sleep 2
            main start
            ;;
        
        "status")
            show_status
            ;;
        
        "health")
            check_health
            ;;
        
        "logs")
            show_logs "$2"
            ;;
        
        *)
            echo "Usage: $0 {start|stop|restart|status|health|logs [service]}"
            echo ""
            echo "Commands:"
            echo "  start    - Start all services"
            echo "  stop     - Stop all services"
            echo "  restart  - Restart all services"
            echo "  status   - Show service status"
            echo "  health   - Check service health"
            echo "  logs     - Show logs for a service (ollama|backend|frontend)"
            exit 1
            ;;
    esac
}

# Handle script interruption
trap 'print_warning "Script interrupted. Use '$0' stop to clean up."; exit 1' INT TERM

# Run main function
main "$@"
