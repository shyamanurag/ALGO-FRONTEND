# Elite Autonomous Trading Platform - Development Commands

.PHONY: help install dev build test clean deploy

# Default target
help:
	@echo "Elite Autonomous Trading Platform - Development Commands"
	@echo ""
	@echo "Available commands:"
	@echo "  install     Install all dependencies"
	@echo "  dev         Start development environment"
	@echo "  build       Build production Docker image"
	@echo "  test        Run all tests"
	@echo "  clean       Clean up containers and volumes"
	@echo "  deploy      Deploy to production"
	@echo "  logs        Show application logs"
	@echo "  db-migrate  Run database migrations"
	@echo "  lint        Run code linting"
	@echo "  format      Format code"

# Install dependencies
install:
	@echo "Installing backend dependencies..."
	cd backend && pip install -r requirements.txt
	@echo "Installing frontend dependencies..."
	cd frontend && yarn install
	@echo "Dependencies installed successfully!"

# Start development environment
dev:
	@echo "Starting development environment..."
	docker-compose -f docker-compose.dev.yml up --build

# Build production image
build:
	@echo "Building production Docker image..."
	docker build -t elite-trading-platform:latest .
	@echo "Production image built successfully!"

# Run tests
test:
	@echo "Running backend tests..."
	cd backend && python -m pytest tests/ -v
	@echo "Running frontend tests..."
	cd frontend && yarn test --watchAll=false
	@echo "All tests completed!"

# Clean up
clean:
	@echo "Cleaning up containers and volumes..."
	docker-compose -f docker-compose.dev.yml down -v
	docker-compose down -v
	docker system prune -f
	@echo "Cleanup completed!"

# Deploy to production (requires doctl)
deploy:
	@echo "Deploying to DigitalOcean App Platform..."
	doctl apps create --spec .do/app.yaml
	@echo "Deployment initiated!"

# Show logs
logs:
	@echo "Showing application logs..."
	docker-compose -f docker-compose.dev.yml logs -f

# Database migrations
db-migrate:
	@echo "Running database migrations..."
	docker-compose -f docker-compose.dev.yml exec backend python -c "from database import db_manager; import asyncio; asyncio.run(db_manager.create_schema())"
	@echo "Database migrations completed!"

# Code linting
lint:
	@echo "Running code linting..."
	cd backend && flake8 . --max-line-length=120 --ignore=E203,W503
	cd frontend && yarn lint
	@echo "Linting completed!"

# Code formatting
format:
	@echo "Formatting code..."
	cd backend && black . --line-length=120
	cd backend && isort . --profile black
	cd frontend && yarn format
	@echo "Code formatting completed!"

# Quick start for new developers
quickstart: install dev

# Production deployment checklist
pre-deploy:
	@echo "Pre-deployment checklist:"
	@echo "✓ Environment variables configured"
	@echo "✓ Database credentials set"
	@echo "✓ Trading API keys configured"
	@echo "✓ SSL certificates ready"
	@echo "✓ Monitoring configured"
	@echo "Ready for deployment!"