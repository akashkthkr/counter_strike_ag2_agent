## Counter-Strike AG2 Multi‑Agent (with Lightweight RAG)

Small, turn‑based, multi‑agent Counter‑Strike simulator:
- Multi‑panel UI (T1, T2, T3, …) so teammates act and see each other’s updates
- AG2 group chat orchestration
- Minimal FSM game logic
- Lightweight, dependency‑free RAG helper

### Quickstart
```bash
cd counter_strike_ag2_agent
source .venv-cs/bin/activate  # or create your own venv
python multi_main.py
```

### Configure LLM (GPT‑5)
Prefer `OAI_CONFIG_LIST`; fallback `OPENAI_API_KEY` works. To target GPT‑5:
```bash
export OAI_CONFIG_LIST='[{"model":"gpt-5","api_key":"YOUR_OPENAI_KEY"}]'
# or
export OPENAI_API_KEY=YOUR_OPENAI_KEY
```

### Commands
- Actions: `shoot`, `plant bomb`, `defuse bomb` (CT only). Unknown → `Invalid action.`
- Pirate aliases: `fire the cannons` (shoot), `bury the chest` (plant), `encounter` (defuse)
- RAG (3 tries per T panel): prefix with `rag:`
  - `rag: where is the bomb site?`
  - `rag: any ct near?`
  - `rag: what should we do now?`
- Cheat (read‑only): prefix with `cheat:`
  - `cheat: status` | `cheat: site` | `cheat: ct` | `cheat: hp`
  - `cheat: next` → vote to skip to next round (majority of T panels triggers a reset)
  
### Vector KB (ChromaDB)
- `kb:add <text>`
- `kb:load <path-to-text>`
- `ask: <question>`

### RAG training ideas
- Map semantics (A/B/Mid), rotations, timings
- Executes (smokes, flashes), post‑plant setups, crossfires
- Threat modeling: CT rotations, eco/buy, man‑advantage play
- Micro: clear corners, bait‑and‑trade, deny retake

### Structure
- `game_state.py`: FSM logic
- `agents.py`: agent setup
- `ui.py`: panel input/render
- `rag.py`: heuristic RAG
- `main.py`: single‑panel
- `multi_main.py`: multi‑panel

### Upgrades
- Replace heuristic RAG with vector DB
- Show bot suggestions in panels
- Add timers/scoreboard; expand actions (move, utility)
  
### Testing tips
- Invalid action: type `dance` → UI should show `Invalid action.`
- Pirate aliases: try `fire the cannons` (shoot) or `bury the chest` (plant).
- Round reset: use `cheat: next` in 2 of 3 panels → round resets and a pirate hint appears.
