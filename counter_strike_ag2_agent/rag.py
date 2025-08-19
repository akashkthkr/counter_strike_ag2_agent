from __future__ import annotations

from typing import List

from .game_state import GameState


class RagTerroristHelper:
    """Very lightweight RAG-like helper that answers questions based on current game facts.

    This is intentionally simple: builds a small fact list from the GameState and
    returns answers using keyword heuristics. No external dependencies.
    """

    @staticmethod
    def build_facts(state: GameState) -> List[str]:
        facts: List[str] = []
        
        # Round and score info
        facts.append(f"Round {state.round}/{state.max_rounds}")
        t_score = state.round_scores.get("Terrorists", 0)
        ct_score = state.round_scores.get("Counter-Terrorists", 0)
        facts.append(f"Score: T-{t_score} CT-{ct_score}")
        
        # Bomb status
        if state.bomb_planted:
            facts.append(f"💣 BOMB PLANTED at {state.bomb_site}!")
        else:
            facts.append("💣 Bomb not planted.")
            
        # Detailed health status
        for team, members in state.player_health.items():
            alive = [f"{m}({hp}HP)" for m, hp in members.items() if hp > 0]
            dead = [m for m, hp in members.items() if hp <= 0]
            team_short = "T" if team == "Terrorists" else "CT"
            
            if alive:
                facts.append(f"{team_short} alive: {', '.join(alive)}")
            if dead:
                facts.append(f"{team_short} dead: {', '.join(dead)}")
                
        # Recent actions context
        if hasattr(state, 'last_action_results') and state.last_action_results:
            recent = state.last_action_results[-2:]  # Last 2 actions for context
            facts.append(f"Recent actions: {' | '.join(recent)}")
            
        return facts

    @staticmethod
    def answer(question: str, state: GameState) -> str:
        q = question.lower()
        facts = RagTerroristHelper.build_facts(state)

        # Bomb site questions
        if "bomb" in q and ("site" in q or "where" in q or "plant" in q):
            if state.bomb_planted and state.bomb_site:
                return f"Bomb planted at {state.bomb_site}."
            return "Bomb is not planted yet. Consider planting at A-site or B-site."

        # CT proximity or threat intuition
        if any(k in q for k in ["ct", "counter", "enemy", "threat", "near", "close"]):
            ct_alive = sum(1 for hp in state.player_health.get("Counter-Terrorists", {}).values() if hp > 0)
            if ct_alive == 0:
                return "No CTs alive. Safe to execute objective."
            if state.bomb_planted:
                return "CTs likely converging on bomb site. Hold angles and trade."
            return "CT presence unknown. Clear corners and use utility before entry."

        # Upgrade/suggestion
        if any(k in q for k in ["upgrade", "suggest", "tip", "strategy", "what should we do"]):
            if not state.bomb_planted:
                return "Group up and execute a fast hit: smoke entry, flash CT, then plant."
            site = state.bomb_site or "site"
            return f"After plant at {site}, set a crossfire and play for time; avoid dry peeks."

        # Default: surface current facts as fallback
        return "Facts: " + " ".join(facts)

    @staticmethod
    def build_facts_from_context(context: dict) -> List[str]:
        """Build facts from a context dictionary (used in Celery tasks)."""
        facts: List[str] = []
        
        # Round and score info
        round_num = context.get("round", 1)
        facts.append(f"Round {round_num}")
        
        # Bomb status
        if context.get("bomb_planted"):
            bomb_site = context.get("bomb_site", "unknown")
            facts.append(f"💣 BOMB PLANTED at {bomb_site}!")
        else:
            facts.append("💣 Bomb not planted.")
            
        # Health status from context
        player_health = context.get("player_health", {})
        for team, members in player_health.items():
            alive = [f"{m}({hp}HP)" for m, hp in members.items() if hp > 0]
            dead = [m for m, hp in members.items() if hp <= 0]
            team_short = "T" if team == "Terrorists" else "CT"
            
            if alive:
                facts.append(f"{team_short} alive: {', '.join(alive)}")
            if dead:
                facts.append(f"{team_short} dead: {', '.join(dead)}")
                
        return facts


