from typing import List

import pygame

from counter_strike_ag2_agent.game_state import GameState
from counter_strike_ag2_agent.agents import create_team
from counter_strike_ag2_agent.ui import InputBox, render_ui


def main() -> None:
    pygame.init()
    width, height = 800, 600
    screen = pygame.display.set_mode((width, height))
    pygame.display.set_caption("Counter-Strike AG2 Agent")

    clock = pygame.time.Clock()
    input_box = InputBox(10, height - 50, 500, 32)
    chat_log: List[str] = ["Welcome! Type actions like 'shoot', 'plant bomb', 'defuse bomb'."]

    state = GameState()
    create_team("Terrorists", is_terrorists=True)
    create_team("Counter-Terrorists", is_terrorists=False)

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            text = input_box.handle_event(event)
            if text is not None:
                chat_log.append(f"You: {text}")
                # Simple routing: treat any text starting with 'action:' as an action
                action = text.lower().strip()
                if action.startswith("action:"):
                    action = action.split(":", 1)[1].strip()
                result = state.apply_action("Terrorists", "player", action)
                chat_log.append(result)
                # CT simple response: always attempt to shoot
                ct_result = state.apply_action("Counter-Terrorists", "player", "shoot player")
                chat_log.append(f"CT: {ct_result}")

        input_box.update()
        render_ui(screen, chat_log, input_box, width, height)

        clock.tick(30)

    pygame.quit()


if __name__ == "__main__":
    main()


