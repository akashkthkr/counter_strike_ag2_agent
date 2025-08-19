# Counter-Strike AG2 Multi-Agent System - Makefile

.PHONY: help setup docker-build docker-up docker-down docker-logs docker-clean test lint

# Default target
help:
	@echo "Counter-Strike AG2 Multi-Agent System"
	@echo ""
	@echo "Available commands:"
	@echo "  setup        - Initial setup (copy .env, create directories)"
	@echo "  docker-build - Build all Docker images"
	@echo "  docker-up    - Start all services"
	@echo "  docker-down  - Stop all services"
	@echo "  docker-logs  - View service logs"
	@echo "  docker-clean - Stop services and remove volumes"
	@echo "  test         - Run tests in Docker"
	@echo "  lint         - Run linting checks"
	@echo "  dev          - Start development environment"
	@echo "  db-shell     - Connect to PostgreSQL"


# Initial setup
setup:
	@echo "🚀 Setting up Counter-Strike AG2 system..."
	@if [ ! -f .env ]; then \
		cp env.example .env; \
		echo "📝 Created .env file. Please edit with your API keys."; \
	fi
	@mkdir -p logs .chroma
	@echo "✅ Setup complete!"

# Docker commands
docker-build:
	@echo "🐳 Building Docker images..."
	docker compose build

docker-up: setup
	@echo "🚀 Starting services..."
	@./run_docker.sh

docker-down:
	@echo "🛑 Stopping services..."
	docker compose down

docker-logs:
	@echo "📋 Service logs:"
	docker compose logs --tail=50

docker-clean:
	@echo "🧹 Cleaning up..."
	docker compose down -v --rmi local
	docker system prune -f

# Development
dev: setup
	@echo "🔧 Starting development environment..."
	docker compose up -d postgres chromadb
	@echo "⏳ Waiting for databases..."
	@sleep 10
	docker compose up api agent_service

# Testing
test:
	@echo "🧪 Running tests..."
	docker compose exec api python -m pytest tests/ -v

test-build:
	@echo "🧪 Running tests with fresh build..."
	docker compose build api
	docker compose run --rm api python -m pytest tests/ -v

# Linting
lint:
	@echo "🔍 Running linting checks..."
	docker compose exec api python -m flake8 counter_strike_ag2_agent/ services/
	docker compose exec api python -m mypy counter_strike_ag2_agent/ services/

# Database utilities
db-shell:
	@echo "🗄️  Connecting to PostgreSQL..."
	docker compose exec postgres psql -U cs_user -d counter_strike_db

db-reset:
	@echo "🔄 Resetting database..."
	docker compose down postgres
	docker volume rm counter_strike_ag2_agent_postgres_data || true
	docker compose up -d postgres



# Service status
status:
	@echo "📊 Service status:"
	@docker compose ps
	@echo ""
	@echo "🩺 Health checks:"
	@curl -s http://localhost:8080/health || echo "❌ API service not responding"
	@curl -s http://localhost:8081/health || echo "❌ Agent service not responding"

# Quick commands
restart: docker-down docker-up

rebuild: docker-clean docker-build docker-up

# Monitoring
monitor:
	@echo "📊 Monitoring services..."
	@echo "Press Ctrl+C to stop monitoring"
	watch -n 2 'docker compose ps && echo "" && docker stats --no-stream'

# Backup
backup:
	@echo "💾 Creating backup..."
	@mkdir -p backups
	@docker compose exec postgres pg_dump -U cs_user counter_strike_db > backups/db_backup_$(shell date +%Y%m%d_%H%M%S).sql
	@docker run --rm -v counter_strike_ag2_agent_chroma_data:/data -v $(PWD)/backups:/backup alpine tar czf /backup/chroma_backup_$(shell date +%Y%m%d_%H%M%S).tar.gz -C /data .
	@echo "✅ Backup created in backups/ directory"

# Production deployment (example)
deploy-prod:
	@echo "🚀 Deploying to production..."
	@echo "⚠️  Make sure to configure production environment variables!"
	docker compose -f docker compose.yml -f docker compose.prod.yml up -d
