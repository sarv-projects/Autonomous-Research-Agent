"""Engine package — research orchestration, modes, agents."""

from .modes import (
    Mode,
    ModeBudgets,
    ModeRegistry,
    QualityDial,
    load_modes,
    get_mode,
)
from . import agents  # noqa: F401  # trigger agent registration

__all__ = [
    "Mode",
    "ModeBudgets",
    "ModeRegistry",
    "QualityDial",
    "load_modes",
    "get_mode",
    "agents",
]
