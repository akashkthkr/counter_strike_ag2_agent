# Counter-Strike AG2 Docker Architecture

This document describes the complete Docker-based microservices architecture and API call flows for the Counter-Strike AG2 Multi-Agent System.

## 🏗️ Docker Architecture Overview

```mermaid
graph TB
    subgraph "Host System"
        USER[👤 User Browser]
        PORTS[🔌 Port Mappings<br/>8080: API<br/>8081: Agents<br/>8082: Web UI<br/>5432: PostgreSQL<br/>8000: ChromaDB]
    end

    subgraph "Docker Network: cs_network"
        subgraph "Frontend Services"
            WEBUI[🌐 Web UI Service<br/>Port: 8082<br/>FastAPI + WebSocket<br/>Jinja2 Templates]
        end

        subgraph "Backend API Services"
            API[📡 API Service<br/>Port: 8080<br/>FastAPI + WebSocket<br/>Game State Management]
            AGENTS[🤖 Agent Service<br/>Port: 8081<br/>AG2 Multi-Agent<br/>AI Processing]
        end

        subgraph "Data Layer"
            POSTGRES[🗄️ PostgreSQL<br/>Port: 5432<br/>Game Sessions<br/>Player States<br/>Action Logs]
            CHROMADB[🔍 ChromaDB<br/>Port: 8000<br/>Vector Database<br/>RAG Knowledge Base]
        end
    end

    %% User interactions
    USER -->|HTTP/WebSocket| WEBUI
    USER -->|Direct API| API
    USER -->|Direct Agents| AGENTS

    %% Frontend to Backend
    WEBUI -->|REST API| API
    WEBUI -->|Agent Queries| AGENTS

    %% Backend API flows
    API -->|Game State| POSTGRES
    API -->|Vector Search| CHROMADB

    %% Agent Service flows
    AGENTS -->|Context Data| POSTGRES
    AGENTS -->|RAG Queries| CHROMADB

    %% Port mappings
    PORTS -.->|8082| WEBUI
    PORTS -.->|8080| API
    PORTS -.->|8081| AGENTS
    PORTS -.->|5432| POSTGRES

    PORTS -.->|8000| CHROMADB

    style USER fill:#e1f5fe
    style WEBUI fill:#f3e5f5
    style API fill:#e8f5e8
    style AGENTS fill:#fff3e0
    style POSTGRES fill:#e3f2fd

    style CHROMADB fill:#f1f8e9
```

## 🔄 API Call Flow Diagrams

### 1. User Action Flow (Game Commands)

```mermaid
sequenceDiagram
    participant User as 👤 User Browser
    participant WebUI as 🌐 Web UI Service
    participant API as 📡 API Service
    participant DB as 🗄️ PostgreSQL
    User->>WebUI: POST /api/terrorist/0/input<br/>{"text": "shoot player"}
    WebUI->>API: POST /sessions/{id}/actions<br/>{"team": "Terrorists", "action": "shoot player"}
    API->>DB: INSERT INTO game_actions
    API->>DB: UPDATE player_states
    API->>DB: SELECT game_state
    DB-->>API: Updated game state
    API-->>WebUI: {"result": "Hit for 30 damage", "game_state": {...}}
    WebUI->>WebUI: Update chat logs
    WebUI-->>User: WebSocket update<br/>Real-time UI refresh
```

### 2. AI Agent Query Flow

```mermaid
sequenceDiagram
    participant User as 👤 User Browser
    participant WebUI as 🌐 Web UI Service
    participant Agents as 🤖 Agent Service
    participant ChromaDB as 🔍 ChromaDB


    User->>WebUI: POST /api/terrorist/0/input<br/>{"text": "rag: what should we do?"}
    WebUI->>Agents: POST /process<br/>{"agent_type": "rag", "query": "what should we do?"}
    Agents->>ChromaDB: POST /api/v1/collections/cs_kb/query<br/>{"query_texts": ["what should we do?"]}
    ChromaDB-->>Agents: {"documents": ["tactical advice..."]}
    Agents->>Agents: Process with RAG Helper
    Agents-->>WebUI: {"success": true, "response": "Group up and execute fast hit"}
    WebUI->>WebUI: Update chat log
    WebUI-->>User: WebSocket update<br/>AI response displayed
```

### 3. Complex AG2 Agent Processing

```mermaid
sequenceDiagram
    participant User as 👤 User Browser
    participant WebUI as 🌐 Web UI Service
    participant Agents as 🤖 Agent Service
    participant Celery as ⚙️ Celery Worker

    participant DB as 🗄️ PostgreSQL

    User->>WebUI: POST /api/terrorist/0/input<br/>{"text": "ag2: analyze current situation"}
    WebUI->>Agents: POST /process<br/>{"agent_type": "ag2", "query": "analyze situation"}
    
    alt Synchronous Processing
        Agents->>Agents: Load AG2 GroupChat
        Agents->>Agents: Generate agent response
        Agents-->>WebUI: {"success": true, "response": "Tactical analysis..."}
    end

    WebUI-->>User: WebSocket update<br/>Response displayed
```

### 4. Real-time WebSocket Updates

