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
        
        # Enhanced game mechanics
        self.round_scores: Dict[str, int] = {"Terrorists": 0, "Counter-Terrorists": 0}
        self.round_time: int = 120  # 2 minutes per round
        self.bomb_timer: int = 40  # 40 seconds to explode
        self.defuse_time: int = 10  # 10 seconds to defuse
        self.current_positions: Dict[str, Dict[str, str]] = {
            team: {"player": "spawn", "bot": "spawn"} for team in TEAMS
        }
        self.last_action_results: list = []  # Track recent actions for better AI responses

    def reset_round(self) -> None:
        """Reset state for a new round and increment round counter."""
        # Award round win
        if self.winner:
            self.round_scores[self.winner] += 1
            
        for team in TEAMS:
            for member in self.player_health[team]:
                self.player_health[team][member] = 100
                self.current_positions[team][member] = "spawn"
        
        self.bomb_planted = False
        self.bomb_site = None
        self.winner = None
        self.phase = "chat"
        self.round += 1
        self.last_action_results = []

    def is_round_over(self) -> bool:
        """Check if the current round is over based on health or objectives.
        
        Algorithm: Simple iteration over health (O(n) where n=players small).
        Edge case: All dead in one team -> opponent wins; bomb planted -> Terrorists win.
        Returns: True if over, False otherwise.
        """
        # Check if all players in a team are dead
        for team in TEAMS:
            if all(hp <= 0 for hp in self.player_health[team].values()):
                self.winner = TEAMS[1 - TEAMS.index(team)]  # Set winner to opposing team
                return True
        
        # Check if someone already won this round
        if self.winner:
            return True
            
        return False  # Round continues
    
    def is_game_over(self) -> bool:
        """Check if the entire match is over (best of 3)."""
        return (self.round > self.max_rounds or 
                max(self.round_scores.values()) >= (self.max_rounds // 2) + 1)

    def apply_action(self, team: str, entity: str, action: str) -> str:
        """Apply a player's action and simulate outcome.
        
        Algorithm: Parse action string, use if-elif for type, apply randomness (Monte Carlo: random.random() for probabilities).
        - Shoot: 70% hit chance, 30 damage (more exchanges).
        - Plant/Defuse: Team-specific, with defuse 80% success.
        Edge case: Invalid action -> return error string; wrong team for objective -> invalid.
        Returns: Result string for logging.
        """
        # Check if entity is alive
        if self.player_health[team][entity] <= 0:
            result = f"{entity} is dead and cannot act."
            self.last_action_results.append(result)
            return result
            
        # Normalize and parse action
        a = action.lower().strip()
        def matches(key: str) -> bool:
            return any(alias in a for alias in ACTION_ALIASES.get(key, []))

        # Movement action
        if "move to" in a or matches("move"):
            # Extract target position
            position = "unknown"
            for pos in POSITIONS:
                if pos.lower() in a:
                    position = pos
                    break
            self.current_positions[team][entity] = position
            result = f"{entity} moved to {position}."
            self.last_action_results.append(result)
            return result
            
        # Shooting action with specific targeting
        elif "shoot" in a or matches("shoot"):
            target_team = TEAMS[1 - TEAMS.index(team)]
            
            # Try to extract specific target
            target = None
            for potential_target in self.player_health[target_team].keys():
                if potential_target in a:
                    target = potential_target
                    break
            
            # If no specific target, choose random alive target
            if not target:
                alive_targets = [t for t, hp in self.player_health[target_team].items() if hp > 0]
                if not alive_targets:
                    result = f"{entity} has no targets to shoot!"
                    self.last_action_results.append(result)
                    return result
                target = random.choice(alive_targets)
            
            # Check if target is alive
            if self.player_health[target_team][target] <= 0:
                result = f"{entity} cannot shoot {target} - already dead!"
                self.last_action_results.append(result)
                return result
            
            # Hit calculation (70% hit chance)
            if random.random() > 0.3:
                damage = 30  # Reduced damage for more exchanges
                self.player_health[target_team][target] -= damage
                
                # Ensure HP doesn't go below 0
                if self.player_health[target_team][target] < 0:
                    self.player_health[target_team][target] = 0
                
                if self.player_health[target_team][target] <= 0:
                    result = f"{entity} killed {target}! (0 HP)"
                else:
                    hp_left = self.player_health[target_team][target]
                    result = f"{entity} hit {target} for {damage} damage! ({hp_left} HP left)"
            else:
                result = f"{entity} missed {target}."
            
            self.last_action_results.append(result)
            return result
            
        # Bomb planting (Terrorists only)
        elif ("plant bomb" in a or matches("plant bomb")) and team == "Terrorists":
            if self.bomb_planted:
                result = f"{entity}: Bomb is already planted!"
                self.last_action_results.append(result)
                return result
                
            # Extract site if specified
            site = None
            for pos in POSITIONS:
                if pos.lower() in a:
                    site = pos
                    break
            if not site:
                site = random.choice(POSITIONS)
                
            self.bomb_planted = True
            self.bomb_site = site
            result = f"{entity} planted bomb at {site}!"
            self.last_action_results.append(result)
            return result
            
        # Bomb defusing (CT only)
        elif ("defuse bomb" in a or matches("defuse bomb")) and team == "Counter-Terrorists":
            if not self.bomb_planted:
                result = f"{entity}: No bomb to defuse!"
                self.last_action_results.append(result)
                return result
                
            # 80% success rate
            if random.random() > 0.2:
                self.bomb_planted = False
                self.winner = "Counter-Terrorists"
                result = f"{entity} successfully defused the bomb! CT wins!"
            else:
                result = f"{entity} failed to defuse the bomb in time!"
                
            self.last_action_results.append(result)
            return result
        
        # Invalid action fallback
        result = f"Invalid action: {action}"
        self.last_action_results.append(result)
        return result
    
    def get_game_status(self) -> str:
        """Get comprehensive game status for AI context."""
        status = []
        status.append(f"Round {self.round}/{self.max_rounds}")
        status.append(f"Score - T:{self.round_scores['Terrorists']} CT:{self.round_scores['Counter-Terrorists']}")
        
        # Health status
        for team in TEAMS:
            alive = [f"{member}({hp}HP)" for member, hp in self.player_health[team].items() if hp > 0]
            dead = [member for member, hp in self.player_health[team].items() if hp <= 0]
            team_short = "T" if team == "Terrorists" else "CT"
            status.append(f"{team_short}: {', '.join(alive) if alive else 'All dead'}")
            if dead:
                status.append(f"{team_short} Dead: {', '.join(dead)}")
        
        # Bomb status
        if self.bomb_planted:
            status.append(f"💣 BOMB PLANTED at {self.bomb_site}!")
        else:
            status.append("💣 Bomb not planted")
            
        # Recent actions
        if self.last_action_results:
            recent = self.last_action_results[-3:]  # Last 3 actions
            status.append(f"Recent: {' | '.join(recent)}")
        
        return " | ".join(status)
