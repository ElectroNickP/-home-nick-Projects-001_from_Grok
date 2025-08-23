#!/bin/bash

# Development Environment Setup Script
# Telegram Bot Manager - Hexagonal Architecture

set -e

echo "🚀 Setting up development environment for Telegram Bot Manager..."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if Python 3.11+ is available
check_python() {
    print_status "Checking Python version..."
    
    if command -v python3.11 &> /dev/null; then
        PYTHON_CMD="python3.11"
        print_success "Found Python 3.11"
    elif command -v python3.12 &> /dev/null; then
        PYTHON_CMD="python3.12"
        print_success "Found Python 3.12"
    elif command -v python3 &> /dev/null; then
        PYTHON_VERSION=$(python3 --version | cut -d' ' -f2 | cut -d'.' -f1,2)
        if [[ "$PYTHON_VERSION" > "3.10" ]]; then
            PYTHON_CMD="python3"
            print_success "Found Python $PYTHON_VERSION"
        else
            print_error "Python 3.11+ is required. Found: $PYTHON_VERSION"
            exit 1
        fi
    else
        print_error "Python 3.11+ is not installed"
        exit 1
    fi
}

# Create virtual environment
create_venv() {
    print_status "Creating virtual environment..."
    
    if [ -d "venv" ]; then
        print_warning "Virtual environment already exists. Removing..."
        rm -rf venv
    fi
    
    $PYTHON_CMD -m venv venv
    print_success "Virtual environment created"
}

# Activate virtual environment
activate_venv() {
    print_status "Activating virtual environment..."
    source venv/bin/activate
    print_success "Virtual environment activated"
}

# Install dependencies
install_dependencies() {
    print_status "Installing dependencies..."
    
    # Upgrade pip
    pip install --upgrade pip
    
    # Install main dependencies
    pip install -r requirements.txt
    
    # Install development dependencies
    pip install -e ".[dev]"
    
    print_success "Dependencies installed"
}

# Install pre-commit hooks
install_pre_commit() {
    print_status "Installing pre-commit hooks..."
    
    if command -v pre-commit &> /dev/null; then
        pre-commit install
        print_success "Pre-commit hooks installed"
    else
        print_warning "pre-commit not found. Install it manually: pip install pre-commit"
    fi
}

# Create necessary directories
create_directories() {
    print_status "Creating directory structure..."
    
    # Create new architecture directories
    mkdir -p apps/{api,admin,bots,workers}
    mkdir -p core/{domain,usecases,ports}
    mkdir -p adapters/{telegram,updater,storage,web}
    mkdir -p infra/{config,logging,scripts}
    mkdir -p tests/{unit,integration,e2e,contract}
    mkdir -p docs
    
    # Create __init__.py files
    touch apps/__init__.py
    touch apps/api/__init__.py
    touch apps/admin/__init__.py
    touch apps/bots/__init__.py
    touch apps/workers/__init__.py
    
    touch core/__init__.py
    touch core/domain/__init__.py
    touch core/usecases/__init__.py
    touch core/ports/__init__.py
    
    touch adapters/__init__.py
    touch adapters/telegram/__init__.py
    touch adapters/updater/__init__.py
    touch adapters/storage/__init__.py
    touch adapters/web/__init__.py
    
    touch infra/__init__.py
    touch infra/config/__init__.py
    touch infra/logging/__init__.py
    touch infra/scripts/__init__.py
    
    touch tests/__init__.py
    touch tests/unit/__init__.py
    touch tests/integration/__init__.py
    touch tests/e2e/__init__.py
    touch tests/contract/__init__.py
    
    print_success "Directory structure created"
}

# Run initial tests
run_tests() {
    print_status "Running initial tests..."
    
    # Run contract tests
    if [ -d "tests/contract" ]; then
        python -m pytest tests/contract/ -v
        print_success "Contract tests passed"
    fi
    
    # Run import linting
    if command -v lint-imports &> /dev/null; then
        lint-imports
        print_success "Import linting passed"
    else
        print_warning "import-linter not found. Install it manually: pip install import-linter"
    fi
}

# Create development configuration
create_dev_config() {
    print_status "Creating development configuration..."
    
    # Create .env file if it doesn't exist
    if [ ! -f ".env" ]; then
        cat > .env << EOF
# Development Environment Configuration
FLASK_ENV=development
FLASK_DEBUG=true
FLASK_PORT=60183

# Database (for future use)
DATABASE_URL=sqlite:///dev.db

# Logging
LOG_LEVEL=DEBUG
LOG_FILE=logs/dev.log

# Security (change in production)
SECRET_KEY=dev-secret-key-change-in-production
ADMIN_USERNAME=admin
ADMIN_PASSWORD=securepassword123

# OpenAI (add your keys)
OPENAI_API_KEY=your_openai_api_key_here
OPENAI_ASSISTANT_ID=your_assistant_id_here

# Telegram (add your bot token)
TELEGRAM_BOT_TOKEN=your_telegram_bot_token_here

# Auto-update
AUTO_UPDATE_ENABLED=true
GIT_REPO_URL=https://github.com/your-repo/telegram-bot-manager.git
EOF
        print_success "Development configuration created (.env)"
    else
        print_warning ".env file already exists"
    fi
}

# Main setup function
main() {
    echo "🏗️  Telegram Bot Manager - Development Setup"
    echo "=============================================="
    
    check_python
    create_venv
    activate_venv
    install_dependencies
    create_directories
    install_pre_commit
    create_dev_config
    
    echo ""
    echo "🎉 Development environment setup complete!"
    echo ""
    echo "Next steps:"
    echo "1. Edit .env file with your API keys"
    echo "2. Activate virtual environment: source venv/bin/activate"
    echo "3. Run tests: python -m pytest"
    echo "4. Start development: python src/app.py"
    echo ""
    echo "📚 Documentation:"
    echo "- Architecture: docs/ARCHITECTURE_BRIEF.md"
    echo "- Migration Plan: docs/MIGRATION_PLAN.md"
    echo ""
    echo "🔧 Quality Tools:"
    echo "- Code formatting: black ."
    echo "- Linting: ruff check ."
    echo "- Type checking: mypy ."
    echo "- Import checking: lint-imports"
    echo ""
}

# Run main function
main "$@"

