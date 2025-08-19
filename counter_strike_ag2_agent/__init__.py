try:
    from dotenv import load_dotenv  # type: ignore
    load_dotenv()
except Exception:
    pass

__all__ = [
    "config",
    "game_state",
    "agents",
    "ui",
]
