"""Constants for the GaggiMate integration."""

DOMAIN = "gaggimate"
DEFAULT_HOST = "gaggimate.local"

# Machine modes from gaggimate firmware constants.h
MODE_STANDBY = 0
MODE_BREW = 1
MODE_STEAM = 2
MODE_WATER = 3
MODE_GRIND = 4

MODE_NAMES = {
    MODE_STANDBY: "Standby",
    MODE_BREW: "Brew",
    MODE_STEAM: "Steam",
    MODE_WATER: "Hot Water",
    MODE_GRIND: "Grind",
}

MODES = list(MODE_NAMES.values())
MODE_BY_NAME = {v: k for k, v in MODE_NAMES.items()}
