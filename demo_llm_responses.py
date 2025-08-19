#!/usr/bin/env python3
"""
Demo script showing what LLM responses would look like.
"""
import random
import time

from counter_strike_ag2_agent.game_state import GameState
from counter_strike_ag2_agent.rag import RagTerroristHelper
from counter_strike_ag2_agent.rag_vector import ChromaRAG


def simulate_ag2_response(question, game_state):
    """Simulate what an AG2 LLM response would look like."""
    print(f"🤖 AG2 Agent Processing...")
    print(f"📤 Sending to LLM: '{question}'")
    
    # Simulate API call delay
    time.sleep(random.uniform(1.0, 2.5))
    
    # Build context like the real system does
    game_status = game_state.get_game_status()
    game_facts = RagTerroristHelper.build_facts(game_state)
    
    print(f"📊 Game Context: {game_status}")
    print(f"📋 Game Facts: {' | '.join(game_facts[:2])}...")
    
    # Simulate realistic LLM responses based on question
    if "strategy" in question.lower() or "attack" in question.lower():
        if not game_state.bomb_planted:
            response = "Based on the current round state, I recommend a coordinated A-site execute. Use smokes to block long angles, flash over the wall, and have your entry fragger clear close corners while support trades behind. Plant for default and set up crossfires."
        else:
            response = "With the bomb planted, focus on holding angles and playing for time. Set up crossfires around the bomb site, use utility to delay retakes, and prioritize trading kills over individual plays."
    elif "buy" in question.lower() or "economy" in question.lower():
        response = "Given your current economy, I suggest a force buy with rifles and minimal utility. Focus on taking map control and getting picks to build your economy for the next round."
    elif "utility" in question.lower():
        response = "Coordinate your utility usage: smoke off common angles first, then use flashes to support your entry. Save HE grenades for post-plant situations or to clear common hiding spots."
    else:
        response = "Based on the current game state, focus on gathering information first. Use sound cues and minimal peeking to understand enemy positions, then coordinate a strategic approach to the objective."
    
    print(f"✅ LLM Response: {response}")
    return response


def simulate_smart_response(question, game_state, kb_context):
    """Simulate what a SMART (AG2 + Vector KB) response would look like."""
    print(f"🧠 SMART Agent Processing...")
    print(f"📤 Vector KB Search: '{question}'")
    
    # Simulate vector search
    time.sleep(0.1)
    print(f"📚 KB Context: {kb_context}")
    
    print(f"📤 Sending enhanced context to LLM...")
    
    # Simulate API call delay
    time.sleep(random.uniform(1.5, 3.0))
    
    # Enhanced response using KB context
    if "A-site" in question and "smokes" in kb_context:
        response = f"Based on your knowledge base and current game state: {kb_context}. I recommend executing A-site with a coordinated smoke setup. Throw smokes to block CT spawn and quad angles, then use pop-flashes to support your entry fraggers. The long angles you mentioned are the key - proper smoke placement will neutralize the CT's positional advantage."
    elif "retake" in question.lower():
        response = f"For retaking based on your tactical knowledge: {kb_context}. Use utility to clear common angles first, coordinate your timing with teammates, and focus on trading kills rather than individual plays. The close-range nature of retakes favors coordinated pushes."
    else:
        response = f"Combining your knowledge base insights with current game analysis: {kb_context}. This suggests a methodical approach - use the tactical principles you've stored while adapting to the current round's specific conditions."
    
    print(f"✅ Enhanced LLM Response: {response}")
    return response


def demo_llm_integration():
    """Demo the LLM integration with realistic examples."""
    print("🎮 Counter-Strike AG2 LLM Integration Demo")
    print("=" * 50)
    
    # Setup
    game_state = GameState()
    kb = ChromaRAG()
    
    # Add some tactical knowledge
    kb.add_texts([
        "A-site requires smokes to block long angles and quad",
        "B-site retakes work best with coordinated utility usage",
        "Always trade kills when teammates are engaged"
    ])
    
    print("📚 Added tactical knowledge to vector database")
    print()
    
    # Demo AG2 commands
    print("1️⃣ AG2 Command Demo (Direct LLM Call)")
    print("-" * 30)
    simulate_ag2_response("What's the best strategy to attack A-site?", game_state)
    print()
    
    # Demo SMART commands  
    print("2️⃣ SMART Command Demo (LLM + Vector KB)")
    print("-" * 35)
    kb_result = kb.ask("A-site strategy")
    simulate_smart_response("How should we attack A-site?", game_state, kb_result)
    print()
    
    # Show the difference
    print("🔍 Key Differences:")
    print("   • ag2: Uses only current game state + LLM knowledge")
    print("   • smart: Uses game state + your stored knowledge + LLM")
    print("   • Both make real API calls (1-3 second delays)")
    print("   • Both provide contextual, game-aware responses")


if __name__ == "__main__":
    demo_llm_integration()