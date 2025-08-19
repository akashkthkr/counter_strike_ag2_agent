# agents.py: Sets up AG2 agents and group chats
import os
import json
from autogen import AssistantAgent, UserProxyAgent, GroupChat, GroupChatManager  # type: ignore
from .config import ACTIONS

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
    # xAI (Grok) fallback if XAI_API_KEY is set
    xai_key = os.environ.get("XAI_API_KEY")
    if xai_key:
        return [{
            "model": os.environ.get("XAI_MODEL", "grok-2-latest"),
            "api_key": xai_key,
            "api_type": "openai",
            "base_url": os.environ.get("XAI_BASE_URL", "https://api.x.ai/v1"),
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

def _filter_config_list(cfg_list: list[dict]) -> list[dict]:
    usable: list[dict] = []
    for item in cfg_list or []:
        api_type = str(item.get("api_type", "")).lower()
        if api_type in ("responses", "openai", "oai"):
            usable.append(item)
        elif api_type == "anthropic":
            try:
                __import__("anthropic")
                usable.append(item)
            except (ImportError, ModuleNotFoundError):
                continue
        else:
            # Unknown/unsupported provider; skip
            continue
    return usable

USABLE_CONFIG_LIST = _filter_config_list(CONFIG_LIST)

def get_active_providers() -> list[str]:
    providers: list[str] = []
    for item in USABLE_CONFIG_LIST:
        p = str(item.get("api_type", "")).lower() or "openai"
        if p not in providers:
            providers.append(p)
    return providers

def create_team(team_name: str, is_terrorists: bool) -> GroupChatManager:
    """Create agents and GroupChat for a team.
    
    Algorithm: Setup two agents per team (player, bot), wrap in GroupChat with max_round limit.
    - Terrorists: UserProxy for player (UI integration).
    - Counter-Terrorists: All AssistantAgents (AI-only).
    Bot provides help/insights via system message.
    Returns: GroupChatManager for the team.
    """
    llm_cfg: dict | bool
    if USABLE_CONFIG_LIST:
        # Avoid real client creation in test environments lacking keys
        has_any_key = bool(os.environ.get("OPENAI_API_KEY") or os.environ.get("ANTHROPIC_API_KEY") or os.environ.get("XAI_API_KEY") or os.environ.get("OAI_CONFIG_LIST"))
        contains_inline_keys = any(bool(item.get("api_key")) for item in USABLE_CONFIG_LIST)
        llm_cfg = {"config_list": USABLE_CONFIG_LIST} if (has_any_key or contains_inline_keys) else False
    else:
        llm_cfg = False

    if is_terrorists:
        player = UserProxyAgent(
            name=f"{team_name}_player",
            human_input_mode="NEVER",  # Input handled via UI
            code_execution_config=False,
        )
        bot = AssistantAgent(
            name=f"{team_name}_bot",
            system_message=f"You are a {team_name} bot in CS. Give SHORT, tactical advice in 1-2 sentences max. Suggest specific actions from {ACTIONS}. Be concise and direct.",
            llm_config=llm_cfg,
        )
    else:
        player = AssistantAgent(
            name=f"{team_name}_player",
            system_message=f"You are a {team_name} player. Discuss and act.",
            llm_config=llm_cfg,
        )
        bot = AssistantAgent(
            name=f"{team_name}_bot",
            system_message=f"You are a {team_name} bot. Give SHORT tactical advice in 1-2 sentences max. Be concise and direct.",
            llm_config=llm_cfg,
        )
    group_chat = GroupChat(agents=[player, bot], messages=[], max_round=3)
    return GroupChatManager(groupchat=group_chat, llm_config=(False if not USABLE_CONFIG_LIST else {"config_list": USABLE_CONFIG_LIST}))


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
    llm_cfg: dict | bool
    if USABLE_CONFIG_LIST:
        has_any_key = bool(os.environ.get("OPENAI_API_KEY") or os.environ.get("ANTHROPIC_API_KEY") or os.environ.get("XAI_API_KEY") or os.environ.get("OAI_CONFIG_LIST"))
        contains_inline_keys = any(bool(item.get("api_key")) for item in USABLE_CONFIG_LIST)
        llm_cfg = {"config_list": USABLE_CONFIG_LIST} if (has_any_key or contains_inline_keys) else False
    else:
        llm_cfg = False

    bot = AssistantAgent(
        name="T_bot",
        system_message=f"You are a Terrorists bot in CS. Give SHORT tactical advice in 1-2 sentences max. Suggest specific actions from {ACTIONS}. Be concise and direct.",
        llm_config=llm_cfg,
    )
    agents = [*players, bot]
    group_chat = GroupChat(agents=agents, messages=[], max_round=3)
    manager = GroupChatManager(groupchat=group_chat, llm_config=(False if not USABLE_CONFIG_LIST else {"config_list": USABLE_CONFIG_LIST}))
    return manager, players
