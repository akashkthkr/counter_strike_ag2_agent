# agents.py: Sets up AG2 agents and group chats
import os
import json

# Prefer ag2; fall back to autogen if ag2 is absent in this venv
try:  # pragma: no cover
    from ag2 import AssistantAgent, UserProxyAgent, GroupChat, GroupChatManager  # type: ignore
except Exception:  # pragma: no cover
    from autogen import AssistantAgent, UserProxyAgent, GroupChat, GroupChatManager  # type: ignore

from .config import ACTIONS  # Import constants

def _load_config_list():
    # Prefer explicit OAI_CONFIG_LIST (file or JSON string)
    cfg = os.environ.get("OAI_CONFIG_LIST")
    if cfg:
        try:
            if os.path.isfile(cfg):
                with open(cfg, "r", encoding="utf-8") as f:
                    return json.load(f)
            return json.loads(cfg)
        except (json.JSONDecodeError, OSError, ValueError):
            pass
    # Anthropic fallback if ANTHROPIC_API_KEY is set
    anth_key = os.environ.get("ANTHROPIC_API_KEY")
    if anth_key:
        return [{
            "model": "claude-3-5-sonnet-20240620",
            "api_key": anth_key,
            "api_type": "anthropic",
            "max_tokens": 1024,
        }]
    # OpenAI fallback if OPENAI_API_KEY is set
    key = os.environ.get("OPENAI_API_KEY")
    if key:
        return [{
            "model": "gpt-5",
            "api_key": key,
            "api_type": "responses",
            "reasoning_effort": "medium",
            "verbosity": "low",
            "allowed_tools": [],
        }]
    return []

CONFIG_LIST = _load_config_list()

def create_team(team_name: str, is_terrorists: bool) -> GroupChatManager:
    """Create agents and GroupChat for a team.
    
    Algorithm: Setup two agents per team (player, bot), wrap in GroupChat with max_round limit.
    - Terrorists: UserProxy for player (UI integration).
    - Counter-Terrorists: All AssistantAgents (AI-only).
    Bot provides help/insights via system message.
    Returns: GroupChatManager for the team.
    """
    if is_terrorists:
        player = UserProxyAgent(
            name=f"{team_name}_player",
            human_input_mode="NEVER",  # Input handled via UI
            code_execution_config=False,
        )
        bot = AssistantAgent(
            name=f"{team_name}_bot",
            system_message=f"You are a {team_name} bot in CS. Provide details, strategies, and help (e.g., when stuck: 'Flank mid to avoid sniper'). Suggest actions like {ACTIONS}.",
            llm_config={"config_list": CONFIG_LIST},
        )
    else:
        player = AssistantAgent(
            name=f"{team_name}_player",
            system_message=f"You are a {team_name} player. Discuss and act.",
            llm_config={"config_list": CONFIG_LIST},
        )
        bot = AssistantAgent(
            name=f"{team_name}_bot",
            system_message=f"You are a {team_name} bot. Provide help and suggest actions.",
            llm_config={"config_list": CONFIG_LIST},
        )
    group_chat = GroupChat(agents=[player, bot], messages=[], max_round=3)
    return GroupChatManager(groupchat=group_chat, llm_config={"config_list": CONFIG_LIST})


def get_user_agent(manager: GroupChatManager):
    for agent in manager.groupchat.agents:
        if isinstance(agent, UserProxyAgent):
            return agent
    return None


def create_terrorists_group(num_players: int) -> tuple[GroupChatManager, list[UserProxyAgent]]:
    if num_players < 1:
        num_players = 1
    players: list[UserProxyAgent] = []
    for idx in range(num_players):
        players.append(
            UserProxyAgent(
                name=f"T_player_{idx+1}",
                human_input_mode="NEVER",
                code_execution_config=False,
            )
        )
    bot = AssistantAgent(
        name="T_bot",
        system_message=f"You are a Terrorists bot in CS. Provide concise strategies and suggest actions like {ACTIONS}.",
        llm_config={"config_list": CONFIG_LIST},
    )
    agents = [*players, bot]
    group_chat = GroupChat(agents=agents, messages=[], max_round=3)
    manager = GroupChatManager(groupchat=group_chat, llm_config={"config_list": CONFIG_LIST})
    return manager, players
