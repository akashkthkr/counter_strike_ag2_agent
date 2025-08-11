# game_state.py: Handles game logic and state machine
import random  # For Monte Carlo-like randomness in actions
from typing import Dict, Optional  # For type hints

from .config import TEAMS, POSITIONS, ACTION_ALIASES  # Import constants

class GameState:
    """Manages the game state, including rounds, health, objectives, and phases."""
    
    def __init__(self) -> None:
        """Initialize game state with defaults."""
        self.round: int = 1  # Current round number
        self.max_rounds: int = 3  # Maximum rounds before game ends
        self.player_health: Dict[str, Dict[str, int]] = {
            team: {"player": 100, "bot": 100} for team in TEAMS
        }  # Health dict: team -> entity -> hp
        self.bomb_planted: bool = False  # Objective flag
        self.bomb_site: Optional[str] = None  # Plant location
        self.winner: Optional[str] = None  # Round winner
        self.phase: str = "chat"  # State machine phase: 'chat', 'action', 'resolve'

    def reset_round(self) -> None:
        """Reset state for a new round and increment round counter."""
        for team in TEAMS:
            for member in self.player_health[team]:
                self.player_health[team][member] = 100
        self.bomb_planted = False
        self.bomb_site = None
        self.winner = None
        self.phase = "chat"
        self.round += 1

    def is_round_over(self) -> bool:
        """Check if the current round is over based on health or objectives.
        
        Algorithm: Simple iteration over health (O(n) where n=players small).
        Edge case: All dead in one team -> opponent wins; bomb planted -> Terrorists win.
        Returns: True if over, False otherwise.
        """
        for team in TEAMS:
            if all(hp <= 0 for hp in self.player_health[team].values()):
                self.winner = TEAMS[1 - TEAMS.index(team)]  # Set winner to opposing team
                return True
        if self.bomb_planted:  # Simplified: No defuse check here; handled in apply_action
            self.winner = "Terrorists"
            return True
        return self.round > self.max_rounds  # Game-level end

    def apply_action(self, team: str, entity: str, action: str) -> str:
        """Apply a player's action and simulate outcome.
        
        Algorithm: Parse action string, use if-elif for type, apply randomness (Monte Carlo: random.random() for probabilities).
        - Shoot: 70% hit chance, 50 damage.
        - Plant/Defuse: Team-specific, with defuse 80% success.
        Edge case: Invalid action -> return error string; wrong team for objective -> invalid.
        Returns: Result string for logging.
        """
        # Normalize pirate-style aliases
        a = action.lower()
        def matches(key: str) -> bool:
            return any(alias in a for alias in ACTION_ALIASES.get(key, []))

        if "move to" in a or matches("move"):
            return f"{entity} moved."  # Placeholder; no position tracking yet
        elif "shoot" in a or matches("shoot"):
            target_team = TEAMS[1 - TEAMS.index(team)]
            target = random.choice(list(self.player_health[target_team].keys()))  # Random target selection
            if random.random() > 0.3:  # 70% hit probability
                self.player_health[target_team][target] -= 50  # Apply damage
                if self.player_health[target_team][target] <= 0:
                    return f"{entity} killed {target}!"
                return f"{entity} hit {target}."
            return f"{entity} missed."
        elif ("plant bomb" in a or matches("plant bomb")) and team == "Terrorists" and not self.bomb_planted:
            self.bomb_planted = True
            self.bomb_site = random.choice(POSITIONS)
            return f"{entity} planted bomb at {self.bomb_site}."
        elif ("defuse bomb" in a or matches("defuse bomb")) and team == "Counter-Terrorists" and self.bomb_planted:
            if random.random() > 0.2:  # 80% success probability
                self.bomb_planted = False
                self.winner = "Counter-Terrorists"
                return f"{entity} defused bomb!"
            return f"{entity} failed to defuse."
        return "Invalid action."  # Fallback for parsing errors
