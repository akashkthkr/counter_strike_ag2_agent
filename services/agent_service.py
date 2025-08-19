import os
import json
from typing import Dict, Any, Optional
from datetime import datetime

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import uvicorn

from counter_strike_ag2_agent.agents import create_terrorists_group, create_team
from counter_strike_ag2_agent.contrib_integration import run_critic, run_quantifier, run_som
from counter_strike_ag2_agent.rag import RagTerroristHelper
from counter_strike_ag2_agent.rag_vector import ChromaRAG
from counter_strike_ag2_agent.game_state import GameState


class AgentRequest(BaseModel):
    agent_type: str  # 'ag2', 'rag', 'smart', 'critic', 'quantifier', 'som'
    query: str
    context: Optional[Dict[str, Any]] = None


class AgentResponse(BaseModel):
    success: bool
    response: Optional[str] = None
    error: Optional[str] = None
    agent_type: str
    processing_time_ms: int


class KBAddRequest(BaseModel):
    text: str


class KBLoadRequest(BaseModel):
    file_path: str


class KBAskRequest(BaseModel):
    query: str


class KBResponse(BaseModel):
    success: bool
    count: Optional[int] = None
    answer: Optional[str] = None
    error: Optional[str] = None


app = FastAPI(title="Counter-Strike AG2 Agent Service", version="1.0.0")

# Initialize agents on startup
agents_cache = {}
kb = ChromaRAG()


@app.on_event("startup")
async def startup_event():
    try:
        # Initialize terrorist group
        manager, agents = create_terrorists_group(num_players=3)
        agents_cache["terrorists"] = {"manager": manager, "agents": agents}
        
        # Initialize counter-terrorist group
        ct_manager = create_team("Counter-Terrorists", is_terrorists=False)
        agents_cache["counter_terrorists"] = {"manager": ct_manager}
        
        print("Agent service initialized successfully")
    except Exception as e:
        print(f"Failed to initialize agents: {e}")


@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow(),
        "agents_loaded": len(agents_cache)
    }


@app.post("/process", response_model=AgentResponse)
async def process_agent_request(request: AgentRequest):
    start_time = datetime.utcnow()
    
    try:
        if request.agent_type == "ag2":
            response = await process_ag2_query(request.query, request.context or {})
        elif request.agent_type == "rag":
            response = await process_rag_query(request.query, request.context or {})
        elif request.agent_type == "smart":
            response = await process_smart_query(request.query, request.context or {})
        elif request.agent_type == "critic":
            response = await process_critic_query(request.query, request.context or {})
        elif request.agent_type == "quantifier":
            response = await process_quantifier_query(request.query, request.context or {})
        elif request.agent_type == "som":
            response = await process_som_query(request.query, request.context or {})
        else:
            raise HTTPException(status_code=400, detail=f"Unknown agent type: {request.agent_type}")
        
        processing_time = int((datetime.utcnow() - start_time).total_seconds() * 1000)
        
        return AgentResponse(
            success=True,
            response=response,
            agent_type=request.agent_type,
            processing_time_ms=processing_time
        )
        
    except Exception as e:
        processing_time = int((datetime.utcnow() - start_time).total_seconds() * 1000)
        
        return AgentResponse(
            success=False,
            error=str(e),
            agent_type=request.agent_type,
            processing_time_ms=processing_time
        )


async def process_ag2_query(query: str, context: Dict[str, Any]) -> str:
    if "terrorists" not in agents_cache:
        raise Exception("Terrorist agents not initialized")
    
    manager = agents_cache["terrorists"]["manager"]
    
    # Get comprehensive game context
    game_status = context.get("game_status", "")
    game_state = reconstruct_game_state(context)
    game_facts = RagTerroristHelper.build_facts(game_state)
    
    full_context = f"Game Status: {game_status}\nDetailed Context: {' '.join(game_facts)}\n\nQuestion: {query}\n\nGive a SHORT tactical response (1-2 sentences max)."
    
    # Create a message for the bot
    user_message = {"content": full_context, "role": "user"}
    
    # Send to AG2 agent (terrorist bot)
    bot_agent = None
    for agent in manager.groupchat.agents:
        if hasattr(agent, 'system_message') and 'bot' in agent.name.lower():
            bot_agent = agent
            break
    
    if not bot_agent:
        raise Exception("Could not find bot agent in group chat")
    
    agent_response = bot_agent.generate_reply(
        messages=[user_message],
        sender=None
    )
    
    # Clean up the response formatting
    if agent_response:
        if isinstance(agent_response, dict) and 'content' in agent_response:
            response_text = agent_response['content']
        else:
            response_text = str(agent_response)
        
        # Clean up excessive newlines and whitespace
        response_text = response_text.replace('\\n\\n', ' ').replace('\\n', ' ')
        response_text = ' '.join(response_text.split())  # Remove extra whitespace
        
        # Limit length to keep it readable
        if len(response_text) > 200:
            response_text = response_text[:197] + "..."
    else:
        response_text = "No response from agent"
    
    return response_text


