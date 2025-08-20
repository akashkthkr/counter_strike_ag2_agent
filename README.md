# Counter-Strike AI Teammates - Play with Smart Bots!

Ever wanted to play Counter-Strike with AI teammates that actually understand tactics? This project lets you do exactly that! It's a modern web-based Counter-Strike simulator where you can chat with AI agents that give you real tactical advice.

## What makes this cool?

- **Smart AI teammates** that actually know Counter-Strike strategy (no more "rush B" spam!)
- **Modern web interface** - sleek browser-based UI with real-time updates
- **Microservices architecture** - scalable Docker containers for each component
- **Real-time WebSocket updates** - see what your teammates are doing instantly
- **Dynamic sound effects** - hear gunshots, bomb plants, and more
- **Multiple AI personalities** - get advice from different types of agents
- **Persistent game sessions** - PostgreSQL database stores all your matches
- **Vector knowledge base** - ChromaDB powers semantic search over tactical knowledge

## Quick Start (5 minutes to get playing!)

### The Easy Way (Docker)
1. **Download the project**
   ```bash
   git clone <your-repo-url>
   cd counter_strike_ag2_agent
   ```

2. **Add your AI API key**
   ```bash
   cp env.example .env
   # Edit .env and add your Anthropic or OpenAI API key
   ```

3. **Start everything**
   ```bash
   ./run_docker.sh
   ```

4. **Open your browser**
   Go to: http://localhost:8082

That's it! You're ready to play.

### The Developer Way (if you want to tinker)
```bash
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
python multi_main.py
```

## Getting AI API Keys (you need this!)

You'll need an API key from one of these:

**Option 1: Anthropic Claude (recommended)**
- Go to https://console.anthropic.com
- Create account, get API key
- Add to .env: `ANTHROPIC_API_KEY=your-key-here`

**Option 2: OpenAI**
- Go to https://platform.openai.com
- Create account, get API key  
- Add to .env: `OPENAI_API_KEY=your-key-here`

## How to Play

The web interface has 4 panels - 3 for terrorists and 1 for counter-terrorists. Just type commands in any panel and press Enter! Updates appear instantly across all panels thanks to WebSocket magic.

### Basic Game Actions
- `move to A-site` - Go to A bombsite
- `shoot player` - Attack an enemy
- `plant bomb` - Plant the bomb (terrorists only)
- `defuse bomb` - Defuse the bomb (CTs only)

### Ask Your AI Teammates
- `ag2: what should we do?` - Get tactical advice from your AI teammate
- `critic: rush B with no utility` - Get your plan critiqued by the critic agent
- `som: should we save or force buy?` - Ask multiple AI experts for consensus
- `rag: where are the enemies?` - Quick tactical lookup from knowledge base
- `smart: best strategy for eco round?` - Combined AI + knowledge base response

### Advanced AI Commands
- `quant: rush A | smoke execute | save` - Rank multiple options by effectiveness
- `kb:add <text>` - Add tactical knowledge to the vector database
- `ask: <question>` - Semantic search through the knowledge base

### Fun Pirate Commands (because why not?)
- `fire the cannons` = shoot
- `bury the chest` = plant bomb
- `cut the fuse` = defuse bomb

## What Each AI Does

**AG2 Agent** - Your main tactical advisor. Knows Counter-Strike strategy and gives solid advice.

**Critic Agent** - Analyzes your plans and tells you what could go wrong. Sometimes harsh but usually right.

**Society of Mind (SoM)** - Multiple AI personalities discuss your question and give you different perspectives.

**Quantifier Agent** - Give it options like "rush A | smoke execute | save" and it'll rank them.

**RAG System** - Quick tactical database. Answers fast without using API calls.

## Troubleshooting

**Web page won't load?**
- Make sure you're going to http://localhost:8082
- Check that Docker is running: `docker ps`

**AI not responding?**
- Check your API key in the .env file
- Make sure you have internet connection
- Try refreshing the browser page

**Sound not working?**
- Click the sound button in the top right
- Make sure your browser allows audio

**Docker acting weird?**
```bash
docker compose down
docker compose up -d
```

## Architecture (for the curious)

The system runs 5 Docker containers in a microservices architecture:
- **Web UI Service** (Port 8082) - Modern FastAPI web server with WebSocket support
- **API Service** (Port 8080) - REST API for game state management and session handling
- **Agent Service** (Port 8081) - AG2 multi-agent system and AI processing
- **PostgreSQL** (Port 5432) - Persistent database for game sessions and state
- **ChromaDB** (Port 8000) - Vector database for semantic knowledge search

Services communicate via HTTP REST APIs within a Docker network, while the web interface provides real-time updates through WebSocket connections. The architecture is designed for scalability and fault tolerance.

## Performance Tips

- `rag:` commands are fastest (~50ms - ChromaDB vector search)
- `ag2:` and other AI commands take 1-5 seconds (LLM API calls)
- `smart:` commands combine both for enhanced responses
- Real-time updates via WebSocket are instant (<50ms)
- Multiple users can play simultaneously without performance impact
- If AI responses are slow, try using Anthropic instead of OpenAI

## Contributing

Found a bug? Want to add features? 

1. Make sure tests pass: `pytest`
2. Test with Docker: `./run_docker.sh`
3. Submit a pull request

The codebase is pretty clean and well-documented. Most of the AI logic is in `counter_strike_ag2_agent/` and the web interface is in `services/web_ui.py`.

## What's Under the Hood

This project uses some pretty cool tech:
- **AG2 (AutoGen)** for multi-agent AI conversations and orchestration
- **FastAPI** for high-performance async web services
- **ChromaDB** for vector-based semantic search over tactical knowledge
- **PostgreSQL** for reliable persistent game state storage
- **WebSocket** for real-time bidirectional communication
- **Docker Compose** for microservices orchestration
- **Jinja2** for dynamic HTML templating
- **Web Audio API** for immersive sound effects

### AG2 Agent Integration

The project leverages several key AG2 agents to create a rich, interactive experience:

- **`AssistantAgent`**: Powers the core tactical AI, providing strategic advice based on game state.
- **`UserProxyAgent`**: Manages human-in-the-loop interactions, seamlessly integrating player commands with the AI system.
- **`GroupChatManager`**: Orchestrates conversations between multiple agents, enabling collaborative problem-solving for complex scenarios.
- **`CriticAgent` (contrib)**: Evaluates player-proposed strategies, offering critical feedback to improve tactical decisions.
- **`QuantifierAgent` (contrib)**: Ranks multiple tactical options, helping players choose the most effective course of action.
- **`SocietyOfMindAgent` (contrib)**: Simulates a team of experts debating a problem, providing diverse perspectives on challenging situations.

The AI agents actually understand Counter-Strike tactics because they're trained on strategy guides and have specialized prompts. They're not just generic chatbots - they know the difference between an eco round and a force buy! The vector knowledge base allows for semantic search, so you can ask "What should I do in a 2v4 clutch?" and get relevant tactical advice.

## License

MIT License - use it however you want!

## Credits

Built with love for the Counter-Strike community. Special thanks to the AG2/AutoGen team for making multi-agent AI accessible.

---

**TL;DR**: It's Counter-Strike with smart AI teammates. Run `./run_docker.sh`, open http://localhost:8082, and start playing!

## Running Tests

If you want to make sure everything works:
```bash
pytest
```

