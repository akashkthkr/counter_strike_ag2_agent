import os
import json
import uuid
from typing import Dict, List, Optional
from datetime import datetime

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import asyncpg

from .database import db_manager

from counter_strike_ag2_agent.game_state import GameState
from counter_strike_ag2_agent.config import TEAMS


class GameAction(BaseModel):
    session_id: str
    team: str
    player: str
    action: str





class GameSessionCreate(BaseModel):
    session_name: str
    max_rounds: int = 3


class GameSessionResponse(BaseModel):
    id: str
    session_name: str
    max_rounds: int
    current_round: int
    is_active: bool
    created_at: datetime


app = FastAPI(title="Counter-Strike AG2 API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# WebSocket connection manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def send_personal_message(self, message: str, websocket: WebSocket):
        await websocket.send_text(message)

    async def broadcast(self, message: str):
        for connection in self.active_connections:
            try:
                await connection.send_text(message)
            except:
                pass


manager = ConnectionManager()

# In-memory game states cache (in production, use Redis)
game_states_cache: Dict[str, GameState] = {}


async def get_db_connection():
    async with db_manager.get_connection() as conn:
        yield conn


@app.on_event("startup")
async def startup_event():
    await db_manager.initialize()


@app.on_event("shutdown")
async def shutdown_event():
    await db_manager.close()


@app.get("/health")
async def health_check():
    return {"status": "healthy", "timestamp": datetime.utcnow()}


@app.post("/sessions", response_model=GameSessionResponse)
async def create_session(session_data: GameSessionCreate, conn: asyncpg.Connection = Depends(get_db_connection)):
    session_id = str(uuid.uuid4())
    
    await conn.execute(
        """
        INSERT INTO game_sessions (id, session_name, max_rounds)
        VALUES ($1, $2, $3)
        """,
        session_id, session_data.session_name, session_data.max_rounds
    )
    
    # Initialize game state
    game_state = GameState()
    game_state.max_rounds = session_data.max_rounds
    game_states_cache[session_id] = game_state
    
    # Save initial game state
    await save_game_state(conn, session_id, game_state)
    
    session = await conn.fetchrow(
        "SELECT * FROM game_sessions WHERE id = $1", session_id
    )
    
    return GameSessionResponse(
        id=str(session['id']),
        session_name=session['session_name'],
        max_rounds=session['max_rounds'],
        current_round=session['current_round'],
        is_active=session['is_active'],
        created_at=session['created_at']
    )


@app.get("/sessions", response_model=List[GameSessionResponse])
async def list_sessions(conn: asyncpg.Connection = Depends(get_db_connection)):
    sessions = await conn.fetch(
        "SELECT * FROM game_sessions WHERE is_active = TRUE ORDER BY created_at DESC"
    )
    
    return [
        GameSessionResponse(
            id=str(session['id']),
            session_name=session['session_name'],
            max_rounds=session['max_rounds'],
            current_round=session['current_round'],
            is_active=session['is_active'],
            created_at=session['created_at']
        )
        for session in sessions
    ]


@app.get("/sessions/{session_id}/state")
async def get_game_state(session_id: str, conn: asyncpg.Connection = Depends(get_db_connection)):
    if session_id not in game_states_cache:
        # Load from database
        state_data = await conn.fetchrow(
            """
            SELECT state_data FROM game_states 
            WHERE session_id = $1 
            ORDER BY round_number DESC, created_at DESC 
            LIMIT 1
            """,
            session_id
        )
        
        if not state_data:
            raise HTTPException(status_code=404, detail="Game session not found")
        
        # Reconstruct GameState from stored data
        game_state = GameState()
        # This would need proper deserialization logic
        game_states_cache[session_id] = game_state
    
    game_state = game_states_cache[session_id]
    
    return {
        "session_id": session_id,
        "round": game_state.round,
        "max_rounds": game_state.max_rounds,
        "player_health": game_state.player_health,
        "bomb_planted": game_state.bomb_planted,
        "bomb_site": game_state.bomb_site,
        "winner": game_state.winner,
        "phase": game_state.phase,
        "round_scores": game_state.round_scores,
        "current_positions": game_state.current_positions,
        "game_status": game_state.get_game_status(),
        "is_round_over": game_state.is_round_over(),
        "is_game_over": game_state.is_game_over()
    }


@app.post("/sessions/{session_id}/actions")
async def apply_action(
    session_id: str, 
    action_data: GameAction, 
    conn: asyncpg.Connection = Depends(get_db_connection)
):
    if session_id not in game_states_cache:
        raise HTTPException(status_code=404, detail="Game session not found")
    
    game_state = game_states_cache[session_id]
    
    # Apply action
    result = game_state.apply_action(action_data.team, action_data.player, action_data.action)
    
    # Log action to database
    await conn.execute(
        """
        INSERT INTO game_actions (session_id, round_number, team, player_name, action, result)
        VALUES ($1, $2, $3, $4, $5, $6)
        """,
        session_id, game_state.round, action_data.team, action_data.player, action_data.action, result
    )
    
    # Save updated game state
    await save_game_state(conn, session_id, game_state)
    
    # Broadcast to WebSocket clients
    await manager.broadcast(json.dumps({
        "type": "action_result",
        "session_id": session_id,
        "team": action_data.team,
        "player": action_data.player,
        "action": action_data.action,
        "result": result,
        "game_state": {
            "round": game_state.round,
            "player_health": game_state.player_health,
            "bomb_planted": game_state.bomb_planted,
            "winner": game_state.winner,
            "is_round_over": game_state.is_round_over(),
            "is_game_over": game_state.is_game_over()
        }
    }))
    
    return {
        "result": result,
        "game_state": await get_game_state(session_id, conn)
    }





@app.websocket("/ws/{session_id}")
async def websocket_endpoint(websocket: WebSocket, session_id: str):
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            # Handle incoming WebSocket messages
            message = json.loads(data)
            
            if message.get("type") == "ping":
                await websocket.send_text(json.dumps({"type": "pong"}))
            elif message.get("type") == "subscribe":
                # Client subscribes to session updates
                await websocket.send_text(json.dumps({
                    "type": "subscribed",
                    "session_id": session_id
                }))
                
    except WebSocketDisconnect:
        manager.disconnect(websocket)


async def save_game_state(conn: asyncpg.Connection, session_id: str, game_state: GameState):
    state_data = {
        "round": game_state.round,
        "max_rounds": game_state.max_rounds,
        "player_health": game_state.player_health,
        "bomb_planted": game_state.bomb_planted,
        "bomb_site": game_state.bomb_site,
        "winner": game_state.winner,
        "phase": game_state.phase,
        "round_scores": game_state.round_scores,
        "round_time": game_state.round_time,
        "bomb_timer": game_state.bomb_timer,
        "current_positions": game_state.current_positions,
        "last_action_results": game_state.last_action_results
    }
    
    await conn.execute(
        """
        INSERT INTO game_states (session_id, round_number, phase, bomb_planted, bomb_site, winner, state_data)
        VALUES ($1, $2, $3, $4, $5, $6, $7)
        """,
        session_id,
        game_state.round,
        game_state.phase,
        game_state.bomb_planted,
        game_state.bomb_site,
        game_state.winner,
        json.dumps(state_data)
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)
