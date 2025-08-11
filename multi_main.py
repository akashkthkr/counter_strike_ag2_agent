from __future__ import annotations

from typing import List, Tuple

import pygame

from counter_strike_ag2_agent.game_state import GameState
from counter_strike_ag2_agent.agents import create_terrorists_group
from counter_strike_ag2_agent.ui import InputBox, render_ui
from counter_strike_ag2_agent.rag import RagTerroristHelper
from counter_strike_ag2_agent.rag_vector import ChromaRAG


def run_multi(num_instances: int = 3, show_ct: bool = True) -> None:
    pygame.init()
    cols = min(2, num_instances)
    rows = (num_instances + cols - 1) // cols
    panel_w, panel_h = 600, 400
    pad = 10
    width = cols * panel_w + (cols + 1) * pad
    height_rows = rows + (1 if show_ct else 0)
    height = height_rows * panel_h + (height_rows + 1) * pad
    screen = pygame.display.set_mode((width, height))
    pygame.display.set_caption("Counter-Strike AG2 Multi-Agent")

    clock = pygame.time.Clock()
    kb = ChromaRAG()  # shared collection for demo

    # Shared state and shared terrorists group chat
    state = GameState()
    manager, players = create_terrorists_group(num_players=num_instances)

    chat_logs: List[List[str]] = []
    input_boxes: List[InputBox] = []
    rects: List[pygame.Rect] = []
    ct_rect: pygame.Rect | None = None
    rag_tries: List[int] = []  # 3 tries per player
    next_round_votes: List[int] = []  # fun hint counter per player

    for i in range(num_instances):
        r = i // cols
        c = i % cols
        x = pad + c * (panel_w + pad)
        y = pad + r * (panel_h + pad)
        rects.append(pygame.Rect(x, y, panel_w, panel_h))
        chat_logs.append([f"T{i+1}: Ready. Type actions like 'shoot' or 'plant bomb'."]) 
        input_boxes.append(InputBox(x + 10, y + panel_h - 50, panel_w - 20, 32))
        rag_tries.append(3)
        next_round_votes.append(0)

    # CT panel (separate; cannot see T chat)
    ct_input: InputBox | None = None
    ct_chat: List[str] | None = None
    if show_ct:
        x = pad + (cols - 1) * (panel_w + pad)
        y = pad + rows * (panel_h + pad)
        ct_rect = pygame.Rect(x, y, panel_w, panel_h)
        ct_input = InputBox(x + 10, y + panel_h - 50, panel_w - 20, 32)
        ct_chat = ["CT: Ready. Type actions like 'shoot' or 'defuse bomb'."]

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            # route input to the panel box that is active
            for i, ib in enumerate(input_boxes):
                text = ib.handle_event(event)
                if text is not None:
                    chat_logs[i].append(f"You: {text}")
                    action = text.lower().strip()
                    if action.startswith("action:"):
                        action = action.split(":", 1)[1].strip()
                    # RAG query: messages starting with 'rag:'
                    if action.startswith("rag:"):
                        if rag_tries[i] <= 0:
                            chat_logs[i].append("RAG: No tries left.")
                        else:
                            rag_tries[i] -= 1
                            q = action.split(":", 1)[1].strip()
                            ans = RagTerroristHelper.answer(q, state)
                            chat_logs[i].append(f"RAG: {ans} ({rag_tries[i]} tries left)")
                    # Vector RAG: knowledge base management and ask
                    elif action.startswith("kb:add "):
                        added = kb.add_texts([action.split(" ", 1)[1].strip()])
                        chat_logs[i].append(f"KB: added {added} snippets")
                    elif action.startswith("kb:load "):
                        cnt = kb.add_file(action.split(" ", 1)[1].strip())
                        chat_logs[i].append(f"KB: loaded {cnt} chunks")
                    elif action.startswith("ask:"):
                        q = action.split(":", 1)[1].strip()
                        ans = kb.ask(q)
                        chat_logs[i].append(f"KB: {ans or 'no match'}")
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
                        # Apply action in shared game state for terrorists player i
                        result = state.apply_action("Terrorists", f"player{i+1}", action)
                        chat_logs[i].append(result)
                        # Broadcast teammate actions to all T panels for shared awareness
                        for j in range(num_instances):
                            if j != i:
                                chat_logs[j].append(f"T{i+1}: {action}")
                        # CT takes a simple reactive turn (visible in CT panel only)
                        if ct_chat is not None:
                            ct_res = state.apply_action("Counter-Terrorists", "player", "shoot player")
                            ct_chat.append(ct_res)

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
        # Draw panels
        screen.fill((10, 10, 10))
        for i, rect in enumerate(rects):
            sub = screen.subsurface(rect)
            input_boxes[i].update()
            render_ui(sub, chat_logs[i], input_boxes[i], rect.width, rect.height)
        if show_ct and ct_rect is not None and ct_input is not None and ct_chat is not None:
            sub_ct = screen.subsurface(ct_rect)
            ct_input.update()
            render_ui(sub_ct, ct_chat, ct_input, ct_rect.width, ct_rect.height)

        pygame.display.flip()
        clock.tick(30)

    pygame.quit()


if __name__ == "__main__":
    run_multi(3)


