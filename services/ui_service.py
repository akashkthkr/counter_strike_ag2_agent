import os
import json
import asyncio
import aiohttp
from typing import List, Dict, Any, Optional
from datetime import datetime

import pygame

from counter_strike_ag2_agent.ui import InputBox, render_ui


class APIClient:
    def __init__(self, api_url: str, agent_url: str):
        self.api_url = api_url
        self.agent_url = agent_url
        self.session: Optional[aiohttp.ClientSession] = None

    async def initialize(self):
        self.session = aiohttp.ClientSession()

    async def close(self):
        if self.session:
            await self.session.close()

    async def create_session(self, session_name: str, max_rounds: int = 3) -> Dict[str, Any]:
        async with self.session.post(
            f"{self.api_url}/sessions",
            json={"session_name": session_name, "max_rounds": max_rounds}
        ) as response:
            return await response.json()

    async def get_game_state(self, session_id: str) -> Dict[str, Any]:
        async with self.session.get(f"{self.api_url}/sessions/{session_id}/state") as response:
            return await response.json()

    async def apply_action(self, session_id: str, team: str, player: str, action: str) -> Dict[str, Any]:
        async with self.session.post(
            f"{self.api_url}/sessions/{session_id}/actions",
            json={
                "session_id": session_id,
                "team": team,
                "player": player,
                "action": action
            }
        ) as response:
            return await response.json()

    async def query_agent(self, agent_type: str, query: str, context: Dict[str, Any]) -> Dict[str, Any]:
        async with self.session.post(
            f"{self.agent_url}/process",
            json={
                "agent_type": agent_type,
                "query": query,
                "context": context
            }
        ) as response:
            return await response.json()


