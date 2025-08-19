# Counter-Strike AG2 Multi-Agent System - Docker Deployment

This document describes how to run the Counter-Strike AG2 system using Docker containers with a microservices architecture.

## 🏗️ Architecture Overview

The system is decomposed into the following microservices:

### Core Services
- **API Service** (FastAPI) - REST API and WebSocket server for game state management
- **Agent Service** - AG2 multi-agent processing service
- **Web UI Service** - Browser-based user interface with real-time updates

### Data Services  
- **PostgreSQL** - Primary database for game sessions, states, and logs
- **ChromaDB** - Vector database for RAG knowledge base

## 🚀 Quick Start

### Prerequisites

1. **Docker & Docker Compose** installed
2. **API Keys** for AI services:
   - Anthropic API key (recommended)
   - OpenAI API key (optional)

### Setup Steps

1. **Clone and navigate to project**:
   ```bash
   cd counter_strike_ag2_agent
   ```

2. **Configure environment**:
   ```bash
   cp env.example .env
   # Edit .env with your API keys
   ```

3. **Start the system**:
   ```bash
   ./run_docker.sh
   ```

### Web Interface Access
After starting the system, access the game through your web browser at:
- **Game Interface**: http://localhost:8082

## 🔧 Configuration

### Environment Variables

Create a `.env` file with the following variables:

```bash
# Required API Keys
ANTHROPIC_API_KEY=sk-ant-your-key-here
OPENAI_API_KEY=sk-your-key-here

# AG2 Configuration (JSON string format recommended for Docker)
OAI_CONFIG_LIST='[{"model":"claude-3-5-sonnet-20240620","api_type":"anthropic","api_key":"sk-ant-your-key-here"}]'

# Database URLs (defaults work for Docker)
DATABASE_URL=postgresql://cs_user:cs_password@postgres:5432/counter_strike_db
CHROMA_URL=http://chromadb:8000

# Service Communication (internal Docker network)
API_URL=http://api:8080
AGENT_URL=http://agent_service:8081

# Optional Configuration
ENVIRONMENT=development
LOG_LEVEL=INFO
GAME_MAX_ROUNDS=3
DEBUG=false
```

### AG2 Configuration Options

You can configure AG2 agents in multiple ways:

1. **JSON String** (recommended for Docker):
   ```bash
   OAI_CONFIG_LIST='[{"model":"claude-3-5-sonnet-20240620","api_type":"anthropic","api_key":"sk-ant-..."}]'
   ```

2. **Config File Path**:
   ```bash
   OAI_CONFIG_LIST=/app/config/oai_config_list.json
   ```

3. **Environment Variable Fallback**:
   ```bash
   # Just set the API key, system will auto-configure
   ANTHROPIC_API_KEY=sk-ant-...
   ```

## 🐳 Docker Services

### Service Ports
- **Web UI**: `localhost:8082`
- **API Server**: `localhost:8080`
- **Agent Service**: `localhost:8081` 
- **ChromaDB**: `localhost:8000`
- **PostgreSQL**: `localhost:5432`

### Service Dependencies
```
Web UI Service
├── API Service
│   └── PostgreSQL
└── Agent Service
    ├── PostgreSQL
    └── ChromaDB
```

## 🎮 Usage

### Game Interface

Once started, the web interface will display multiple panels:
- **3 Terrorist Panels**: Individual player interfaces with real-time updates
- **1 Counter-Terrorist Panel**: CT team interface
- **Sound Effects**: Dynamic audio feedback for actions
- **Real-time Communication**: WebSocket-based instant updates

### Available Commands

#### Game Actions
- `shoot player` - Attack enemy player
- `shoot bot` - Attack enemy bot
- `plant bomb` - Plant bomb at current site
- `defuse bomb` - Defuse planted bomb
- `move to A-site` - Move to A bombsite
- `move to B-site` - Move to B bombsite

#### AI Queries
- `rag: <question>` - Query RAG knowledge base (fastest, ~50ms)
- `ag2: <question>` - Query AG2 agents (1-5s, uses LLM APIs)
- `smart: <question>` - Combined AG2 + RAG query (enhanced responses)
- `critic: <plan>` - Critique a strategy using specialized agent
- `quant: option1 | option2 | option3` - Rank options by effectiveness
- `som: <complex question>` - Society of Mind multi-expert reasoning

#### Knowledge Base Commands
- `kb:add <text>` - Add tactical knowledge to vector database
- `kb:load <file_path>` - Load knowledge from file
- `ask: <question>` - Semantic search through knowledge base

