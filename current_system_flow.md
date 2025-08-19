# Current Counter-Strike AG2 System Flow Diagram

## Microservices Architecture Overview

```mermaid
graph TB
    subgraph "User Layer"
        BROWSER[Web Browser<br/>localhost:8082]
    end
    
    subgraph "Docker Network: cs_network"
        subgraph "Web UI Service (Port 8082)"
            WEBUI[Web UI Service<br/>FastAPI + WebSocket]
            TEMPLATES[Jinja2 Templates]
            STATIC[Static Assets]
        end
        
        subgraph "API Service (Port 8080)"
            API[API Server<br/>FastAPI REST]
            SESSION[Session Management]
            GAMELOGIC[Game State Logic]
        end
        
        subgraph "Agent Service (Port 8081)"
            AGENTS[Agent Service<br/>FastAPI]
            AG2[AG2 Multi-Agent System]
            RAG[RAG Helper]
            CONTRIB[Contrib Integration]
        end
        
        subgraph "Data Layer"
            POSTGRES[(PostgreSQL<br/>Port 5432)]
            CHROMA[(ChromaDB<br/>Port 8000)]
        end
    end
    
    subgraph "External Services"
        ANTHROPIC[Anthropic Claude API]
        OPENAI[OpenAI API]
    end
    
    BROWSER --> WEBUI
    WEBUI --> TEMPLATES
    WEBUI --> STATIC
    WEBUI --> API
    WEBUI --> AGENTS
    API --> SESSION
    API --> GAMELOGIC
    API --> POSTGRES
    AGENTS --> AG2
    AGENTS --> RAG
    AGENTS --> CONTRIB
    AGENTS --> POSTGRES
    AGENTS --> CHROMA
    AG2 --> ANTHROPIC
    AG2 --> OPENAI
    CONTRIB --> ANTHROPIC
    CONTRIB --> OPENAI
```

## Detailed Web-Based Command Flow

```mermaid
sequenceDiagram
    participant User as User Browser
    participant WebUI as Web UI Service
    participant API as API Service
    participant Agent as Agent Service
    participant DB as PostgreSQL
    participant Chroma as ChromaDB
    participant LLM as AI APIs
    
    User->>WebUI: Connect to localhost:8082
    WebUI-->>User: Game interface loaded (WebSocket connected)
    
    alt Regular Action (shoot, move, plant, defuse)
        User->>WebUI: "move to A-site" (WebSocket)
        WebUI->>API: POST /sessions/{id}/actions
        API->>DB: Update game state
        DB-->>API: State updated
        API-->>WebUI: Updated state (WebSocket broadcast)
        WebUI-->>User: Real-time UI update across all panels
    
    else RAG Query (rag: question)
        User->>WebUI: "rag: where are the enemies?" (WebSocket)
        WebUI->>Agent: POST /process (RAG request)
        Agent->>API: GET /sessions/{id}/state
        API->>DB: Get current game state
        DB-->>API: Game state data
        API-->>Agent: Game context
        Agent->>Agent: RAG Helper keyword matching
        Agent-->>WebUI: Heuristic answer (~50ms)
        WebUI-->>User: Fast tactical response
    
    else AG2 Query (ag2: question)
        User->>WebUI: "ag2: what should we do?" (WebSocket)
        WebUI->>Agent: POST /process (AG2 request)
        Agent->>API: GET /sessions/{id}/state
        API-->>Agent: Game context
        Agent->>LLM: Generate tactical advice
        LLM-->>Agent: AI response (1-5s)
        Agent-->>WebUI: Formatted response
        WebUI-->>User: AI tactical advice displayed
    
    else Smart Query (smart: question)
        User->>WebUI: "smart: best A-site strategy?" (WebSocket)
        WebUI->>Agent: POST /process (Smart request)
        Agent->>API: GET /sessions/{id}/state
        Agent->>Chroma: Vector similarity search
        Chroma-->>Agent: Relevant tactical knowledge
        Agent->>LLM: Generate enhanced response with context
        LLM-->>Agent: AI response with knowledge base context
        Agent-->>WebUI: Enhanced tactical response
        WebUI-->>User: Comprehensive advice displayed
    
    else Vector KB Operations (kb:add, ask:)
        User->>WebUI: "kb:add smoke lineups for Dust2" (WebSocket)
        WebUI->>Agent: POST /process (KB request)
        Agent->>Chroma: Add/query vector database
        Chroma-->>Agent: Operation result
        Agent-->>WebUI: KB operation response
        WebUI-->>User: Knowledge base updated/queried
    
    else Contrib Agents (critic:, quant:, som:)
        User->>WebUI: "critic: rush B with no utility" (WebSocket)
        WebUI->>Agent: POST /process (Contrib request)
        Agent->>API: GET /sessions/{id}/state
        Agent->>LLM: Specialized agent (Critic/Quantifier/SoM)
        LLM-->>Agent: Specialized analysis
        Agent-->>WebUI: Expert analysis response
        WebUI-->>User: Specialized AI feedback displayed
    
    else Cheat Commands (cheat:)
        User->>WebUI: "cheat: hp" (WebSocket)
        WebUI->>API: GET /sessions/{id}/state
        API->>DB: Direct state access
        DB-->>API: Detailed state information
        API-->>WebUI: Cheat information
        WebUI-->>User: Debug info displayed
    end
    
    Note over User,LLM: Real-time updates flow continuously
    API->>WebUI: State changes (WebSocket broadcast)
    WebUI->>User: Live UI updates across all panels
```

## Agent Creation and Management Flow

