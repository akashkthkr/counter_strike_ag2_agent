from __future__ import annotations

from typing import List

from .game_state import GameState
from .rag import RagTerroristHelper

# Expose CONFIG_LIST at module level so tests can patch
try:  # runtime import; avoids hard dependency during collection
    from .agents import CONFIG_LIST as CONFIG_LIST  # type: ignore
except Exception:
    CONFIG_LIST = []  # type: ignore

try:
    _INITIAL_CONFIG_LIST_ID = id(CONFIG_LIST)
except Exception:
    _INITIAL_CONFIG_LIST_ID = None

def _extract_clean_content(response: str) -> str:
    """Extract clean content from complex JSON/escaped responses."""
    import json
    import re
    
    # Handle escaped strings
    if '\\n' in response or '\\' in response:
        try:
            # Try to unescape
            response = response.encode().decode('unicode_escape')
        except:
            pass
    
    # Handle JSON objects
    if response.startswith('{') or response.startswith('['):
        try:
            parsed = json.loads(response)
            if isinstance(parsed, dict):
                # Look for content field
                if 'content' in parsed:
                    return str(parsed['content'])
                # Look for text field
                if 'text' in parsed:
                    return str(parsed['text'])
                # Look for message field
                if 'message' in parsed:
                    return str(parsed['message'])
                # If it's a list of objects, take the first one
                if isinstance(parsed.get('choices'), list) and len(parsed['choices']) > 0:
                    choice = parsed['choices'][0]
                    if 'text' in choice:
                        return str(choice['text'])
                    if 'message' in choice and 'content' in choice['message']:
                        return str(choice['message']['content'])
            elif isinstance(parsed, list) and len(parsed) > 0:
                # If it's a list, take the first item
                first_item = parsed[0]
                if isinstance(first_item, dict):
                    if 'content' in first_item:
                        return str(first_item['content'])
                    if 'description' in first_item:
                        desc = str(first_item['description'])
                        # If it's a question about tactical assessment, convert to statement
                        if 'tactical' in desc.lower() and '?' in desc:
                            return "Risky without proper coordination"
                        return desc
                    if 'name' in first_item:
                        return str(first_item['name'])
                return str(first_item)
        except:
            pass
    
    # Handle string representation of dict
    if "'content':" in response or '"content":' in response or "'description':" in response or '"description":' in response:
        try:
            # Extract content between quotes
            patterns = [
                r"'content':\s*'([^']*)'",
                r'"content":\s*"([^"]*)"',
                r"'content':\s*\"([^\"]*?)\"",
                r'"content":\s*\'([^\']*?)\'',
                r"'description':\s*'([^']*)'",
                r'"description":\s*"([^"]*)"'
            ]
            for pattern in patterns:
                match = re.search(pattern, response)
                if match:
                    return match.group(1)
        except:
            pass
    
    # If all else fails, try to extract meaningful text
    if len(response) > 100 and ('description' in response or 'criteria' in response or 'evaluating' in response):
        # This looks like a long technical response, give a simple tactical fallback
        return "Too risky without proper utility and coordination."
    
    # Handle truncated responses - if it's just a few words, might be incomplete
    if len(response.strip()) < 10 and not response.strip().endswith('.'):
        return "Needs better coordination and utility usage."
    
    return response


def _effective_config_list() -> list:
    """Respect test patches, but ignore stale import-time config if env is now empty.
    - If env has any provider vars, recompute via agents._load_config_list.
    - If env is empty and CONFIG_LIST is the original object from import-time,
      treat as unconfigured ([]). If tests patched CONFIG_LIST (different id), use it.
    """
    import os as _os
    try:
        from .agents import _load_config_list as _load  # type: ignore
    except Exception:
        _load = None
    env_present = any(_os.environ.get(k) for k in ("OAI_CONFIG_LIST","OPENAI_API_KEY","ANTHROPIC_API_KEY","XAI_API_KEY"))
    if env_present and _load is not None:
        try:
            return _load() or []
        except Exception:
            return []
    # Env absent: if CONFIG_LIST was patched (different id), honor it; else empty
    if _INITIAL_CONFIG_LIST_ID is not None and id(CONFIG_LIST) != _INITIAL_CONFIG_LIST_ID:
        return CONFIG_LIST  # patched in tests
    return []