```mermaid
sequenceDiagram
    participant User1 as 👤 User 1 (T1)
    participant User2 as 👤 User 2 (T2)
    participant WebUI as 🌐 Web UI Service
    participant API as 📡 API Service

    User1->>WebUI: WebSocket connection
    User2->>WebUI: WebSocket connection
    WebUI->>WebUI: Store connections[]

    User1->>WebUI: POST /api/terrorist/0/input<br/>{"text": "plant bomb"}
    WebUI->>API: Game action
    API-->>WebUI: Action result
    
    WebUI->>WebUI: Update panel 0 chat
    WebUI->>WebUI: Broadcast to panels 1,2<br/>"T1: plant bomb"
    
    WebUI-->>User1: WebSocket: Updated panel 0
    WebUI-->>User2: WebSocket: Updated panel 1<br/>Shows T1's action
```

## 🐳 Container Communication

### Internal Docker Network

All services communicate within the `cs_network` Docker network using container names as hostnames:

```yaml
# Service Discovery
API_URL=http://api:8080           # Web UI → API Service
AGENT_URL=http://agent_service:8081  # Web UI → Agent Service
DATABASE_URL=postgresql://cs_user:cs_password@postgres:5432/counter_strike_db

CHROMA_URL=http://chromadb:8000
```

### Port Mapping Strategy

```
Host Port → Container Port → Service
8080      → 8080           → API Service (FastAPI)
8081      → 8081           → Agent Service (AG2)
8082      → 8082           → Web UI Service (Frontend)
5432      → 5432           → PostgreSQL Database

8000      → 8000           → ChromaDB Vector Store
```

## 📊 Service Dependencies & Startup Order

```mermaid
graph TD
    A[PostgreSQL] --> B[API Service]

    D[ChromaDB] --> B
    
    A --> F[Agent Service]
    D --> F
    
    B --> G[Web UI Service]
    F --> G

    style A fill:#e3f2fd
    style D fill:#f1f8e9
    style B fill:#e8f5e8
    style F fill:#fff3e0
    style G fill:#f3e5f5
```

### Health Check Chain

```bash
# Startup sequence with health checks
1. PostgreSQL, ChromaDB (parallel)
2. Wait for databases to be healthy
3. API Service, Agent Service (parallel)
4. Web UI Service (depends on API + Agents)
```

## 🔧 Configuration & Environment

### Shared Environment Variables

```bash
# Database connections
DATABASE_URL=postgresql://cs_user:cs_password@postgres:5432/counter_strike_db

CHROMA_URL=http://chromadb:8000

# Service URLs
API_URL=http://api:8080
AGENT_URL=http://agent_service:8081

# AI Configuration
ANTHROPIC_API_KEY=sk-ant-...
OPENAI_API_KEY=sk-...
OAI_CONFIG_LIST='[{"model":"claude-3-5-sonnet-20240620","api_type":"anthropic","api_key":"..."}]'
```

### Volume Mounts

```yaml
volumes:
  # Persistent data
  - postgres_data:/var/lib/postgresql/data
  
  - chroma_data:/chroma/chroma
  
  # Application logs
  - ./logs:/app/logs
  
  # Web UI assets (development)
  - ./templates:/app/templates
  - ./static:/app/static
```

## 🚀 Deployment Commands

### Build and Start

```bash
# Build all services
docker compose build

# Start core services
docker compose up -d postgres chromadb

# Start application services
docker compose up -d api agent_service

# Start web interface
docker compose up -d web_ui

# Or start everything at once
./run_docker.sh
```

### Monitoring

```bash
# Check service status
docker compose ps

# View logs
docker compose logs -f api
docker compose logs -f agent_service
docker compose logs -f web_ui

# Monitor resource usage
docker stats

# Health checks
curl http://localhost:8080/health
curl http://localhost:8081/health
curl http://localhost:8082/api/state
```

## 🔍 Troubleshooting

### Common Issues

1. **Service Communication Failures**
   ```bash
   # Check network connectivity
   docker compose exec api ping postgres
   docker compose exec web_ui curl http://api:8080/health
   ```

2. **Database Connection Issues**
   ```bash
   # Check PostgreSQL
   docker compose exec postgres pg_isready -U cs_user
   

   ```

3. **Agent Processing Failures**
   ```bash
   # Check AG2 configuration
   docker compose exec agent_service env | grep OAI_CONFIG_LIST
   
   # Test agent endpoint
   curl -X POST http://localhost:8081/process \
     -H "Content-Type: application/json" \
     -d '{"agent_type": "rag", "query": "test", "context": {}}'
   ```

### Performance Tuning

```yaml
# Adjust worker concurrency
celery_worker:
  command: celery -A services.celery_app worker --concurrency=8

# Database connection pooling
environment:
  - DATABASE_POOL_SIZE=20
  - DATABASE_MAX_OVERFLOW=30

# Memory limits
deploy:
  resources:
    limits:
      memory: 1G
      cpus: '0.5'
```

## 🏆 Architecture Benefits

1. **🔄 Scalability**: Each service can be scaled independently
2. **🛡️ Isolation**: Service failures don't cascade
3. **🔧 Maintainability**: Clear separation of concerns
4. **📊 Observability**: Individual service monitoring
5. **🚀 Deployment**: Easy to deploy and update
6. **🌐 Accessibility**: Web-based UI works anywhere
7. **💾 Persistence**: Data survives container restarts

This architecture provides a robust, scalable foundation for the Counter-Strike AG2 Multi-Agent System with clear API boundaries and efficient inter-service communication.
