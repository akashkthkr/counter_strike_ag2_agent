#!/bin/bash

# Counter-Strike AG2 Docker Startup Script (Headless - No UI)

set -e

echo "🚀 Starting Counter-Strike AG2 Multi-Agent System (Headless Mode)..."

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
required_vars=("ANTHROPIC_API_KEY" "DATABASE_URL" "CHROMA_URL")
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

echo "🖥️  Running in headless mode (no UI service)"

# Build and start services (excluding UI)
echo "🐳 Building Docker images..."
docker compose build

echo "🚀 Starting backend services..."
docker compose up -d postgres chromadb

echo "⏳ Waiting for databases to be ready..."
sleep 10

echo "🤖 Starting API and Agent services..."
docker compose up -d api agent_service

echo "⏳ Waiting for services to be ready..."
sleep 5

# Check service health
echo "🩺 Checking service health..."
services=("postgres:5432" "chromadb:8000" "api:8080" "agent_service:8081")
for service in "${services[@]}"; do
    host=$(echo $service | cut -d':' -f1)
    port=$(echo $service | cut -d':' -f2)
    
    if docker compose exec -T $host sh -c "nc -z localhost $port" 2>/dev/null; then
        echo "✅ $service is healthy"
    else
        echo "❌ $service is not responding"
    fi
done

echo ""
echo "🎯 Counter-Strike AG2 system is running in headless mode!"
echo ""
echo "📊 Service URLs:"
echo "   🌐 API Server: http://localhost:8080"
echo "   🤖 Agent Service: http://localhost:8081"
echo "   📊 API Documentation: http://localhost:8080/docs"
echo "   🔍 ChromaDB: http://localhost:8000"
echo "   🗄️  PostgreSQL: localhost:5432"
echo ""
echo "🎮 How to interact with the system:"
echo "   1. Use the API directly: curl http://localhost:8080/health"
echo "   2. Create a game session via API"
echo "   3. Send actions and queries via REST endpoints"
echo "   4. Use WebSocket for real-time updates: ws://localhost:8080/ws/{session_id}"
echo ""
echo "📚 API Documentation available at: http://localhost:8080/docs"
echo ""
echo "🛑 To stop all services: docker compose down"
echo "🗑️  To stop and remove volumes: docker compose down -v"
echo ""
echo "💡 To run with Web UI, use: ./run_docker.sh"

# Keep running and show logs
echo "📋 Following service logs (Ctrl+C to stop)..."
docker compose logs -f api agent_service