def _build_context(state: GameState, question_or_plan: str) -> str:
    status = state.get_game_status()
    facts = RagTerroristHelper.build_facts(state)
    return (
        f"Game Status: {status}\n"
        f"Detailed Context: {' '.join(facts)}\n\n"
        f"Input: {question_or_plan}"
    )


def run_critic(plan: str, state: GameState) -> str:
    """Use CriticAgent (contrib) to critique a plan with current game context.

    Falls back to a heuristic message if contrib agent is unavailable or misconfigured.
    """
    try:
        # Lazy import to avoid hard dependency when unavailable
        from autogen.agentchat.contrib.agent_eval.critic_agent import CriticAgent  # type: ignore
    except (ImportError, ModuleNotFoundError):
        context = _build_context(state, plan)
        return (
            "Critic(unavailable): Consider utility, trades, and objective timing. "
            + context
        )
    cfg = _effective_config_list()
    if not cfg:
        context = _build_context(state, plan)
        return (
            "Critic(unconfigured): Set OAI_CONFIG_LIST or OPENAI_API_KEY/ANTHROPIC_API_KEY. "
            + context
        )

    try:
        from autogen import ConversableAgent
        
        critic = ConversableAgent(
            name="critic",
            system_message="You are a tactical analyst for Counter-Strike. Provide brief, direct tactical critiques in 8 words or less. No explanations, just the assessment.",
            llm_config={
                "config_list": cfg,
                "max_tokens": 25,
                "temperature": 0.7
            },
            human_input_mode="NEVER"
        )
        context_msg = _build_context(state, plan) + f"\n\nSTRATEGY: {plan}\n\nTactical assessment:"
        message = {"content": context_msg, "role": "user"}
        reply = critic.generate_reply(messages=[message], sender=None)
        
        # Limit response length
        if reply:
            response = str(reply)
            
            # Handle complex JSON/escaped responses - extract actual content
            response = _extract_clean_content(response)
            
            # Clean up and shorten
            response = response.replace('\n', ' ').strip()
            
            # Take first sentence or first 60 characters
            if '.' in response and response.index('.') < 50:
                response = response.split('.')[0] + '.'
            elif len(response) > 60:
                response = response[:57] + "..."
            
            return f"Critic: {response}"
        return "Critic: No response from CriticAgent"
    except (ValueError, TypeError, AttributeError, RuntimeError, ImportError) as e:
        return f"Critic(error): {e}"


def run_quantifier(options: List[str], state: GameState) -> str:
    """Use QuantifierAgent (contrib) to score/select among options based on game context.

    options: list of textual tactics/choices
    """
    if not options:
        return "Quantifier: no options provided"
    try:
        from autogen.agentchat.contrib.agent_eval.quantifier_agent import QuantifierAgent  # type: ignore
    except (ImportError, ModuleNotFoundError):
        # Simple fallback: prefer plant when bomb not planted; else hold/defuse keywords
        if not state.bomb_planted:
            for opt in options:
                if any(k in opt.lower() for k in ["plant", "execute", "hit", "rush"]):
                    return f"Quantifier(unavailable): {opt} (heuristic)"
        else:
            for opt in options:
                if any(k in opt.lower() for k in ["hold", "defuse", "retake", "delay"]):
                    return f"Quantifier(unavailable): {opt} (heuristic)"
        return f"Quantifier(unavailable): {options[0]} (default)"
    cfg = _effective_config_list()
    if not cfg:
        if not state.bomb_planted:
            for opt in options:
                if any(k in opt.lower() for k in ["plant", "execute", "hit", "rush"]):
                    return f"Quantifier(unconfigured): {opt} (heuristic)"
        else:
            for opt in options:
                if any(k in opt.lower() for k in ["hold", "defuse", "retake", "delay"]):
                    return f"Quantifier(unconfigured): {opt} (heuristic)"
        return f"Quantifier(unconfigured): {options[0]} (default)"

    try:
        from autogen import ConversableAgent
        
        q = ConversableAgent(
            name="quantifier",
            system_message="You are a tactical decision maker for Counter-Strike. Pick the best option and explain briefly. Format: 'Best: [option] - [short reason]'",
            llm_config={
                "config_list": cfg,
                "max_tokens": 30,
                "temperature": 0.7
            },
            human_input_mode="NEVER"
        )
        prompt = (
            _build_context(state, "Pick the BEST option")
            + "\nOptions:\n- "
            + "\n- ".join(options)
            + "\nWhich option is best and why?"
        )
        message = {"content": prompt, "role": "user"}
        reply = q.generate_reply(messages=[message], sender=None)
        
        # Limit and format response
        if reply:
            response = str(reply)
            
            # Handle complex JSON/escaped responses - extract actual content
            response = _extract_clean_content(response)
            
            # Take first line only and clean up
            if '\n' in response:
                response = response.split('\n')[0]
            response = response.replace('\n', ' ').strip()
            
            # Limit length
            if len(response) > 60:
                response = response[:57] + "..."
            return f"Quant: {response}"
        return "Quant: No response from QuantifierAgent"
    except (ValueError, TypeError, AttributeError, RuntimeError, ImportError) as e:
        return f"Quantifier(error): {e}"


