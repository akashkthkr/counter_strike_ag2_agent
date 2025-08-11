# ui.py: Pygame UI components
import pygame
from pygame.locals import MOUSEBUTTONDOWN, KEYDOWN, K_RETURN, K_BACKSPACE  # Event constants

class InputBox:
    """Pygame text input box for user messages/actions."""
    
    def __init__(self, x: int, y: int, w: int, h: int, text: str = '') -> None:
        """Initialize input box with position and size."""
        self.rect = pygame.Rect(x, y, w, h)
        self.color = pygame.Color('lightskyblue3')
        self.text: str = text
        self.font = pygame.font.Font(None, 32)
        self.txt_surface = self.font.render(text, True, self.color)
        self.active: bool = False

    def handle_event(self, event: pygame.event.Event) -> str | None:
        """Handle mouse/key events for input.
        
        Algorithm: Activate on click, append chars, backspace, return on enter.
        Edge case: Empty text on enter -> return None (ignore).
        Returns: Input text on enter, else None.
        """
        if event.type == MOUSEBUTTONDOWN:
            self.active = self.rect.collidepoint(event.pos)
        if event.type == KEYDOWN and self.active:
            if event.key == K_RETURN:
                if not self.text:
                    return None
                out = self.text
                self.text = ""
                self.txt_surface = self.font.render(self.text, True, self.color)
                return out
            elif event.key == K_BACKSPACE:
                self.text = self.text[:-1]
            else:
                self.text += event.unicode
            self.txt_surface = self.font.render(self.text, True, self.color)
        return None

    def update(self) -> None:
        """Update box width based on text."""
        self.rect.w = max(200, self.txt_surface.get_width() + 10)  # Dynamic resize

    def draw(self, screen: pygame.Surface) -> None:
        """Draw the box and text on screen."""
        # Adjust for subsurface offset so elements render inside panels
        try:
            off_x, off_y = screen.get_abs_offset()
        except Exception:
            off_x, off_y = 0, 0
        local_rect = pygame.Rect(
            self.rect.x - off_x,
            self.rect.y - off_y,
            self.rect.w,
            self.rect.h,
        )
        screen.blit(self.txt_surface, (local_rect.x + 5, local_rect.y + 5))
        pygame.draw.rect(screen, self.color, local_rect, 2)

def render_ui(
    screen: pygame.Surface,
    chat_log: list[str],
    input_box: InputBox,
    width: int,
    height: int,
) -> None:
    """Render chat log and input box."""
    screen.fill((20, 20, 20))
    font = pygame.font.Font(None, 24)
    padding = 10
    line_height = 28
    max_lines = (height - 100) // line_height
    lines_to_show = chat_log[-max_lines:]
    y = padding
    for line in lines_to_show:
        text_surface = font.render(line, True, (230, 230, 230))
        screen.blit(text_surface, (padding, y))
        y += line_height
    input_box.draw(screen)