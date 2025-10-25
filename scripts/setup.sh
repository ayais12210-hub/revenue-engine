#!/bin/bash

# Revenue Engine Setup Script
# This script sets up the complete revenue generation system

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Check prerequisites
check_prerequisites() {
    log_info "Checking prerequisites..."
    
    local missing_deps=()
    
    if ! command_exists python3; then
        missing_deps+=("python3")
    fi
    
    if ! command_exists node; then
        missing_deps+=("node")
    fi
    
    if ! command_exists docker; then
        missing_deps+=("docker")
    fi
    
    if ! command_exists docker-compose; then
        missing_deps+=("docker-compose")
    fi
    
    if ! command_exists pnpm; then
        missing_deps+=("pnpm")
    fi
    
    if [ ${#missing_deps[@]} -ne 0 ]; then
        log_error "Missing dependencies: ${missing_deps[*]}"
        log_info "Please install the missing dependencies and run this script again."
        exit 1
    fi
    
    log_success "All prerequisites are installed"
}

# Setup environment
setup_environment() {
    log_info "Setting up environment..."
    
    # Copy environment files if they don't exist
    if [ ! -f .env ]; then
        if [ -f .env.example ]; then
            cp .env.example .env
            log_success "Created .env file from .env.example"
            log_warning "Please update .env with your actual values"
        else
            log_error ".env.example not found"
            exit 1
        fi
    else
        log_info ".env file already exists"
    fi
    
    # Copy frontend environment file
    if [ ! -f web/copykit-landing/.env ]; then
        if [ -f web/copykit-landing/.env.example ]; then
            cp web/copykit-landing/.env.example web/copykit-landing/.env
            log_success "Created frontend .env file"
        fi
    fi
}

# Install Python dependencies
install_python_deps() {
    log_info "Installing Python dependencies..."
    
    # API dependencies
    if [ -f api/requirements.txt ]; then
        pip install -r api/requirements.txt
        log_success "Installed API dependencies"
    else
        log_error "api/requirements.txt not found"
        exit 1
    fi
    
    # Automation dependencies
    if [ -f automations/requirements.txt ]; then
        pip install -r automations/requirements.txt
        log_success "Installed automation dependencies"
    fi
    
    # Test dependencies
    if [ -f tests/requirements.txt ]; then
        pip install -r tests/requirements.txt
        log_success "Installed test dependencies"
    fi
}

# Install Node.js dependencies
install_node_deps() {
    log_info "Installing Node.js dependencies..."
    
    cd web/copykit-landing
    
    if [ -f package.json ]; then
        pnpm install
        log_success "Installed frontend dependencies"
    else
        log_error "package.json not found in web/copykit-landing"
        exit 1
    fi
    
    cd ../..
}

# Setup database
setup_database() {
    log_info "Setting up database..."
    
    # Check if DATABASE_URL is set
    if [ -z "$DATABASE_URL" ]; then
        log_warning "DATABASE_URL not set, skipping database setup"
        log_info "Please set DATABASE_URL in your .env file and run: python scripts/migrate.py"
        return
    fi
    
    # Run database migrations
    if [ -f scripts/migrate.py ]; then
        python scripts/migrate.py
        log_success "Database migrations completed"
    else
        log_error "Migration script not found"
        exit 1
    fi
}

# Build Docker images
build_docker_images() {
    log_info "Building Docker images..."
    
    # Build API image
    if [ -f Dockerfile ]; then
        docker build -t revenue-engine-api .
        log_success "Built API Docker image"
    else
        log_warning "Dockerfile not found, skipping API image build"
    fi
    
    # Build frontend image
    if [ -f web/copykit-landing/Dockerfile ]; then
        cd web/copykit-landing
        docker build -t revenue-engine-frontend .
        log_success "Built frontend Docker image"
        cd ../..
    else
        log_warning "Frontend Dockerfile not found, skipping frontend image build"
    fi
}

# Run tests
run_tests() {
    log_info "Running tests..."
    
    # Run Python tests
    if [ -f tests/e2e_tests.py ]; then
        log_info "Running E2E tests..."
        python -m pytest tests/e2e_tests.py -v || log_warning "Some tests failed"
    fi
    
    # Run frontend tests
    cd web/copykit-landing
    if [ -f package.json ] && grep -q "test" package.json; then
        log_info "Running frontend tests..."
        pnpm test || log_warning "Some frontend tests failed"
    fi
    cd ../..
}

# Start services
start_services() {
    log_info "Starting services..."
    
    if [ -f docker-compose.yml ]; then
        # Start core services
        docker-compose up -d postgres redis
        
        # Wait for services to be ready
        log_info "Waiting for services to be ready..."
        sleep 10
        
        # Start API
        docker-compose up -d api
        
        # Wait for API to be ready
        log_info "Waiting for API to be ready..."
        sleep 15
        
        # Start frontend
        docker-compose up -d frontend
        
        log_success "All services started"
        log_info "API: http://localhost:5000"
        log_info "Frontend: http://localhost:3000"
        log_info "Database: localhost:5432"
    else
        log_error "docker-compose.yml not found"
        exit 1
    fi
}

# Show status
show_status() {
    log_info "Checking service status..."
    
    # Check API health
    if curl -s http://localhost:5000/health > /dev/null 2>&1; then
        log_success "API is healthy"
    else
        log_warning "API is not responding"
    fi
    
    # Check frontend
    if curl -s http://localhost:3000 > /dev/null 2>&1; then
        log_success "Frontend is running"
    else
        log_warning "Frontend is not responding"
    fi
    
    # Check database
    if docker-compose ps postgres | grep -q "Up"; then
        log_success "Database is running"
    else
        log_warning "Database is not running"
    fi
}

# Cleanup function
cleanup() {
    log_info "Cleaning up..."
    docker-compose down
    log_success "Cleanup completed"
}

# Main function
main() {
    echo "=========================================="
    echo "Revenue Engine Setup Script"
    echo "=========================================="
    echo
    
    # Parse command line arguments
    case "${1:-setup}" in
        "setup")
            check_prerequisites
            setup_environment
            install_python_deps
            install_node_deps
            setup_database
            build_docker_images
            start_services
            show_status
            ;;
        "start")
            start_services
            show_status
            ;;
        "stop")
            cleanup
            ;;
        "test")
            run_tests
            ;;
        "status")
            show_status
            ;;
        "migrate")
            setup_database
            ;;
        "help"|"-h"|"--help")
            echo "Usage: $0 [command]"
            echo
            echo "Commands:"
            echo "  setup    - Complete setup (default)"
            echo "  start    - Start all services"
            echo "  stop     - Stop all services"
            echo "  test     - Run tests"
            echo "  status   - Show service status"
            echo "  migrate  - Run database migrations"
            echo "  help     - Show this help"
            ;;
        *)
            log_error "Unknown command: $1"
            echo "Use '$0 help' for available commands"
            exit 1
            ;;
    esac
    
    echo
    echo "=========================================="
    log_success "Setup completed successfully!"
    echo "=========================================="
}

# Trap to ensure cleanup on script exit
trap cleanup EXIT

# Run main function
main "$@"