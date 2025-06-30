#!/bin/bash

# AI Observability RCA - Ollama Installation Script
# This script installs Ollama and downloads the Llama3 model

set -e

echo "🚀 Installing Ollama and Llama3 model for AI Observability RCA"
echo "================================================================"

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️ $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ️ $1${NC}"
}

# Check if running on supported OS
check_os() {
    if [[ "$OSTYPE" == "linux-gnu"* ]]; then
        print_status "Running on Linux"
        if command -v apt-get &> /dev/null; then
            DISTRO="ubuntu"
        elif command -v yum &> /dev/null; then
            DISTRO="centos"
        else
            print_warning "Unknown Linux distribution. Proceeding with generic installation."
            DISTRO="linux"
        fi
    elif [[ "$OSTYPE" == "darwin"* ]]; then
        print_status "Running on macOS"
        DISTRO="macos"
    else
        print_error "Unsupported OS: $OSTYPE"
        exit 1
    fi
}

# Check if Ollama is already installed
check_ollama_installed() {
    if command -v ollama &> /dev/null; then
        print_status "Ollama is already installed"
        ollama --version
        return 0
    else
        print_info "Ollama not found. Installing..."
        return 1
    fi
}

# Install Ollama
install_ollama() {
    print_info "Installing Ollama..."
    
    # Download and install Ollama
    curl -fsSL https://ollama.ai/install.sh | sh
    
    if command -v ollama &> /dev/null; then
        print_status "Ollama installed successfully"
        ollama --version
    else
        print_error "Ollama installation failed"
        exit 1
    fi
}

# Start Ollama service
start_ollama() {
    print_info "Starting Ollama service..."
    
    # Check if Ollama is already running
    if pgrep -f "ollama" > /dev/null; then
        print_status "Ollama service is already running"
    else
        # Start Ollama in background
        nohup ollama serve > /dev/null 2>&1 &
        
        # Wait a moment for service to start
        sleep 3
        
        if pgrep -f "ollama" > /dev/null; then
            print_status "Ollama service started successfully"
        else
            print_error "Failed to start Ollama service"
            exit 1
        fi
    fi
}

# Download Llama3 model
download_llama3() {
    print_info "Downloading Llama3 model (this may take a while)..."
    
    # Check if model is already downloaded
    if ollama list | grep -q "llama3"; then
        print_status "Llama3 model is already available"
        return 0
    fi
    
    # Download llama3 model
    echo "📥 Downloading Llama3 model..."
    echo "⏳ This may take 10-30 minutes depending on your internet connection..."
    
    ollama pull llama3
    
    if ollama list | grep -q "llama3"; then
        print_status "Llama3 model downloaded successfully"
    else
        print_error "Failed to download Llama3 model"
        exit 1
    fi
}

# Test Ollama and Llama3
test_ollama() {
    print_info "Testing Ollama with Llama3..."
    
    # Test with a simple prompt
    response=$(ollama run llama3 "Say 'Hello from Llama3!' and nothing else." 2>/dev/null || echo "")
    
    if [[ -n "$response" ]]; then
        print_status "Ollama and Llama3 are working correctly"
        echo "📝 Test response: $response"
    else
        print_warning "Ollama test failed or returned no response"
        print_info "This might be normal if the model is still initializing"
    fi
}

# Setup systemd service (Linux only)
setup_systemd_service() {
    if [[ "$DISTRO" == "ubuntu" ]] || [[ "$DISTRO" == "centos" ]] || [[ "$DISTRO" == "linux" ]]; then
        print_info "Setting up Ollama as a system service..."
        
        # Create systemd service file
        sudo tee /etc/systemd/system/ollama.service > /dev/null << EOF
[Unit]
Description=Ollama Service
After=network-online.target

[Service]
Type=exec
ExecStart=/usr/local/bin/ollama serve
User=ollama
Group=ollama
Restart=always
RestartSec=3
Environment="PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin:/usr/games:/usr/local/games:/snap/bin"

[Install]
WantedBy=default.target
EOF

        # Create ollama user
        sudo useradd -r -s /bin/false -m -d /usr/share/ollama ollama 2>/dev/null || true
        
        # Reload systemd and enable service
        sudo systemctl daemon-reload
        sudo systemctl enable ollama
        
        print_status "Ollama systemd service configured"
        print_info "Use 'sudo systemctl start ollama' to start the service"
        print_info "Use 'sudo systemctl status ollama' to check the service status"
    fi
}

# Print usage instructions
print_usage() {
    echo ""
    echo "================================================================"
    echo "🎉 Ollama installation completed successfully!"
    echo ""
    echo "📋 What was installed:"
    echo "   • Ollama CLI tool"
    echo "   • Llama3 language model"
    echo ""
    echo "🔧 Usage:"
    echo "   • Start Ollama: ollama serve"
    echo "   • List models: ollama list"
    echo "   • Chat with Llama3: ollama run llama3"
    echo ""
    echo "🌐 API Endpoint:"
    echo "   • Default: http://localhost:11434"
    echo "   • This is configured in your backend .env file"
    echo ""
    echo "🏥 Health Check:"
    echo "   • curl http://localhost:11434/api/tags"
    echo ""
    if [[ "$DISTRO" == "ubuntu" ]] || [[ "$DISTRO" == "centos" ]] || [[ "$DISTRO" == "linux" ]]; then
        echo "🔄 Service Management (Linux):"
        echo "   • Start: sudo systemctl start ollama"
        echo "   • Stop: sudo systemctl stop ollama"
        echo "   • Status: sudo systemctl status ollama"
        echo "   • Logs: sudo journalctl -u ollama -f"
        echo ""
    fi
    echo "📚 Next steps:"
    echo "   1. Ensure Ollama is running: ollama serve"
    echo "   2. Start the backend API: cd backend && python run.py"
    echo "   3. Start the frontend: cd frontend && streamlit run app.py"
    echo ""
    echo "================================================================"
}

# Main installation flow
main() {
    echo "Starting Ollama installation..."
    
    # Check OS compatibility
    check_os
    
    # Install Ollama if not present
    if ! check_ollama_installed; then
        install_ollama
    fi
    
    # Start Ollama service
    start_ollama
    
    # Download Llama3 model
    download_llama3
    
    # Test the installation
    test_ollama
    
    # Setup systemd service (Linux only)
    if [[ "$DISTRO" != "macos" ]]; then
        setup_systemd_service
    fi
    
    # Print usage instructions
    print_usage
}

# Run main function
main "$@"
