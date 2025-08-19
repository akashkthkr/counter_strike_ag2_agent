#!/bin/bash

# Counter-Strike AG2 Docker Startup Script

set -e

echo "🚀 Starting Counter-Strike AG2 Multi-Agent System with Docker..."

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo "⚠️  No .env file found. Copying from env.example..."
    cp env.example .env
    echo "📝 Please edit .env file with your API keys before running again."
    exit 1
fi

# Load environment variables (safely handle special characters)
echo "📋 Loading environment variables..."
if [ -f ".env" ]; then
    set -a  # automatically export all variables
    source .env 2>/dev/null || {
        echo "❌ Error loading .env file. Please check for syntax errors."
        echo "Common issues:"
        echo "  - Unquoted values with special characters"
        echo "  - Missing quotes around values with spaces"
        echo "  - Array syntax (use comma-separated strings instead)"
        exit 1
    }
    set +a  # stop automatically exporting
    echo "✅ Environment variables loaded successfully"
else
    echo "❌ .env file not found"
    exit 1
fi

# Check required environment variables
required_vars=("ANTHROPIC_API_KEY" "DATABASE_URL" "REDIS_URL" "CHROMA_URL")
missing_vars=()

for var in "${required_vars[@]}"; do
    if [ -z "${!var}" ]; then
        missing_vars+=("$var")
    fi
done

if [ ${#missing_vars[@]} -gt 0 ]; then
    echo "❌ Missing required environment variables:"
    for var in "${missing_vars[@]}"; do
        echo "   - $var"
    done
    echo ""
    echo "Please check your .env file and ensure all required variables are set."
    echo "You can copy from env.example: cp env.example .env"
    exit 1
fi

echo "✅ All required environment variables are set"

# Create necessary directories
echo "📁 Creating directories..."
mkdir -p logs
mkdir -p .chroma

# Web UI runs entirely in Docker - no X11 setup needed!
echo "🌐 Using web-based UI - no X11 dependencies required!"

# Build and start services
echo "🐳 Building Docker images..."
docker compose build

echo "🚀 Starting services..."
docker compose up -d postgres redis chromadb

echo "⏳ Waiting for databases to be ready..."
sleep 10

echo "🤖 Starting API and Agent services..."
docker compose up -d api celery_worker celery_beat agent_service

echo "⏳ Waiting for services to be ready..."
sleep 5

# Check service health
echo "🩺 Checking service health..."
services=("postgres:5432" "redis:6379" "chromadb:8000" "api:8080" "agent_service:8081")
for service in "${services[@]}"; do
    host=$(echo $service | cut -d':' -f1)
    port=$(echo $service | cut -d':' -f2)
    
    if docker compose exec -T $host sh -c "nc -z localhost $port" 2>/dev/null; then
        echo "✅ $service is healthy"
    else
        echo "❌ $service is not responding"
    fi
done

echo "🌐 Starting Web UI service..."
docker compose up -d web_ui

echo "⏳ Waiting for Web UI to be ready..."
sleep 3

# Check Web UI health
if curl -s http://localhost:8082/api/state > /dev/null 2>&1; then
    echo "✅ Web UI is healthy"
else
    echo "⚠️  Web UI may still be starting up"
fi

echo "🎯 Counter-Strike AG2 system is running!"
echo ""
echo "📊 Service URLs:"
echo "   🌐 Web UI: http://localhost:8082"
echo "   📡 API: http://localhost:8080"
echo "   🤖 Agent Service: http://localhost:8081"
echo "   🔍 ChromaDB: http://localhost:8000"
echo "   🗄️  PostgreSQL: localhost:5432"
echo "   📦 Redis: localhost:6379"
echo ""
echo ""
echo "🎮 How to play:"
echo "   1. Open your browser to: http://localhost:8082"
echo "   2. Use the 3 Terrorist panels and 1 CT panel"
echo "   3. Type commands like: 'shoot player', 'plant bomb', 'rag: what should we do?'"
echo "   4. Watch real-time updates across all panels!"
echo ""
echo "🛑 To stop all services: docker compose down"
echo "🗑️  To stop and remove volumes: docker compose down -v"
