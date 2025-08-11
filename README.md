## Counter‑Strike AG2 Multi‑Agent — Usability Guide

Turn‑based, multi‑panel Counter‑Strike simulator with AG2 group‑chat orchestration and an optional vector knowledge base. Use `rag:` for the offline game‑state helper and `ag2:` for LLM answers.

### What you get
- Multi‑panel UI so multiple Terrorist players can act in parallel and see each other’s updates
- AG2 bot teammate that answers questions and gives tactics
- Minimal finite‑state game logic: move, shoot, plant, defuse
- Optional vector KB via ChromaDB for map/tactics knowledge

## 1) Setup
- Python 3.10+ recommended
- macOS/Linux/Windows supported (Pygame windowed UI)

```bash
cd counter_strike_ag2_agent
python -m venv .venv-cs
source .venv-cs/bin/activate  # Windows: .venv-cs\\Scripts\\activate
pip install -r requirements.txt
```

Notes
- If the bundled AG2 wheel is missing 
- First run of ChromaDB will create a `.chroma` directory for persistence.

## 2) Configure the LLM (AG2/Autogen)
The AG2 agent uses a config list. You can provide it either as a JSON string or a path to a JSON file using `OAI_CONFIG_LIST`.

Examples
```bash
# JSON string
export OAI_CONFIG_LIST='[{"model":"gpt-5","api_type":"responses","api_key":"$OPENAI_API_KEY"}]'

# Path to JSON file (see format below)
export OAI_CONFIG_LIST=/absolute/path/to/oai_config_list.json

# Fallbacks if OAI_CONFIG_LIST is not set
export OPENAI_API_KEY=...     # uses model gpt-5 by default
# or
export ANTHROPIC_API_KEY=...  # uses claude‑3.5‑sonnet
```

oai_config_list.json format
```json
[
  { "model": "gpt-5", "api_type": "responses", "api_key": "YOUR_OPENAI_KEY" }
]
```

Security
- Do not commit real API keys. Prefer environment variables or a local, ignored JSON file.

## 3) Run the game

Single‑panel (quick demo)
```bash
python main.py
```

Multi‑panel (recommended)
```bash
python multi_main.py
```
Defaults: 3 Terrorist panels and 1 Counter‑Terrorist panel. To change panel count or hide CT, import and call directly:
```bash
python - <<'PY'
from multi_main import run_multi
run_multi(num_instances=4, show_ct=False)
PY
```

UI basics
- Click a panel’s input box to focus it
- Type a command and press Enter
- Each Terrorist panel shares the same round and state; teammate actions are broadcast to all T panels
- Copy/paste is supported in the input box (Cmd/Ctrl+C/V/X). Long chat lines wrap automatically.

## 4) How to play — Commands

- Actions
  - move: `move to A-site`, `move to Mid`, `move to B-site`
  - shoot: `shoot player`, `shoot bot` (70% hit chance; 30 dmg)
  - plant: `plant bomb` (T only; site inferred if not specified)
  - defuse: `defuse bomb` (CT only; 80% success)

- Pirate aliases (fun equivalents)
  - shoot → `fire the cannons`, `open fire`
  - plant → `bury the chest`, `drop the keg`
  - defuse → `encounter`, `cut the fuse`

- Heuristic RAG (offline, game‑state aware; 5 uses per T panel)
  - `rag: where is the bomb site?`
  - `rag: any ct near?`
  - `rag: what should we do now?`

- AG2 Agent (LLM teammate)
  - `ag2: best plan to hit A?`
  - Returns bot advice using LLM based on summarized game facts

- Smart (AG2 + vector KB)
  - `smart: how should we retake B?`
  - Combines current game facts plus the top KB hit as context for AG2

- Vector KB (ChromaDB)
  - `kb:add <text>` — add a snippet
  - `kb:load <path-to-text>` — load and chunk a local text file
  - `ask: <question>` — query the KB directly (top‑1 chunk shown)

- Cheat utilities (read‑only + a round‑skip)
  - `cheat: status` | `cheat: site` | `cheat: ct` | `cheat: hp`
  - `cheat: next` — vote to skip to next round (majority of T panels triggers a reset)

Rules and outcomes
- Movement updates your position tag (A‑site/B‑site/Mid/spawn)
- Shooting targets an explicitly named enemy if present; otherwise a random alive target
- Plant chooses the site mentioned or a random site if omitted
- Defuse ends the round with CT win on success
- The UI logs recent actions and status; rounds advance via win/lose or by vote skip

Limits
- Each T panel starts with 5 uses shared between `rag:`, `ag2:` and `smart:` commands. Uses are not replenished mid‑session.

## 5) Troubleshooting
- Window doesn’t appear: ensure you are on a local machine with a display; Pygame needs a windowing environment
- No AG2 responses: verify `OAI_CONFIG_LIST` or `OPENAI_API_KEY`/`ANTHROPIC_API_KEY` is set
- ChromaDB errors: delete `.chroma/` to reset local persistence if needed
- Keyboard input not sent: click inside the panel’s input box; press Enter

## 6) Tests

### Layout
- All tests live under `tests/`.
- Shared fixtures/utilities go in `tests/conftest.py`.

### Quick start (pytest)
```bash
pip install pytest pytest-cov
pytest -q
```

### Useful commands
- Run a single file:
  ```bash
  pytest tests/test_rag.py -q
  ```
- Run a single test:
  ```bash
  pytest tests/test_rag.py::TestRagTerroristHelper::test_build_facts_initial_state -q
  ```
- Stop on first failure / increase verbosity:
  ```bash
  pytest -x -vv
  ```
- Select by keyword:
  ```bash
  pytest -k "rag and not integration"
  ```

### Coverage
```bash
pytest --cov=counter_strike_ag2_agent --cov-report=term-missing --cov-report=xml
```

### CI/JUnit XML
Generate a JUnit XML for CI systems:
```bash
pytest --junitxml=test-output.xml
```

### Fixtures and temp resources
- Use built-in fixtures like `tmp_path`/`monkeypatch` for isolation.
- Vector KB tests already isolate state by using temporary directories.
- If you see HuggingFace tokenizers fork warnings, you can silence them with:
  ```bash
  export TOKENIZERS_PARALLELISM=false
  ```

### Unittest fallback
You can still run via the stdlib test runner if preferred:
```bash
python -m unittest -v
```

## 7) Project structure
- `counter_strike_ag2_agent/game_state.py` — core FSM and actions
- `counter_strike_ag2_agent/agents.py` — AG2/autogen agents and group chat
- `counter_strike_ag2_agent/ui.py` — Pygame input and rendering
- `counter_strike_ag2_agent/rag.py` — lightweight, dependency‑free RAG helper
- `counter_strike_ag2_agent/rag_vector.py` — ChromaDB wrapper for vector KB
- `main.py` — single‑panel demo
- `multi_main.py` — multi‑panel orchestrator

## 8) Tips and ideas
- Seed the KB with callouts, executes, timings, and roles to improve `smart:` answers
- Try pirate aliases for fun variation
- Expand commands (movement granularity, utility) or display bot suggestions inline

License: MIT (see `LICENSE`).