async def process_rag_query(query: str, context: Dict[str, Any]) -> str:
    game_state = reconstruct_game_state(context)
    answer = RagTerroristHelper.answer(query, game_state)
    return answer


async def process_smart_query(query: str, context: Dict[str, Any]) -> str:
    if "terrorists" not in agents_cache:
        raise Exception("Terrorist agents not initialized")
    
    manager = agents_cache["terrorists"]["manager"]
    game_state = reconstruct_game_state(context)
    
    # Get comprehensive game context and knowledge base info
    game_status = context.get("game_status", "")
    game_facts = RagTerroristHelper.build_facts(game_state)
    kb_info = kb.ask(query) or "No relevant knowledge found"
    
    full_context = f"""Game Status: {game_status}
Detailed Context: {' '.join(game_facts)}
Knowledge Base: {kb_info}
Question: {query}

Give SHORT tactical advice (1-2 sentences max) based on the current game state and available knowledge."""
    
    # Create a message for the bot
    user_message = {"content": full_context, "role": "user"}
    
    # Send to AG2 agent (terrorist bot)
    bot_agent = None
    for agent in manager.groupchat.agents:
        if hasattr(agent, 'system_message') and 'bot' in agent.name.lower():
            bot_agent = agent
            break
    
    if not bot_agent:
        raise Exception("Could not find bot agent in group chat")
    
    agent_response = bot_agent.generate_reply(
        messages=[user_message],
        sender=None
    )
    
    # Clean up the response formatting
    if agent_response:
        if isinstance(agent_response, dict) and 'content' in agent_response:
            response_text = agent_response['content']
        else:
            response_text = str(agent_response)
        
        # Clean up excessive newlines and whitespace
        response_text = response_text.replace('\\n\\n', ' ').replace('\\n', ' ')
        response_text = ' '.join(response_text.split())  # Remove extra whitespace
        
        # Limit length to keep it readable
        if len(response_text) > 200:
            response_text = response_text[:197] + "..."
    else:
        response_text = "No response from agent"
    
    return response_text


async def process_critic_query(query: str, context: Dict[str, Any]) -> str:
    game_state = reconstruct_game_state(context)
    return run_critic(query, game_state)


async def process_quantifier_query(query: str, context: Dict[str, Any]) -> str:
    game_state = reconstruct_game_state(context)
    options = [o.strip() for o in query.split("|") if o.strip()]
    return run_quantifier(options, game_state)


async def process_som_query(query: str, context: Dict[str, Any]) -> str:
    game_state = reconstruct_game_state(context)
    return run_som(query, game_state)


def reconstruct_game_state(context: Dict[str, Any]) -> GameState:
    game_state = GameState()
    game_state.round = context.get("round", 1)
    game_state.player_health = context.get("player_health", {
        team: {"player": 100, "bot": 100} for team in ["Terrorists", "Counter-Terrorists"]
    })
    game_state.bomb_planted = context.get("bomb_planted", False)
    game_state.bomb_site = context.get("bomb_site")
    game_state.winner = context.get("winner")
    game_state.phase = context.get("phase", "chat")
    game_state.round_scores = context.get("round_scores", {"Terrorists": 0, "Counter-Terrorists": 0})
    game_state.current_positions = context.get("current_positions", {
        team: {"player": "spawn", "bot": "spawn"} for team in ["Terrorists", "Counter-Terrorists"]
    })
    return game_state


@app.get("/agents/status")
async def get_agents_status():
    return {
        "agents_loaded": list(agents_cache.keys()),
        "kb_status": "initialized" if kb else "not_initialized"
    }


@app.post("/kb/add", response_model=KBResponse)
async def add_to_kb(request: KBAddRequest):
    try:
        count = kb.add_texts([request.text])
        return KBResponse(success=True, count=count)
    except Exception as e:
        return KBResponse(success=False, error=str(e))


@app.post("/kb/load", response_model=KBResponse)
async def load_file_to_kb(request: KBLoadRequest):
    try:
        kb.clear()  # Clear then load to ensure reload reflects updates
        count = kb.add_file(request.file_path)
        return KBResponse(success=True, count=count)
    except Exception as e:
        return KBResponse(success=False, error=str(e))


@app.post("/kb/clear", response_model=KBResponse)
async def clear_kb():
    try:
        kb.clear()
        return KBResponse(success=True, count=0)
    except Exception as e:
        return KBResponse(success=False, error=str(e))


@app.post("/kb/ask", response_model=KBResponse)
async def ask_kb(request: KBAskRequest):
    try:
        answer = kb.ask(request.query)
        return KBResponse(success=True, answer=answer or "no match")
    except Exception as e:
        return KBResponse(success=False, error=str(e))


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8081)