```mermaid
graph TB
    subgraph "Agent Initialization"
        START[System Start]
        CONFIG_LOAD[Load AG2 Config]
        CREATE_AGENTS[Create Terrorist Group]
    end
    
    subgraph "Agent Configuration"
        OAI_CONFIG[OAI_CONFIG_LIST]
        OPENAI_KEY[OPENAI_API_KEY]
        ANTHROPIC_KEY[ANTHROPIC_API_KEY]
        FALLBACK[No Config Fallback]
    end
    
    subgraph "Agent Types Created"
        USER_PROXY[UserProxyAgent - T Players]
        ASSISTANT[AssistantAgent - T Bot]
        GROUP_CHAT[GroupChat Container]
        MANAGER[GroupChatManager]
    end
    
    START --> CONFIG_LOAD
    CONFIG_LOAD --> OAI_CONFIG
    CONFIG_LOAD --> OPENAI_KEY
    CONFIG_LOAD --> ANTHROPIC_KEY
    CONFIG_LOAD --> FALLBACK
    
    CONFIG_LOAD --> CREATE_AGENTS
    CREATE_AGENTS --> USER_PROXY
    CREATE_AGENTS --> ASSISTANT
    CREATE_AGENTS --> GROUP_CHAT
    CREATE_AGENTS --> MANAGER
```

## Command Type Routing

```mermaid
flowchart TD
    INPUT[User Input] --> PARSE{Parse Command Type}
    
    PARSE -->|"action:"| GAME_ACTION[Game Action]
    PARSE -->|"rag:"| RAG_QUERY[RAG Query]
    PARSE -->|"ag2:"| AG2_QUERY[AG2 Agent Query]
    PARSE -->|"smart:"| SMART_QUERY[Smart Query]
    PARSE -->|"kb:add"| KB_ADD[Vector KB Add]
    PARSE -->|"kb:load"| KB_LOAD[Vector KB Load]
    PARSE -->|"ask:"| KB_ASK[Vector KB Query]
    PARSE -->|"critic:"| CRITIC[Critic Agent]
    PARSE -->|"quant:"| QUANTIFIER[Quantifier Agent]
    PARSE -->|"som:"| SOCIETY[Society of Mind]
    PARSE -->|"cheat:"| CHEAT[Cheat Commands]
    PARSE -->|default| GAME_ACTION
    
    GAME_ACTION --> GAME_STATE[GameState.apply_action()]
    RAG_QUERY --> RAG_HELPER[RagTerroristHelper.answer()]
    AG2_QUERY --> AG2_BOT[Terrorist Bot Agent]
    SMART_QUERY --> COMBINED[AG2 + Vector KB]
    KB_ADD --> CHROMA[ChromaDB]
    KB_LOAD --> CHROMA
    KB_ASK --> CHROMA
    CRITIC --> CONTRIB_CRITIC[CriticAgent]
    QUANTIFIER --> CONTRIB_QUANT[QuantifierAgent]
    SOCIETY --> CONTRIB_SOM[SocietyOfMindAgent]
    CHEAT --> DIRECT_STATE[Direct State Access]
```

## Key Components Breakdown

### 1. **Web UI Service** (services/web_ui.py) - Frontend Orchestrator
- Serves modern web interface on port 8082
- Handles WebSocket connections for real-time updates
- Routes user commands to appropriate backend services
- Manages multi-panel display state (3 Terrorist + 1 CT)
- Broadcasts game state changes to all connected clients

### 2. **API Service** (services/api_server.py) - Core Game Backend
- FastAPI REST server on port 8080
- Manages game sessions and persistent state
- Validates and applies game actions
- Maintains round/score state in PostgreSQL
- Provides health checks and monitoring endpoints

### 3. **Agent Service** (services/agent_service.py) - AI Processing Hub
- FastAPI service on port 8081 dedicated to AI operations
- **AG2 Multi-Agent System**: Creates and manages terrorist/CT agents
- **RAG Helper**: Fast offline heuristic responses using game facts
- **Contrib Integration**: Specialized agents (Critic, Quantifier, SoM)
- **Vector RAG Client**: Interfaces with ChromaDB for semantic search

### 4. **PostgreSQL Database** - Persistent Game Storage
- Stores game sessions, player actions, and state history
- Provides ACID transactions for game state consistency
- Connection pooling for efficient multi-service access
- Health checks and backup capabilities

### 5. **ChromaDB** - Vector Knowledge Base
- Semantic search over Counter-Strike tactical knowledge
- Persistent vector storage with similarity search
- Supports knowledge base expansion via kb:add commands
- Integration with sentence-transformers for offline embeddings

### 6. **Docker Network** - Service Communication
- Internal cs_network for secure service-to-service communication
- Environment variable configuration for service discovery
- Health check dependencies and startup ordering
- Volume persistence for data across container restarts

## Agent Usage Patterns

### Current Agent Calls:
1. **ag2:** - Direct call to AG2 multi-agent system with game context
2. **smart:** - Combined AG2 agent + ChromaDB vector search
3. **rag:** - Fast RAG helper with keyword matching (~50ms)
4. **critic:** - CriticAgent for strategy plan evaluation
5. **quant:** - QuantifierAgent for option ranking and selection
6. **som:** - SocietyOfMindAgent for multi-expert reasoning
7. **kb:add/ask:** - Direct ChromaDB vector operations

### Microservices Response Flow:
1. User command received via WebSocket in Web UI Service
2. Web UI Service routes to appropriate backend service (API or Agent)
3. Agent Service retrieves game context from API Service
4. Agent Service processes request (RAG/AG2/Contrib/Vector)
5. Response formatted and returned to Web UI Service
6. Web UI Service broadcasts response via WebSocket to all connected clients
7. Real-time UI updates across all panels

This microservices architecture provides excellent separation of concerns with dedicated services for UI, game logic, AI processing, and data storage. The WebSocket-based real-time updates ensure all players see changes instantly, while the containerized approach enables easy scaling and deployment.