"""
Status effects system for the combat engine.
Handles buffs, debuffs, damage-over-time (DoT), crowd control (CC), and defensive barriers.
"""
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional, Dict, Any


class EffectType(str, Enum):
    BLEED = "BLEED"            # Physical DoT (ignores armor)
    BURN = "BURN"              # Magic DoT + reduces defense
    POISON = "POISON"          # Stacking DoT
    STUN = "STUN"              # Cannot take actions this turn
    SHIELD = "SHIELD"          # Absorbs flat damage
    REGEN = "REGEN"            # Heals HP each turn
    ATTACK_BUFF = "ATTACK_BUFF"# Increases outgoing damage %
    DEFENSE_BUFF = "DEFENSE_BUFF" # Reduces incoming damage %
    DODGE_BUFF = "DODGE_BUFF"  # Greatly increases dodge chance


@dataclass
class StatusEffect:
    id: str
    name: str
    effect_type: EffectType
    duration: int               # Turns remaining
    power: float                # Value: DoT damage, shield HP, or percentage buff
    description: str = ""
    source_name: str = ""       # Who applied it

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "effect_type": self.effect_type.value,
            "duration": self.duration,
            "power": self.power,
            "description": self.description,
            "source_name": self.source_name,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "StatusEffect":
        return cls(
            id=data["id"],
            name=data["name"],
            effect_type=EffectType(data["effect_type"]),
            duration=data["duration"],
            power=data["power"],
            description=data.get("description", ""),
            source_name=data.get("source_name", ""),
        )
