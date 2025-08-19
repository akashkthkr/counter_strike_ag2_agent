#!/usr/bin/env python3
"""
Test script to verify LLM API calls are working.
"""
import os

from counter_strike_ag2_agent.agents import (create_terrorists_group,
                                             get_active_providers)
from counter_strike_ag2_agent.game_state import GameState
from counter_strike_ag2_agent.rag import RagTerroristHelper


def test_llm_setup():
    """Test if LLM API calls are properly configured."""
    print("🔧 Testing LLM API Configuration...")
    print("=" * 40)
    
    # Check environment variables
    has_openai = bool(os.environ.get('OPENAI_API_KEY'))
    has_anthropic = bool(os.environ.get('ANTHROPIC_API_KEY'))
    has_xai = bool(os.environ.get('XAI_API_KEY'))  # Grok/x.ai
    has_config = bool(os.environ.get('OAI_CONFIG_LIST'))
    
    print(f"🔑 OPENAI_API_KEY: {'✅ Set' if has_openai else '❌ Not set'}")
    print(f"🔑 ANTHROPIC_API_KEY: {'✅ Set' if has_anthropic else '❌ Not set'}")
    print(f"🔑 XAI_API_KEY: {'✅ Set' if has_xai else '❌ Not set'}")
    print(f"🔑 OAI_CONFIG_LIST: {'✅ Set' if has_config else '❌ Not set'}")
    
    if not (has_openai or has_anthropic or has_xai or has_config):
        print("\n⚠️  No API keys configured!")
        print("   Set one of these environment variables:")
        print("   export OPENAI_API_KEY='your-key-here'")
        print("   export ANTHROPIC_API_KEY='your-key-here'")
        print("   export XAI_API_KEY='your-xai-key-here'  # Grok-3 via x.ai")
        return False
    
    # Test agent creation
    try:
        providers = get_active_providers()
        print(f"\n🤖 Active providers: {providers}")
        
        manager, players = create_terrorists_group(num_players=1)
        print(f"✅ Created AG2 agents successfully")
        
        # Find the bot agent
        bot_agent = None
        for agent in manager.groupchat.agents:
            if hasattr(agent, 'system_message') and 'bot' in agent.name.lower():
                bot_agent = agent
                break
        
        if bot_agent:
            print(f"🎯 Found terrorist bot agent: {bot_agent.name}")
            print(f"📝 System message: {bot_agent.system_message[:100]}...")
            
            # Test a simple LLM call
            print(f"\n🚀 Testing LLM API call...")
            
            game_state = GameState()
            game_status = game_state.get_game_status()
            game_facts = RagTerroristHelper.build_facts(game_state)
            
            context = f"Game Status: {game_status}\nDetailed Context: {' '.join(game_facts)}\n\nQuestion: What's a good opening strategy?"
            
            user_message = {"content": context, "role": "user"}
            
            print("📤 Sending request to LLM...")
            response = bot_agent.generate_reply(messages=[user_message], sender=None)
            
            if response:
                print(f"✅ LLM Response received!")
                print(f"📝 Response: {str(response)[:200]}...")
                return True
            else:
                print(f"❌ No response from LLM")
                return False
        else:
            print(f"❌ Could not find bot agent")
            return False
            
    except Exception as e:
        print(f"❌ Error testing LLM: {e}")
        return False


def show_usage_examples():
    """Show examples of LLM-powered commands."""
    print(f"\n🎮 How to Use LLM Commands in Game:")
    print("=" * 35)
    
    print("1️⃣ Start the game:")
    print("   python multi_main.py")
    
    print("\n2️⃣ Use AG2 commands (direct LLM calls):")
    print("   ag2: What's the best strategy for this round?")
    print("   ag2: Should we rush or play slow?")
    print("   ag2: How should we coordinate our attack?")
    
    print("\n3️⃣ Add knowledge for smart commands:")
    print("   kb:add A-site requires utility to clear angles")
    print("   kb:add B-site is better for close engagements")
    
    print("\n4️⃣ Use smart commands (LLM + knowledge base):")
    print("   smart: How to attack A-site effectively?")
    print("   smart: Best retake strategy for current situation?")
    
    print("\n⏱️  Expected response times:")
    print("   • rag: commands = Instant (local)")
    print("   • ask: commands = <100ms (local vector search)")
    print("   • ag2: commands = 1-3 seconds (LLM API call)")
    print("   • smart: commands = 1-3 seconds (vector + LLM)")


if __name__ == "__main__":
    success = test_llm_setup()
    show_usage_examples()
    
    if success:
        print(f"\n🎉 LLM integration is working! Try the ag2: and smart: commands in game.")
    else:
        print(f"\n🔧 Set up your API key first, then try again.")