import os
import json
import asyncio
from typing import List, Dict, Any, Optional
from datetime import datetime

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import httpx


class WebUIService:
    def __init__(self):
        self.api_url = os.getenv("API_URL", "http://api:8080")
        self.agent_url = os.getenv("AGENT_URL", "http://agent_service:8081")
        self.session_id: Optional[str] = None
        self.game_state: Dict[str, Any] = {}
        
        # UI state for multiple panels
        self.num_panels = 3
        self.chat_logs: List[List[str]] = [[] for _ in range(self.num_panels)]
        self.rag_tries: List[int] = [5 for _ in range(self.num_panels)]
        self.ct_chat: List[str] = []
        
        # WebSocket connections
        self.connections: List[WebSocket] = []

    async def broadcast_update(self):
        """Immediately broadcast state update to all connected clients"""
        if not self.connections:
            return
        
        state = await self.get_ui_state()
        message = json.dumps(state)
        
        # Send to all connected clients
        disconnected = []
        for connection in self.connections:
            try:
                await connection.send_text(message)
            except:
                disconnected.append(connection)
        
        # Remove disconnected clients
        for conn in disconnected:
            if conn in self.connections:
                self.connections.remove(conn)

    async def initialize_session(self):
        """Create a new game session"""
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    f"{self.api_url}/sessions",
                    json={
                        "session_name": f"Web Session {datetime.now().strftime('%H:%M:%S')}",
                        "max_rounds": 3
                    }
                )
                if response.status_code == 200:
                    session_data = response.json()
                    self.session_id = session_data["id"]
                    
                    # Get initial game state
                    state_response = await client.get(f"{self.api_url}/sessions/{self.session_id}/state")
                    if state_response.status_code == 200:
                        self.game_state = state_response.json()
                    
                    # Initialize chat logs
                    for i in range(self.num_panels):
                        self.chat_logs[i] = [
                            f"T{i+1}: Ready! Session",
                            "Commands: 'shoot player/bot', 'plant bomb', 'move to A-site', 'defuse bomb'",
                            "AI Help: 'rag:', 'ag2:', 'smart:', 'critic:', 'quant:', 'som:', 'kb:add', 'kb:load <file>', 'kb:clear', 'ask:'"
                        ]
                    
                    self.ct_chat = [
                        f"CT: Ready! Session",
                        "Commands: 'shoot player/bot', 'defuse bomb', 'move to A-site/B-site'",
                        "Objective: Prevent bomb plant or defuse if planted!"
                    ]
                    
                    return True
            except Exception as e:
                print(f"Failed to initialize session: {e}")
                # Create a fallback session ID
                import uuid
                self.session_id = str(uuid.uuid4())
                for i in range(self.num_panels):
                    self.chat_logs[i] = [
                        f"T{i+1}: Demo Mode - Backend services starting...",
                        "Commands: 'shoot player/bot', 'plant bomb', 'move to A-site'",
                        "AI Help: 'rag:', 'ag2:', 'smart:', 'critic:', 'quant:', 'som:', 'kb:add', 'kb:load <file>', 'kb:clear', 'ask:'"
                    ]
                self.ct_chat = [
                    "CT: Demo Mode - Backend services starting...",
                    "Commands: 'shoot player/bot', 'defuse bomb'",
                    "Objective: Prevent bomb plant or defuse if planted!"
                ]
        return False

    async def handle_terrorist_input(self, panel_index: int, text: str) -> Dict[str, Any]:
        """Handle input from terrorist panel"""
        self.chat_logs[panel_index].append(f"You: {text}")
        action = text.lower().strip()
        
        if action.startswith("action:"):
            action = action.split(":", 1)[1].strip()
        
        try:
            # Handle AI queries
            if action.startswith(("rag:", "ag2:", "smart:", "critic:", "quant:", "som:")):
                if self.rag_tries[panel_index] <= 0:
                    self.chat_logs[panel_index].append("AI: No tries left.")
                    return {"success": False, "message": "No tries left"}
                
                self.rag_tries[panel_index] -= 1
                agent_type = action.split(":")[0]
                query = action.split(":", 1)[1].strip()
                
                # Map agent types
                agent_type_map = {
                    "rag": "rag",
                    "ag2": "ag2", 
                    "smart": "smart",
                    "critic": "critic",
                    "quant": "quantifier",
                    "som": "som"
                }
                
                mapped_type = agent_type_map.get(agent_type, agent_type)
                
                try:
                    async with httpx.AsyncClient(timeout=30.0) as client:
                        response = await client.post(
                            f"{self.agent_url}/process",
                            json={
                                "agent_type": mapped_type,
                                "query": query,
                                "context": self.game_state
                            }
                        )
                        
                        if response.status_code == 200:
                            result = response.json()
                            if result["success"]:
                                self.chat_logs[panel_index].append(
                                    f"{agent_type.upper()}: {result['response']} ({self.rag_tries[panel_index]} tries left)"
                                )
                            else:
                                self.chat_logs[panel_index].append(
                                    f"{agent_type.upper()} Error: {result['error'][:100]}... ({self.rag_tries[panel_index]} tries left)"
                                )
                        else:
                            self.chat_logs[panel_index].append(f"{agent_type.upper()} Error: Service unavailable")
                except Exception as e:
                    self.chat_logs[panel_index].append(f"{agent_type.upper()} Error: {str(e)[:100]}...")
            
            # Handle knowledge base commands
            elif action.startswith("kb:add"):
                parts = text.strip().split(" ", 1)
                if len(parts) > 1 and parts[1]:
                    try:
                        async with httpx.AsyncClient(timeout=30.0) as client:
                            response = await client.post(
                                f"{self.agent_url}/kb/add",
                                json={"text": parts[1]}
                            )
                            if response.status_code == 200:
                                result = response.json()
                                self.chat_logs[panel_index].append(f"KB: added {result.get('count', 1)} snippets")
                            else:
                                self.chat_logs[panel_index].append("KB Error: Failed to add text")
                    except Exception as e:
                        self.chat_logs[panel_index].append(f"KB Error: {str(e)[:50]}...")
                else:
                    self.chat_logs[panel_index].append("KB Error: No text provided to add.")
            
            elif action.startswith("kb:load "):
                file_path = action.split(" ", 1)[1].strip()
                try:
                    async with httpx.AsyncClient(timeout=30.0) as client:
                        response = await client.post(
                            f"{self.agent_url}/kb/load",
                            json={"file_path": file_path}
                        )
                        if response.status_code == 200:
                            result = response.json()
                            self.chat_logs[panel_index].append(f"KB: loaded {result.get('count', 0)} chunks")
                        else:
                            self.chat_logs[panel_index].append("KB Error: Failed to load file")
                except Exception as e:
                    self.chat_logs[panel_index].append(f"KB Error: {str(e)[:50]}...")
            
            elif action.strip() == "kb:clear":
                try:
                    async with httpx.AsyncClient(timeout=30.0) as client:
                        response = await client.post(f"{self.agent_url}/kb/clear")
                        if response.status_code == 200:
                            self.chat_logs[panel_index].append("KB: cleared")
                        else:
                            self.chat_logs[panel_index].append("KB Error: Failed to clear")
                except Exception as e:
                    self.chat_logs[panel_index].append(f"KB Error: {str(e)[:50]}...")
            
            elif action.startswith("ask:"):
                query = action.split(":", 1)[1].strip()
                try:
                    async with httpx.AsyncClient(timeout=30.0) as client:
                        response = await client.post(
                            f"{self.agent_url}/kb/ask",
                            json={"query": query}
                        )
                        if response.status_code == 200:
                            result = response.json()
                            answer = result.get('answer', 'no match')
                            self.chat_logs[panel_index].append(f"KB: {answer}")
                        else:
                            self.chat_logs[panel_index].append("KB Error: Failed to query")
                except Exception as e:
                    self.chat_logs[panel_index].append(f"KB Error: {str(e)[:50]}...")
            
            # Handle cheat commands
            elif action.startswith("cheat:"):
                await self.handle_cheat_command(panel_index, action)
            
            # Handle regular game actions
            else:
                try:
                    async with httpx.AsyncClient(timeout=10.0) as client:
                        response = await client.post(
                            f"{self.api_url}/sessions/{self.session_id}/actions",
                            json={
                                "session_id": self.session_id,
                                "team": "Terrorists",
                                "player": "player",
                                "action": action
                            }
                        )
                        
                        if response.status_code == 200:
                            result = response.json()
                            
                            if not result["result"].startswith("Invalid action:"):
                                self.chat_logs[panel_index].append(result["result"])
                                
                                # Broadcast to other terrorist panels
                                for j in range(self.num_panels):
                                    if j != panel_index:
                                        self.chat_logs[j].append(f"T{panel_index+1}: {action}")
                                
                                # Update game state
                                self.game_state = result.get("game_state", self.game_state)
                                
                                # Add status after significant actions
                                if any(keyword in action.lower() for keyword in ["shoot", "plant", "defuse", "move"]):
                                    status = self.game_state.get("game_status", "")
                                    if status:
                                        self.chat_logs[panel_index].append(f"📊 {status}")
                        else:
                            self.chat_logs[panel_index].append(f"Action failed: HTTP {response.status_code}")
                except Exception as e:
                    self.chat_logs[panel_index].append(f"Action error: {str(e)[:100]}...")
            
            # Limit chat log length
            if len(self.chat_logs[panel_index]) > 12:
                self.chat_logs[panel_index] = self.chat_logs[panel_index][-12:]
            
            # Immediately broadcast update to all clients
            await self.broadcast_update()
                
            return {"success": True, "message": "Action processed"}
                
        except Exception as e:
            error_msg = f"Error: {str(e)[:100]}..."
            self.chat_logs[panel_index].append(error_msg)
            return {"success": False, "message": error_msg}

    async def handle_ct_input(self, text: str) -> Dict[str, Any]:
        """Handle input from CT panel"""
        self.ct_chat.append(f"You: {text}")
        action = text.lower().strip()
        
        if action.startswith("action:"):
            action = action.split(":", 1)[1].strip()
        
        try:
            if action.startswith("cheat:"):
                await self.handle_ct_cheat_command(action)
            else:
                try:
                    async with httpx.AsyncClient(timeout=10.0) as client:
                        response = await client.post(
                            f"{self.api_url}/sessions/{self.session_id}/actions",
                            json={
                                "session_id": self.session_id,
                                "team": "Counter-Terrorists",
                                "player": "player",
                                "action": action
                            }
                        )
                        
                        if response.status_code == 200:
                            result = response.json()
                            self.ct_chat.append(result["result"])
                            self.game_state = result.get("game_state", self.game_state)
                            
                            if any(keyword in action.lower() for keyword in ["shoot", "plant", "defuse", "move"]):
                                status = self.game_state.get("game_status", "")
                                if status:
                                    self.ct_chat.append(f"📊 {status}")
                        else:
                            self.ct_chat.append(f"Action failed: HTTP {response.status_code}")
                except Exception as e:
                    self.ct_chat.append(f"Action error: {str(e)[:100]}...")
            
            if len(self.ct_chat) > 12:
                self.ct_chat = self.ct_chat[-12:]
            
            # Immediately broadcast update to all clients
            await self.broadcast_update()
                
            return {"success": True, "message": "Action processed"}
                
        except Exception as e:
            error_msg = f"Error: {str(e)[:100]}..."
            self.ct_chat.append(error_msg)
            return {"success": False, "message": error_msg}

    async def handle_cheat_command(self, panel_index: int, action: str):
        """Handle cheat commands for terrorist panels"""
        cmd = action.split(":", 1)[1].strip()
        
        if cmd in ("status", "site"):
            if self.game_state.get("bomb_planted"):
                site = self.game_state.get("bomb_site", "unknown")
                self.chat_logs[panel_index].append(f"CHEAT: Bomb at {site}")
            else:
                self.chat_logs[panel_index].append("CHEAT: Bomb not planted")
        
        elif cmd == "hp":
            player_health = self.game_state.get("player_health", {})
            if player_health:
                snap = []
                for team, members in player_health.items():
                    snap.append(team + "=" + ",".join(f"{m}:{hp}" for m, hp in members.items()))
                self.chat_logs[panel_index].append("CHEAT: " + " | ".join(snap))
            else:
                self.chat_logs[panel_index].append("CHEAT: No health data available")
        
        else:
            self.chat_logs[panel_index].append("CHEAT: unknown command")

    async def handle_ct_cheat_command(self, action: str):
        """Handle cheat commands for CT panel"""
        cmd = action.split(":", 1)[1].strip()
        
        if cmd in ("status", "site"):
            if self.game_state.get("bomb_planted"):
                site = self.game_state.get("bomb_site", "unknown")
                self.ct_chat.append(f"CHEAT: Bomb at {site}")
            else:
                self.ct_chat.append("CHEAT: Bomb not planted")
        
        elif cmd == "hp":
            player_health = self.game_state.get("player_health", {})
            if player_health:
                snap = []
                for team, members in player_health.items():
                    snap.append(team + "=" + ",".join(f"{m}:{hp}" for m, hp in members.items()))
                self.ct_chat.append("CHEAT: " + " | ".join(snap))
            else:
                self.ct_chat.append("CHEAT: No health data available")
        
        else:
            self.ct_chat.append("CHEAT: unknown command")

    async def get_ui_state(self) -> Dict[str, Any]:
        """Get current UI state for web interface"""
        return {
            "session_id": self.session_id,
            "game_state": self.game_state,
            "terrorist_panels": [
                {
                    "panel_id": i,
                    "chat_log": self.chat_logs[i],
                    "rag_tries": self.rag_tries[i]
                }
                for i in range(self.num_panels)
            ],
            "ct_panel": {
                "chat_log": self.ct_chat
            }
        }


# Global web UI service instance
web_ui = WebUIService()

# FastAPI app for web UI
app = FastAPI(title="Counter-Strike AG2 Web UI", version="1.0.0")

# Mount static files and templates
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")


@app.on_event("startup")
async def startup_event():
    await web_ui.initialize_session()


@app.get("/", response_class=HTMLResponse)
async def get_ui(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@app.get("/api/state")
async def get_state():
    return await web_ui.get_ui_state()


@app.post("/api/terrorist/{panel_id}/input")
async def terrorist_input(panel_id: int, data: dict):
    result = await web_ui.handle_terrorist_input(panel_id, data["text"])
    return result


@app.post("/api/ct/input")
async def ct_input(data: dict):
    result = await web_ui.handle_ct_input(data["text"])
    return result


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    web_ui.connections.append(websocket)
    
    try:
        while True:
            # Send periodic updates
            state = await web_ui.get_ui_state()
            await websocket.send_text(json.dumps(state))
            await asyncio.sleep(2)
    except WebSocketDisconnect:
        web_ui.connections.remove(websocket)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8082)
