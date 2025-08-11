# config.py: Centralized constants for the game
# Follows PEP 8: All caps for constants

TEAMS = ["Terrorists", "Counter-Terrorists"]
POSITIONS = ["A-site", "B-site", "Mid"]
ACTIONS = ["move to <position>", "shoot <target>", "plant bomb", "defuse bomb"]

# Pirate-style aliases for actions (e.g., Captain Jack Sparrow theme)
ACTION_ALIASES = {
    "shoot": [
        "shoot",
        "fire the cannons",
        "open fire",
        "blast",
        "send lead",
    ],
    "plant bomb": [
        "plant bomb",
        "bury the chest",
        "drop the keg",
        "plant the keg",
    ],
    "defuse bomb": [
        "defuse bomb",
        "encounter",
        "cut the fuse",
        "disarm the keg",
        "quench the fuse",
    ],
    "move": [
        "move",
        "sail",
        "weigh anchor",
        "set course",
    ],
}