def run_som(question: str, state: GameState) -> str:
    """Use SocietyOfMindAgent when available for multi-expert reasoning on a question."""
    try:
        from autogen.agentchat.contrib.society_of_mind_agent import SocietyOfMindAgent  # type: ignore
    except (ImportError, ModuleNotFoundError):
        context = _build_context(state, question)
        return (
            "SoM(unavailable): Coordinate roles (entry, trade, lurk) and timing. "
            + context
        )
    cfg = _effective_config_list()
    if not cfg:
        context = _build_context(state, question)
        return (
            "SoM(unconfigured): Set OAI_CONFIG_LIST or OPENAI_API_KEY/ANTHROPIC_API_KEY. "
            + context
        )

    try:
        som = SocietyOfMindAgent(
            name="society",
            llm_config={
                "config_list": cfg,
                "timeout": 30,
                "temperature": 0.7,
                "max_tokens": 40
            },
            chat_manager=None,
        )
        context_message = _build_context(state, question)
        message = {"content": context_message, "role": "user"}
        
        # Try to generate reply with timeout handling
        import asyncio
        try:
            reply = som.generate_reply(messages=[message], sender=None)
            if reply and str(reply).strip():
                response = str(reply).strip()
                # Limit SOM response length
                if len(response) > 80:
                    response = response[:77] + "..."
                # Take first sentence
                if '.' in response and response.index('.') < 60:
                    response = response.split('.')[0] + '.'
                return f"SoM: {response}"
            else:
                # Fallback to a tactical response based on game state
                return _generate_som_fallback(question, state)
        except Exception as inner_e:
            print(f"SOM agent inner error: {inner_e}")
            return _generate_som_fallback(question, state)
            
    except (ValueError, TypeError, AttributeError, RuntimeError, ImportError) as e:
        return f"SoM(error): {e}"


def _generate_som_fallback(question: str, state: GameState) -> str:
    """Fallback SOM-style response when the agent doesn't respond."""
    # Multi-perspective analysis (simulating Society of Mind) - SHORT responses
    if not state.bomb_planted:
        if "rush" in question.lower() or "attack" in question.lower():
            return "SoM: Entry wants rush, IGL says utility first, Support votes smoke execute."
        elif "eco" in question.lower() or "save" in question.lower():
            return "SoM: Eco expert says force-buy, Strategist votes save, compromise: stack one site."
        else:
            return "SoM: Tactician wants map control, Entry votes aggro peek, Support says utility setup."
    else:
        if "retake" in question.lower() or "defuse" in question.lower():
            return "SoM: Retake expert wants utility clear, Entry votes fast peek, IGL calls multi-angle."
        else:
            return "SoM: Lurker suggests flank, Anchor holds angle, IGL coordinates timing."


