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
        if state.bomb_planted:
            facts.append(f"Bomb is planted at {state.bomb_site}.")
        else:
            facts.append("Bomb is not planted.")
        # Health snapshot
        for team, members in state.player_health.items():
            alive = [m for m, hp in members.items() if hp > 0]
            facts.append(f"{team} alive: {', '.join(alive) if alive else 'none'}.")
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
            return "After plant, set a crossfire and play for time; avoid dry peeks."

        # Default: surface current facts as fallback
        return "Facts: " + " ".join(facts)