class DockerizedUI:
    def __init__(self, num_instances: int = 3, show_ct: bool = True):
        self.num_instances = num_instances
        self.show_ct = show_ct
        
        # API configuration
        api_url = os.getenv("API_URL", "http://localhost:8080")
        agent_url = os.getenv("AGENT_URL", "http://localhost:8081")
        self.api_client = APIClient(api_url, agent_url)
        
        # Game session
        self.session_id: Optional[str] = None
        self.game_state: Dict[str, Any] = {}
        
        # UI state
        self.chat_logs: List[List[str]] = []
        self.input_boxes: List[InputBox] = []
        self.rects: List[pygame.Rect] = []
        self.ct_rect: Optional[pygame.Rect] = None
        self.rag_tries: List[int] = []
        self.scroll_offsets: List[int] = []
        
        # CT panel state
        self.ct_input: Optional[InputBox] = None
        self.ct_chat: Optional[List[str]] = None
        self.ct_scroll_offset: int = 0

    async def initialize(self):
        await self.api_client.initialize()
        
        # Create game session
        session_data = await self.api_client.create_session(
            session_name=f"Docker Session {datetime.now().strftime('%H:%M:%S')}",
            max_rounds=3
        )
        self.session_id = session_data["id"]
        
        # Initialize Pygame
        pygame.init()
        try:
            pygame.scrap.init()
        except Exception:
            pass
        
        # Setup UI layout
        total_panels = self.num_instances + (1 if self.show_ct else 0)
        cols = min(2, total_panels)
        rows = (total_panels + cols - 1) // cols
        panel_w, panel_h = 700, 360
        pad = 10
        width = cols * panel_w + (cols + 1) * pad
        height = rows * panel_h + (rows + 1) * pad
        
        self.screen = pygame.display.set_mode((width, height))
        pygame.display.set_caption("Counter-Strike AG2 Multi-Agent (Dockerized)")
        self.clock = pygame.time.Clock()
        
        # Initialize panels
        for i in range(self.num_instances):
            r = i // cols
            c = i % cols
            x = pad + c * (panel_w + pad)
            y = pad + r * (panel_h + pad)
            self.rects.append(pygame.Rect(x, y, panel_w, panel_h))
            self.chat_logs.append([
                f"T{i+1}: Ready! Docker Session {self.session_id[:8]}",
                "Commands: 'shoot player/bot', 'plant bomb', 'move to A-site', 'defuse bomb'",
                "AI Help: 'rag:', 'ag2:', 'smart:', 'critic:', 'quant:', 'som:', 'kb:add', 'kb:load <file>', 'kb:clear', 'ask:'"
            ])
            self.input_boxes.append(InputBox(x + 10, y + panel_h - 50, panel_w - 20, 32))
            self.rag_tries.append(5)
            self.scroll_offsets.append(0)
        
        # CT panel
        if self.show_ct:
            ct_index = self.num_instances
            r = ct_index // cols
            c = ct_index % cols
            x = pad + c * (panel_w + pad)
            y = pad + r * (panel_h + pad)
            self.ct_rect = pygame.Rect(x, y, panel_w, panel_h)
            self.ct_input = InputBox(x + 10, y + panel_h - 50, panel_w - 20, 32)
            self.ct_chat = [
                f"CT: Ready! Docker Session {self.session_id[:8]}",
                "Commands: 'shoot player/bot', 'defuse bomb', 'move to A-site/B-site'",
                "Objective: Prevent bomb plant or defuse if planted!"
            ]
        
        # Get initial game state
        self.game_state = await self.api_client.get_game_state(self.session_id)

    async def run(self):
        await self.initialize()
        
        running = True
        while running:
            events = pygame.event.get()
            for event in events:
                if event.type == pygame.QUIT:
                    running = False
                
                if event.type == getattr(pygame, "MOUSEWHEEL", None):
                    mx, my = pygame.mouse.get_pos()
                    for i, rect in enumerate(self.rects):
                        if rect.collidepoint(mx, my):
                            self.scroll_offsets[i] = max(0, self.scroll_offsets[i] + event.y)
                    if self.show_ct and self.ct_rect and self.ct_rect.collidepoint(mx, my):
                        self.ct_scroll_offset = max(0, self.ct_scroll_offset + event.y)
                
                # Handle terrorist panel inputs
                for i, ib in enumerate(self.input_boxes):
                    text = ib.handle_event(event)
                    if text is not None:
                        await self.handle_terrorist_input(i, text)
                
                # Handle CT panel input
                if self.show_ct and self.ct_input:
                    text_ct = self.ct_input.handle_event(event)
                    if text_ct is not None:
                        await self.handle_ct_input(text_ct)
            
            # Update input boxes
            for ib in self.input_boxes:
                ib.update()
            if self.ct_input:
                self.ct_input.update()
            
            # Render UI
            self.screen.fill((10, 10, 10))
            for i, rect in enumerate(self.rects):
                sub = self.screen.subsurface(rect)
                render_ui(sub, self.chat_logs[i], self.input_boxes[i], rect.width, rect.height, self.scroll_offsets[i])
            
            if self.show_ct and self.ct_rect and self.ct_input and self.ct_chat:
                sub_ct = self.screen.subsurface(self.ct_rect)
                render_ui(sub_ct, self.ct_chat, self.ct_input, self.ct_rect.width, self.ct_rect.height, self.ct_scroll_offset)
            
            pygame.display.flip()
            self.clock.tick(30)
        
        await self.cleanup()

    async def handle_terrorist_input(self, panel_index: int, text: str):
        self.chat_logs[panel_index].append(f"You: {text}")
        action = text.lower().strip()
        
        if action.startswith("action:"):
            action = action.split(":", 1)[1].strip()
        
        try:
            # Handle AI queries
            if action.startswith(("rag:", "ag2:", "smart:", "critic:", "quant:", "som:")):
                if self.rag_tries[panel_index] <= 0:
                    self.chat_logs[panel_index].append("AI: No tries left.")
                    return
                
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
                
                response = await self.api_client.query_agent(
                    mapped_type, 
                    query, 
                    self.game_state
                )
                
                if response["success"]:
                    self.chat_logs[panel_index].append(
                        f"{agent_type.upper()}: {response['response']} ({self.rag_tries[panel_index]} tries left)"
                    )
                else:
                    self.chat_logs[panel_index].append(
                        f"{agent_type.upper()} Error: {response['error'][:100]}... ({self.rag_tries[panel_index]} tries left)"
                    )
            
            # Handle cheat commands
            elif action.startswith("cheat:"):
                await self.handle_cheat_command(panel_index, action)
            
            # Handle regular game actions
            else:
                result = await self.api_client.apply_action(
                    self.session_id, 
                    "Terrorists", 
                    "player", 
                    action
                )
                
                if not result["result"].startswith("Invalid action:"):
                    self.chat_logs[panel_index].append(result["result"])
                    
                    # Broadcast to other terrorist panels
                    for j in range(self.num_instances):
                        if j != panel_index:
                            self.chat_logs[j].append(f"T{panel_index+1}: {action}")
                    
                    # Update game state
                    self.game_state = result["game_state"]
                    
                    # Add status after significant actions
                    if any(keyword in action.lower() for keyword in ["shoot", "plant", "defuse", "move"]):
                        status = self.game_state.get("game_status", "")
                        self.chat_logs[panel_index].append(f"📊 {status}")
                    
                    # Handle round/game end
                    if self.game_state.get("is_round_over"):
                        winner = self.game_state.get("winner", "Unknown")
                        round_num = self.game_state.get("round", 1)
                        winner_msg = f"🏆 Round {round_num} won by {winner}!"
                        
                        for j in range(self.num_instances):
                            self.chat_logs[j].append(winner_msg)
                        if self.ct_chat:
                            self.ct_chat.append(winner_msg)
                        
                        if self.game_state.get("is_game_over"):
                            game_over_msg = "🎯 GAME OVER!"
                            for j in range(self.num_instances):
                                self.chat_logs[j].append(game_over_msg)
                            if self.ct_chat:
                                self.ct_chat.append(game_over_msg)
            
            # Limit chat log length
            if len(self.chat_logs[panel_index]) > 12:
                self.chat_logs[panel_index] = self.chat_logs[panel_index][-12:]
                
        except Exception as e:
            self.chat_logs[panel_index].append(f"Error: {str(e)[:100]}...")

    async def handle_ct_input(self, text: str):
        if not self.ct_chat:
            return
            
        self.ct_chat.append(f"You: {text}")
        action = text.lower().strip()
        
        if action.startswith("action:"):
            action = action.split(":", 1)[1].strip()
        
        try:
            if action.startswith("cheat:"):
                await self.handle_ct_cheat_command(action)
            else:
                result = await self.api_client.apply_action(
                    self.session_id,
                    "Counter-Terrorists", 
                    "player", 
                    action
                )
                
                self.ct_chat.append(result["result"])
                self.game_state = result["game_state"]
                
                if any(keyword in action.lower() for keyword in ["shoot", "plant", "defuse", "move"]):
                    status = self.game_state.get("game_status", "")
                    self.ct_chat.append(f"📊 {status}")
            
            if len(self.ct_chat) > 12:
                self.ct_chat = self.ct_chat[-12:]
                
        except Exception as e:
            self.ct_chat.append(f"Error: {str(e)[:100]}...")

    async def handle_cheat_command(self, panel_index: int, action: str):
        cmd = action.split(":", 1)[1].strip()
        
        if cmd in ("status", "site"):
            if self.game_state.get("bomb_planted"):
                site = self.game_state.get("bomb_site", "unknown")
                self.chat_logs[panel_index].append(f"CHEAT: Bomb at {site}")
            else:
                self.chat_logs[panel_index].append("CHEAT: Bomb not planted")
        
        elif cmd == "hp":
            player_health = self.game_state.get("player_health", {})
            snap = []
            for team, members in player_health.items():
                snap.append(team + "=" + ",".join(f"{m}:{hp}" for m, hp in members.items()))
            self.chat_logs[panel_index].append("CHEAT: " + " | ".join(snap))
        
        else:
            self.chat_logs[panel_index].append("CHEAT: unknown command")

    async def handle_ct_cheat_command(self, action: str):
        if not self.ct_chat:
            return
            
        cmd = action.split(":", 1)[1].strip()
        
        if cmd in ("status", "site"):
            if self.game_state.get("bomb_planted"):
                site = self.game_state.get("bomb_site", "unknown")
                self.ct_chat.append(f"CHEAT: Bomb at {site}")
            else:
                self.ct_chat.append("CHEAT: Bomb not planted")
        
        elif cmd == "hp":
            player_health = self.game_state.get("player_health", {})
            snap = []
            for team, members in player_health.items():
                snap.append(team + "=" + ",".join(f"{m}:{hp}" for m, hp in members.items()))
            self.ct_chat.append("CHEAT: " + " | ".join(snap))
        
        else:
            self.ct_chat.append("CHEAT: unknown command")

    async def cleanup(self):
        await self.api_client.close()
        pygame.quit()


async def main():
    ui = DockerizedUI(num_instances=3, show_ct=True)
    await ui.run()


if __name__ == "__main__":
    asyncio.run(main())
