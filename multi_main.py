from __future__ import annotations

import random
from typing import List

import pygame

from counter_strike_ag2_agent.agents import create_terrorists_group
from counter_strike_ag2_agent.contrib_integration import (run_critic,
                                                          run_quantifier,
                                                          run_som)
from counter_strike_ag2_agent.game_state import GameState
from counter_strike_ag2_agent.rag import RagTerroristHelper
from counter_strike_ag2_agent.rag_vector import ChromaRAG
from counter_strike_ag2_agent.ui import InputBox, render_ui


def run_multi(num_instances: int = 3, show_ct: bool = True) -> None:
    getattr(pygame, "init", lambda: None)()
    # Initialize clipboard for copy/paste support
    try:
        pygame.scrap.init()  # type: ignore[attr-defined]
    except Exception:
        pass
    # Grid based on total panels (terrorists + optional CT)
    total_panels = num_instances + (1 if show_ct else 0)
    cols = min(2, total_panels)
    rows = (total_panels + cols - 1) // cols
    # Slightly larger tiles for better readability
    panel_w, panel_h = 700, 360
    pad = 10
    width = cols * panel_w + (cols + 1) * pad
    height = rows * panel_h + (rows + 1) * pad
    screen = pygame.display.set_mode((width, height))
    pygame.display.set_caption("Counter-Strike AG2 Multi-Agent")

    clock = pygame.time.Clock()
    kb = ChromaRAG()  # shared collection for demo

    # Shared state and shared terrorists group chat
    state = GameState()
    manager, _ = create_terrorists_group(num_players=num_instances)

    chat_logs: List[List[str]] = []
    input_boxes: List[InputBox] = []
    rects: List[pygame.Rect] = []
    ct_rect: pygame.Rect | None = None
    rag_tries: List[int] = []  # 5 tries per player
    next_round_votes: List[int] = []  # fun hint counter per player
    scroll_offsets: List[int] = []

    for i in range(num_instances):
        r = i // cols
        c = i % cols
        x = pad + c * (panel_w + pad)
        y = pad + r * (panel_h + pad)
        rects.append(pygame.Rect(x, y, panel_w, panel_h))
        chat_logs.append([
            f"T{i+1}: Ready! Round {state.round}/{state.max_rounds}",
            "Commands: 'shoot player/bot', 'plant bomb', 'move to A-site', 'defuse bomb'",
            "AI Help: 'rag:', 'ag2:', 'smart:', 'kb:add', 'kb:load <file>', 'kb:clear', 'ask:'"
        ]) 
        input_boxes.append(InputBox(x + 10, y + panel_h - 50, panel_w - 20, 32))
        rag_tries.append(5)
        next_round_votes.append(0)
        scroll_offsets.append(0)

    # CT panel (separate; cannot see T chat)
    ct_input: InputBox | None = None
    ct_chat: List[str] | None = None
    if show_ct:
        ct_index = num_instances  # Place CT after all T panels in the same grid
        r = ct_index // cols
        c = ct_index % cols
        x = pad + c * (panel_w + pad)
        y = pad + r * (panel_h + pad)
        ct_rect = pygame.Rect(x, y, panel_w, panel_h)
        ct_input = InputBox(x + 10, y + panel_h - 50, panel_w - 20, 32)
        ct_chat = [
            f"CT: Ready! Round {state.round}/{state.max_rounds}",
            "Commands: 'shoot player/bot', 'defuse bomb', 'move to A-site/B-site'",
            "Objective: Prevent bomb plant or defuse if planted!"
        ]
        ct_scroll_offset = 0

    running = True
    while running:
        events = pygame.event.get()
        for event in events:
            if event.type == getattr(pygame, "QUIT", None):
                running = False
            if event.type == getattr(pygame, "MOUSEWHEEL", None):
                mx, my = pygame.mouse.get_pos()
                for i, rect in enumerate(rects):
                    if rect.collidepoint(mx, my):
                        scroll_offsets[i] = max(0, scroll_offsets[i] + event.y)
                if show_ct and ct_rect is not None and ct_rect.collidepoint(mx, my):
                    ct_scroll_offset = max(0, ct_scroll_offset + event.y)
            # route input to the panel box that is active
            for i, ib in enumerate(input_boxes):
                text = ib.handle_event(event)
                if text is not None:
                    chat_logs[i].append(f"You: {text}")
                    action = text.lower().strip()
                    if action.startswith("action:"):
                        action = action.split(":", 1)[1].strip()
                    # RAG helper (offline heuristic)
                    if action.startswith("rag:" ):
                        if rag_tries[i] <= 0:
                            chat_logs[i].append("RAG: No tries left.")
                        else:
                            rag_tries[i] -= 1
                            q = action.split(":", 1)[1].strip()
                            ans = RagTerroristHelper.answer(q, state)
                            chat_logs[i].append(f"RAG: {ans} ({rag_tries[i]} tries left)")
                    # AG2 Agent query: messages starting with 'ag2:'
                    elif action.startswith("ag2:"):
                        if rag_tries[i] <= 0:
                            chat_logs[i].append("AG2: No tries left.")
                        else:
                            rag_tries[i] -= 1
                            q = action.split(":", 1)[1].strip()
                            try:
                                # Get comprehensive game context
                                game_status = state.get_game_status()
                                game_facts = RagTerroristHelper.build_facts(state)
                                context = f"Game Status: {game_status}\nDetailed Context: {' '.join(game_facts)}\n\nQuestion: {q}\n\nGive a SHORT tactical response (1-2 sentences max)."
                                
                                # Create a message for the bot
                                user_message = {"content": context, "role": "user"}
                                
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
                                
                                chat_logs[i].append(f"AG2: {response_text} ({rag_tries[i]} tries left)")
                            except Exception as e:
                                error_msg = str(e)
                                if "Could not find bot agent" in error_msg:
                                    chat_logs[i].append(f"AG2 Error: Bot agent not found. Check AG2 setup. ({rag_tries[i]} tries left)")
                                elif "api" in error_msg.lower() or "key" in error_msg.lower():
                                    chat_logs[i].append(f"AG2 Error: API issue - {error_msg[:100]}... ({rag_tries[i]} tries left)")
                                else:
                                    chat_logs[i].append(f"AG2 Error: {error_msg[:100]}... ({rag_tries[i]} tries left)")
                    # Vector RAG: knowledge base management and ask
                    elif action.startswith("kb:add"):
                        parts = text.strip().split(" ", 1)
                        if len(parts) > 1 and parts[1]:
                            added = kb.add_texts([parts[1]])
                            chat_logs[i].append(f"KB: added {added} snippets")
                        else:
                            chat_logs[i].append("KB Error: No text provided to add.")
                    elif action.startswith("kb:load "):
                        # Clear then load to ensure reload reflects updates
                        kb.clear()
                        cnt = kb.add_file(text.strip().split(" ", 1)[1].strip())
                        chat_logs[i].append(f"KB: loaded {cnt} chunks")
                    elif action.strip() == "kb:clear":
                        kb.clear()
                        chat_logs[i].append("KB: cleared")
                    elif action.startswith("ask:"):
                        q = action.split(":", 1)[1].strip()
                        ans = kb.ask(q)
                        chat_logs[i].append(f"KB: {ans or 'no match'}")
                    # Smart AG2+RAG query: messages starting with 'smart:'
                    elif action.startswith("smart:"):
                        if rag_tries[i] <= 0:
                            chat_logs[i].append("SMART: No tries left.")
                        else:
                            rag_tries[i] -= 1
                            q = action.split(":", 1)[1].strip()
                            try:
                                # Get comprehensive game context and knowledge base info
                                game_status = state.get_game_status()
                                game_facts = RagTerroristHelper.build_facts(state)
                                kb_info = kb.ask(q) or "No relevant knowledge found"
                                
                                context = f"""Game Status: {game_status}
Detailed Context: {' '.join(game_facts)}
Knowledge Base: {kb_info}
Question: {q}

Give SHORT tactical advice (1-2 sentences max) based on the current game state and available knowledge."""
                                
                                # Create a message for the bot
                                user_message = {"content": context, "role": "user"}
                                
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
                                
                                chat_logs[i].append(f"SMART: {response_text} ({rag_tries[i]} tries left)")
                            except Exception as e:
                                error_msg = str(e)
                                if "Could not find bot agent" in error_msg:
                                    chat_logs[i].append(f"SMART Error: Bot agent not found. Check AG2 setup. ({rag_tries[i]} tries left)")
                                elif "api" in error_msg.lower() or "key" in error_msg.lower():
                                    chat_logs[i].append(f"SMART Error: API issue - {error_msg[:100]}... ({rag_tries[i]} tries left)")
                                else:
                                    chat_logs[i].append(f"SMART Error: {error_msg[:100]}... ({rag_tries[i]} tries left)")
                    # New: Critic evaluation of a plan using AG2 contrib CriticAgent
                    elif action.startswith("critic:"):
                        if rag_tries[i] <= 0:
                            chat_logs[i].append("CRITIC: No tries left.")
                        else:
                            rag_tries[i] -= 1
                            plan = action.split(":", 1)[1].strip()
                            res = run_critic(plan, state)
                            chat_logs[i].append(f"CRITIC: {res} ({rag_tries[i]} tries left)")
                    # New: Quantifier selection among options. Format: quant: opt1 | opt2 | opt3
                    elif action.startswith("quant:"):
                        if rag_tries[i] <= 0:
                            chat_logs[i].append("QUANT: No tries left.")
                        else:
                            rag_tries[i] -= 1
                            raw = action.split(":", 1)[1].strip()
                            options = [o.strip() for o in raw.split("|") if o.strip()]
                            res = run_quantifier(options, state)
                            chat_logs[i].append(f"QUANT: {res} ({rag_tries[i]} tries left)")
                    # New: Society-of-Mind reasoning for complex questions
                    elif action.startswith("som:"):
                        if rag_tries[i] <= 0:
                            chat_logs[i].append("SOM: No tries left.")
                        else:
                            rag_tries[i] -= 1
                            q = action.split(":", 1)[1].strip()
                            res = run_som(q, state)
                            chat_logs[i].append(f"SOM: {res} ({rag_tries[i]} tries left)")
                    elif action.startswith("cheat:"):
                        cmd = action.split(":", 1)[1].strip()
                        if cmd in ("status", "site"):
                            if state.bomb_planted:
                                chat_logs[i].append(f"CHEAT: Bomb at {state.bomb_site}")
                            else:
                                chat_logs[i].append("CHEAT: Bomb not planted")
                        elif cmd == "ct":
                            ct_alive = sum(1 for hp in state.player_health.get("Counter-Terrorists", {}).values() if hp > 0)
                            chat_logs[i].append(f"CHEAT: CT alive {ct_alive}")
                        elif cmd == "hp":
                            snap = []
                            for team, members in state.player_health.items():
                                snap.append(team + "=" + ",".join(f"{m}:{hp}" for m, hp in members.items()))
                            chat_logs[i].append("CHEAT: " + " | ".join(snap))
                        elif cmd == "next":
                            next_round_votes[i] += 1
                            need = max(1, len(next_round_votes) // 2)
                            chat_logs[i].append(f"CHEAT: next-round vote {next_round_votes[i]}/{need}")
                            # If majority votes, reset round with a pirate flair hint
                            if sum(1 for v in next_round_votes if v > 0) >= need:
                                for p in range(len(chat_logs)):
                                    chat_logs[p].append("Captain: Trim the sails! New round be upon us.")
                                    next_round_votes[p] = 0
                                state.reset_round()
                        else:
                            chat_logs[i].append("CHEAT: unknown command")
                    else:
                        # Apply action in shared game state (single terrorist entity key 'player')
                        result = state.apply_action("Terrorists", "player", action)
                        
                        # Check if action was invalid
                        if result.startswith("Invalid action:"):
                            # Don't show invalid actions to anyone - completely silent
                            pass
                        else:
                            # Valid action - show result to current player
                            chat_logs[i].append(result)
                            
                            # Broadcast teammate actions to all T panels for shared awareness
                            for j in range(num_instances):
                                if j != i:
                                    chat_logs[j].append(f"T{i+1}: {action}")
                        
                        # Add game status after significant actions
                        if any(keyword in action.lower() for keyword in ["shoot", "plant", "defuse", "move"]):
                            status = state.get_game_status()
                            chat_logs[i].append(f"📊 {status}")
                        
                        # Check if round is over
                        if state.is_round_over():
                            winner_msg = f"🏆 Round {state.round} won by {state.winner}!"
                            for j in range(num_instances):
                                chat_logs[j].append(winner_msg)
                            if ct_chat is not None:
                                ct_chat.append(winner_msg)
                                
                            # Check if game is over
                            if state.is_game_over():
                                final_winner = max(state.round_scores.items(), key=lambda x: x[1])[0]
                                game_over_msg = f"🎯 GAME OVER! {final_winner} wins the match!"
                                for j in range(num_instances):
                                    chat_logs[j].append(game_over_msg)
                                if ct_chat is not None:
                                    ct_chat.append(game_over_msg)
                            else:
                                # Start new round
                                state.reset_round()
                                new_round_msg = f"🔄 Round {state.round} starting..."
                                for j in range(num_instances):
                                    chat_logs[j].append(new_round_msg)
                                if ct_chat is not None:
                                    ct_chat.append(new_round_msg)
                        
                        # Smart CT response based on game state
                        if ct_chat is not None and not state.is_round_over():
                            # CT responds intelligently based on situation
                            if state.bomb_planted:
                                ct_action = "defuse bomb"
                            elif any(hp <= 50 for hp in state.player_health["Counter-Terrorists"].values()):
                                ct_action = "shoot player"  # Fight back when hurt
                            else:
                                ct_action = random.choice(["shoot player", "move to A-site", "move to B-site"])
                            
                            ct_res = state.apply_action("Counter-Terrorists", "player", ct_action)
                            ct_chat.append(f"CT: {ct_action}")
                            ct_chat.append(ct_res)
                        
                        # Limit chat log to last 12 messages to prevent UI overflow
                        for j in range(num_instances):
                            if len(chat_logs[j]) > 12:
                                chat_logs[j] = chat_logs[j][-12:]

            # CT panel input
            if show_ct and ct_input is not None and ct_chat is not None:
                text_ct = ct_input.handle_event(event)
                if text_ct is not None:
                    ct_chat.append(f"You: {text_ct}")
                    act_ct = text_ct.lower().strip()
                    if act_ct.startswith("action:"):
                        act_ct = act_ct.split(":", 1)[1].strip()
                    if act_ct.startswith("cheat:"):
                        cmd = act_ct.split(":", 1)[1].strip()
                        if cmd in ("status", "site"):
                            if state.bomb_planted:
                                ct_chat.append(f"CHEAT: Bomb at {state.bomb_site}")
                            else:
                                ct_chat.append("CHEAT: Bomb not planted")
                        elif cmd == "ct":
                            ct_alive = sum(1 for hp in state.player_health.get("Counter-Terrorists", {}).values() if hp > 0)
                            ct_chat.append(f"CHEAT: CT alive {ct_alive}")
                        elif cmd == "hp":
                            snap = []
                            for team, members in state.player_health.items():
                                snap.append(team + "=" + ",".join(f"{m}:{hp}" for m, hp in members.items()))
                            ct_chat.append("CHEAT: " + " | ".join(snap))
                        else:
                            ct_chat.append("CHEAT: unknown command")
                    else:
                        res_ct = state.apply_action("Counter-Terrorists", "player", act_ct)
                        ct_chat.append(res_ct)
                        
                        # Add game status for CT after actions
                        if any(keyword in act_ct.lower() for keyword in ["shoot", "plant", "defuse", "move"]):
                            status = state.get_game_status()
                            ct_chat.append(f"📊 {status}")
                        
                        # Limit CT chat log to last 12 messages
                        if len(ct_chat) > 12:
                            ct_chat = ct_chat[-12:]
        # Draw panels
        screen.fill((10, 10, 10))
        for i, rect in enumerate(rects):
            sub = screen.subsurface(rect)
            input_boxes[i].update()
            render_ui(sub, chat_logs[i], input_boxes[i], rect.width, rect.height, scroll_offsets[i])
        if show_ct and ct_rect is not None and ct_input is not None and ct_chat is not None:
            sub_ct = screen.subsurface(ct_rect)
            ct_input.update()
            render_ui(sub_ct, ct_chat, ct_input, ct_rect.width, ct_rect.height, ct_scroll_offset if 'ct_scroll_offset' in locals() else 0)

        pygame.display.flip()
        clock.tick(30)

    getattr(pygame, "quit", lambda: None)()


if __name__ == "__main__":
    run_multi(3)


