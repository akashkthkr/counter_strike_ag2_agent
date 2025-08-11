# ui.py: Pygame UI components
import pygame

_MOUSEBUTTONDOWN = getattr(pygame, "MOUSEBUTTONDOWN", None)
_KEYDOWN = getattr(pygame, "KEYDOWN", None)
_K_RETURN = getattr(pygame, "K_RETURN", None)
_K_BACKSPACE = getattr(pygame, "K_BACKSPACE", None)
_K_C = getattr(pygame, "K_c", None)
_K_V = getattr(pygame, "K_v", None)
_K_X = getattr(pygame, "K_x", None)
_K_UP = getattr(pygame, "K_UP", None)
_K_DOWN = getattr(pygame, "K_DOWN", None)
_KMOD_CTRL = getattr(pygame, "KMOD_CTRL", 0)
_KMOD_META = getattr(pygame, "KMOD_META", 0)
_SCRAP = getattr(pygame, "scrap", None)
_SCRAP_TEXT = getattr(pygame, "SCRAP_TEXT", None)

class InputBox:
    """Pygame text input box for user messages/actions."""
    
    def __init__(self, x: int, y: int, w: int, h: int, text: str = '', placeholder: str = 'Type a command…') -> None:
        """Initialize input box with position and size."""
        self.rect = pygame.Rect(x, y, w, h)
        self.color = pygame.Color('lightskyblue3')
        self.text: str = text
        self.placeholder: str = placeholder
        self.font = pygame.font.Font(None, 32)
        self.txt_surface = self.font.render(text, True, self.color)
        self.active: bool = False
        self.history: list[str] = []
        self.history_idx: int = 0  # points to len(history) (one past last)

    def handle_event(self, event: pygame.event.Event) -> str | None:
        """Handle mouse/key events for input.
        
        Algorithm: Activate on click, append chars, backspace, return on enter.
        Edge case: Empty text on enter -> return None (ignore).
        Returns: Input text on enter, else None.
        """
        if event.type == _MOUSEBUTTONDOWN:
            self.active = self.rect.collidepoint(event.pos)
        if event.type == _KEYDOWN and self.active:
            mods = pygame.key.get_mods()
            is_cmd = bool(mods & (_KMOD_CTRL | _KMOD_META))
            # Clipboard: copy/cut/paste support
            if is_cmd and _K_V is not None and event.key == _K_V:
                try:
                    clip = None
                    if _SCRAP and _SCRAP_TEXT is not None:
                        try:
                            clip = _SCRAP.get(_SCRAP_TEXT)
                        except Exception:
                            clip = None
                    if clip:
                        try:
                            pasted = clip.decode("utf-8")
                        except Exception:
                            pasted = clip.decode(errors="ignore")
                        self.text += pasted.replace("\r", "").replace("\n", " ")
                        self.txt_surface = self.font.render(self.text, True, self.color)
                        return None
                except Exception:
                    pass
            if is_cmd and _K_C is not None and event.key == _K_C:
                try:
                    if _SCRAP and _SCRAP_TEXT is not None:
                        _SCRAP.put(_SCRAP_TEXT, self.text.encode("utf-8"))
                except Exception:
                    pass
                return None
            if is_cmd and _K_X is not None and event.key == _K_X:
                try:
                    if _SCRAP and _SCRAP_TEXT is not None:
                        _SCRAP.put(_SCRAP_TEXT, self.text.encode("utf-8"))
                except Exception:
                    pass
                self.text = ""
                self.txt_surface = self.font.render(self.text, True, self.color)
                return None
            if _K_RETURN is not None and event.key == _K_RETURN:
                if not self.text:
                    return None
                out = self.text
                # Maintain input history
                if not self.history or self.history[-1] != out:
                    self.history.append(out)
                self.history_idx = len(self.history)
                self.text = ""
                self.txt_surface = self.font.render(self.text, True, self.color)
                return out
            elif _K_BACKSPACE is not None and event.key == _K_BACKSPACE:
                self.text = self.text[:-1]
            elif _K_UP is not None and event.key == _K_UP:
                if self.history:
                    self.history_idx = max(0, self.history_idx - 1)
                    self.text = self.history[self.history_idx]
            elif _K_DOWN is not None and event.key == _K_DOWN:
                if self.history:
                    self.history_idx = min(len(self.history), self.history_idx + 1)
                    self.text = self.history[self.history_idx - 1] if self.history_idx > 0 and self.history_idx <= len(self.history) else ""
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
        if self.text:
            screen.blit(self.txt_surface, (local_rect.x + 5, local_rect.y + 5))
        else:
            # Placeholder when empty
            ph = self.font.render(self.placeholder, True, (130, 130, 130))
            screen.blit(ph, (local_rect.x + 5, local_rect.y + 5))
        pygame.draw.rect(screen, self.color, local_rect, 2)

def render_ui(
    screen: pygame.Surface,
    chat_log: list[str],
    input_box: InputBox,
    width: int,
    height: int,
    scroll_offset_lines: int = 0,
) -> None:
    """Render chat log and input box."""
    screen.fill((20, 20, 20))
    font = pygame.font.Font(None, 24)
    padding = 10
    line_height = 28

    def wrap_text(text: str, max_w: int) -> list[str]:
        if not text:
            return [""]
        words = text.split(" ")
        lines: list[str] = []
        current = ""
        for word in words:
            trial = (current + " " + word).strip()
            if font.size(trial)[0] <= max_w:
                current = trial
            else:
                if current:
                    lines.append(current)
                # Handle very long single words by hard clipping
                if font.size(word)[0] <= max_w:
                    current = word
                else:
                    # break word into chunks
                    chunk = ""
                    for ch in word:
                        if font.size(chunk + ch)[0] <= max_w:
                            chunk += ch
                        else:
                            lines.append(chunk)
                            chunk = ch
                    current = chunk
        if current:
            lines.append(current)
        return lines

    # Flatten all wrapped lines, then select a window based on scroll offset
    all_lines: list[str] = []
    for original in chat_log[-500:]:  # cap work
        all_lines.extend(wrap_text(original, width - 2 * padding))

    max_visible = max(1, (height - 80) // line_height)
    total = len(all_lines)
    # Clamp offset: can't scroll beyond history
    offset = max(0, min(scroll_offset_lines, max(0, total - max_visible)))
    start = max(0, total - max_visible - offset)
    end = start + max_visible
    visible_lines = all_lines[start:end]

    y = padding
    for wrapped in visible_lines:
        text_surface = font.render(wrapped, True, (230, 230, 230))
        screen.blit(text_surface, (padding, y))
        y += line_height

    # Controls hint
    hint = "Scroll: wheel  |  History: ↑/↓  |  Copy/Paste: Cmd/Ctrl+C/V/X"
    hint_surface = font.render(hint, True, (150, 150, 150))
    screen.blit(hint_surface, (padding, height - 60))
    input_box.draw(screen)