#### Utility Commands
- `cheat: status` - Show bomb status
- `cheat: hp` - Show all player health
- `cheat: next` - Vote to skip round

### API Endpoints

The FastAPI server provides REST and WebSocket APIs:

#### REST Endpoints
- `GET /health` - Service health check
- `POST /sessions` - Create new game session
- `GET /sessions` - List active sessions
- `GET /sessions/{id}/state` - Get game state
- `POST /sessions/{id}/actions` - Apply game action

#### WebSocket
- `WS /ws` - Real-time game updates for web UI

#### Agent Service Endpoints
- `POST /process` - Process AI agent requests directly

## 🔍 Monitoring & Debugging

### Service Logs
```bash
# View all service logs
docker-compose logs

# View specific service logs
docker-compose logs api
docker-compose logs agent_service
docker-compose logs web_ui

# Follow logs in real-time
docker-compose logs -f api
```

### Database Access
```bash
# Connect to PostgreSQL
docker-compose exec postgres psql -U cs_user -d counter_strike_db

# View game sessions
SELECT * FROM game_sessions;

# View recent actions
SELECT * FROM game_actions ORDER BY timestamp DESC LIMIT 10;
```



### ChromaDB Interface
- Web UI: http://localhost:8000
- API docs: http://localhost:8000/docs

## 🛠️ Development

### Building Images
```bash
# Build all images
docker-compose build

# Build specific service
docker-compose build api
```

### Running Individual Services
```bash
# Start only databases
docker-compose up -d postgres chromadb

# Start API service
docker-compose up api

# Start agent service
docker-compose up agent_service

# Start web UI
docker-compose up web_ui
```

### Testing
```bash
# Run tests in Docker
docker-compose exec api python -m pytest

# Run specific test suite
docker-compose exec api python -m pytest tests/test_agents.py
```

## 🚨 Troubleshooting

### Common Issues

#### Web UI Not Loading
- **Browser**: Ensure you're accessing http://localhost:8082
- **Network**: Check that port 8082 is not blocked by firewall
- **Services**: Verify web_ui container is running with `docker compose ps`

#### Agent API Errors
- Verify API keys in `.env` file
- Check `OAI_CONFIG_LIST` format
- Review agent service logs: `docker-compose logs agent_service`

#### Database Connection Issues
- Ensure PostgreSQL is healthy: `docker-compose ps postgres`
- Check database logs: `docker-compose logs postgres`
- Verify DATABASE_URL in `.env`

#### Service Communication Errors
- Check all services are running: `docker-compose ps`
- Verify network connectivity between containers
- Review API service logs for connection errors

### Health Checks
```bash
# Check all service health
curl http://localhost:8080/health
curl http://localhost:8081/health

# Check database connectivity
docker-compose exec postgres pg_isready -U cs_user

# Check web UI
curl http://localhost:8082
```

## 🧹 Cleanup

### Stop Services
```bash
# Stop all services
docker-compose down

# Stop and remove volumes (clears all data)
docker-compose down -v

# Remove images as well
docker-compose down -v --rmi all
```

### Reset Everything
```bash
# Complete cleanup
docker-compose down -v --rmi all
docker system prune -a
./run_docker.sh
```

## 📊 Performance Tuning

### Agent Processing
Adjust agent service resources in `docker-compose.yml`:
```yaml
agent_service:
  deploy:
    resources:
      limits:
        memory: 2G
        cpus: '1.0'
```

### Database Connections
Tune PostgreSQL connection pool in `services/database.py`:
```python
self.pool = await asyncpg.create_pool(self.database_url, min_size=10, max_size=50)
```

### Memory Limits
Add resource limits in `docker-compose.yml`:
```yaml
api:
  deploy:
    resources:
      limits:
        memory: 1G
        cpus: '0.5'
```

## 🔐 Security Considerations

1. **API Keys**: Never commit API keys to version control
2. **Database**: Change default passwords in production
3. **Network**: Use internal networks for service communication
4. **Secrets**: Use Docker secrets for sensitive data in production

## 📈 Scaling

For production deployment:

1. **Load Balancer**: Add nginx/traefik for API load balancing
2. **Multiple Agent Services**: Scale agent processing horizontally
3. **Database Replication**: Set up PostgreSQL read replicas
4. **CDN**: Use CDN for web UI static assets
5. **Container Orchestration**: Deploy with Kubernetes or Docker Swarm

## 🤝 Contributing

When developing new features:

1. Add appropriate Docker health checks
2. Update service dependencies in docker-compose.yml
3. Add environment variables to env.example
4. Update this documentation
5. Test with `docker-compose build && ./run_docker.sh`
