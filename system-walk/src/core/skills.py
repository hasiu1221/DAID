"""
Skills and Abilities definition for Combat System.
Includes physical attacks, spells, healing, defensive skills, and tactical abilities.
"""
from dataclasses import dataclass
from enum import Enum
from typing import Optional, Dict, Any, List
from src.core.status_effects import StatusEffect, EffectType


class SkillType(str, Enum):
    PHYSICAL = "PHYSICAL"
    MAGICAL = "MAGICAL"
    HEAL = "HEAL"
    BUFF = "BUFF"
    DEBUFF = "DEBUFF"


class SkillTarget(str, Enum):
    ENEMY = "ENEMY"
    SELF = "SELF"
    ALLY = "ALLY"


@dataclass
class Skill:
    id: str
    name: str
    skill_type: SkillType
    target_type: SkillTarget
    stamina_cost: int
    mana_cost: int
    cooldown: int                     # Max cooldown turns
    current_cooldown: int = 0
    base_value: float = 0.0           # Base damage or healing
    scaling_stat: str = "strength"     # "strength", "agility", "intelligence"
    scaling_factor: float = 1.0       # Multiplier for attribute
    crit_bonus: float = 0.0           # Extra crit chance (0.0 - 1.0)
    applies_effect: Optional[StatusEffect] = None
    effect_chance: float = 1.0        # Probability to apply effect
    description: str = ""

    def is_ready(self) -> bool:
        return self.current_cooldown <= 0

    def start_cooldown(self):
        self.current_cooldown = self.cooldown

    def tick_cooldown(self):
        if self.current_cooldown > 0:
            self.current_cooldown -= 1

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "skill_type": self.skill_type.value,
            "target_type": self.target_type.value,
            "stamina_cost": self.stamina_cost,
            "mana_cost": self.mana_cost,
            "cooldown": self.cooldown,
            "current_cooldown": self.current_cooldown,
            "base_value": self.base_value,
            "scaling_stat": self.scaling_stat,
            "scaling_factor": self.scaling_factor,
            "crit_bonus": self.crit_bonus,
            "applies_effect": self.applies_effect.to_dict() if self.applies_effect else None,
            "effect_chance": self.effect_chance,
            "description": self.description,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Skill":
        effect = None
        if data.get("applies_effect"):
            effect = StatusEffect.from_dict(data["applies_effect"])
        return cls(
            id=data["id"],
            name=data["name"],
            skill_type=SkillType(data["skill_type"]),
            target_type=SkillTarget(data["target_type"]),
            stamina_cost=data["stamina_cost"],
            mana_cost=data["mana_cost"],
            cooldown=data["cooldown"],
            current_cooldown=data.get("current_cooldown", 0),
            base_value=data["base_value"],
            scaling_stat=data["scaling_stat"],
            scaling_factor=data["scaling_factor"],
            crit_bonus=data.get("crit_bonus", 0.0),
            applies_effect=effect,
            effect_chance=data.get("effect_chance", 1.0),
            description=data.get("description", ""),
        )


# =========================================================================
# Preset Skills Registry
# =========================================================================

SKILL_REGISTRY: Dict[str, Skill] = {
    # Generic
    "basic_attack": Skill(
        id="basic_attack",
        name="Basic Attack",
        skill_type=SkillType.PHYSICAL,
        target_type=SkillTarget.ENEMY,
        stamina_cost=10,
        mana_cost=0,
        cooldown=0,
        base_value=15.0,
        scaling_stat="strength",
        scaling_factor=0.8,
        description="A standard weapon swing.",
    ),
    "guard": Skill(
        id="guard",
        name="Defensive Guard",
        skill_type=SkillType.BUFF,
        target_type=SkillTarget.SELF,
        stamina_cost=15,
        mana_cost=0,
        cooldown=2,
        base_value=0.0,
        scaling_stat="strength",
        scaling_factor=0.0,
        applies_effect=StatusEffect(
            id="guard_effect",
            name="Guarding",
            effect_type=EffectType.DEFENSE_BUFF,
            duration=1,
            power=50.0,  # 50% damage reduction
            description="Reduces incoming damage by 50% for 1 turn.",
        ),
        description="Brace for impact, halving incoming damage next turn.",
    ),

    # Warrior Skills
    "heavy_slam": Skill(
        id="heavy_slam",
        name="Heavy Slam",
        skill_type=SkillType.PHYSICAL,
        target_type=SkillTarget.ENEMY,
        stamina_cost=30,
        mana_cost=0,
        cooldown=2,
        base_value=35.0,
        scaling_stat="strength",
        scaling_factor=1.4,
        applies_effect=StatusEffect(
            id="stun_effect",
            name="Stunned",
            effect_type=EffectType.STUN,
            duration=1,
            power=1.0,
            description="Cannot act for 1 turn.",
        ),
        effect_chance=0.4,
        description="A crushing blow with 40% chance to stun the target.",
    ),
    "rend": Skill(
        id="rend",
        name="Rend",
        skill_type=SkillType.PHYSICAL,
        target_type=SkillTarget.ENEMY,
        stamina_cost=20,
        mana_cost=0,
        cooldown=3,
        base_value=20.0,
        scaling_stat="strength",
        scaling_factor=1.0,
        applies_effect=StatusEffect(
            id="bleed_effect",
            name="Bleeding",
            effect_type=EffectType.BLEED,
            duration=3,
            power=12.0,  # 12 dmg per turn
            description="Suffering 12 physical damage each turn.",
        ),
        effect_chance=1.0,
        description="Causes deep wounds, making the enemy bleed for 3 turns.",
    ),
    "iron_skin": Skill(
        id="iron_skin",
        name="Iron Skin",
        skill_type=SkillType.BUFF,
        target_type=SkillTarget.SELF,
        stamina_cost=25,
        mana_cost=0,
        cooldown=4,
        base_value=0.0,
        scaling_stat="strength",
        scaling_factor=0.0,
        applies_effect=StatusEffect(
            id="iron_skin_shield",
            name="Iron Barrier",
            effect_type=EffectType.SHIELD,
            duration=3,
            power=60.0,
            description="Absorbs up to 60 damage.",
        ),
        description="Harden your body, absorbing up to 60 damage.",
    ),

    # Mage Skills
    "fireball": Skill(
        id="fireball",
        name="Fireball",
        skill_type=SkillType.MAGICAL,
        target_type=SkillTarget.ENEMY,
        stamina_cost=5,
        mana_cost=30,
        cooldown=1,
        base_value=40.0,
        scaling_stat="intelligence",
        scaling_factor=1.5,
        applies_effect=StatusEffect(
            id="burn_effect",
            name="Burning",
            effect_type=EffectType.BURN,
            duration=3,
            power=14.0,
            description="Suffering 14 magical burn damage each turn.",
        ),
        effect_chance=0.7,
        description="Hurl a ball of fire, dealing heavy magic damage and burning.",
    ),
    "arcane_barrier": Skill(
        id="arcane_barrier",
        name="Arcane Barrier",
        skill_type=SkillType.BUFF,
        target_type=SkillTarget.SELF,
        stamina_cost=0,
        mana_cost=35,
        cooldown=4,
        base_value=0.0,
        scaling_stat="intelligence",
        scaling_factor=0.5,
        applies_effect=StatusEffect(
            id="arcane_shield",
            name="Arcane Shield",
            effect_type=EffectType.SHIELD,
            duration=3,
            power=80.0,
            description="Absorbs 80 damage.",
        ),
        description="Summons an ethereal ward absorbing up to 80 damage.",
    ),
    "chain_lightning": Skill(
        id="chain_lightning",
        name="Chain Lightning",
        skill_type=SkillType.MAGICAL,
        target_type=SkillTarget.ENEMY,
        stamina_cost=5,
        mana_cost=45,
        cooldown=3,
        base_value=55.0,
        scaling_stat="intelligence",
        scaling_factor=1.6,
        crit_bonus=0.25,
        description="Electrifying bolt with high critical strike chance.",
    ),

    # Rogue Skills
    "backstab": Skill(
        id="backstab",
        name="Shadow Strike",
        skill_type=SkillType.PHYSICAL,
        target_type=SkillTarget.ENEMY,
        stamina_cost=35,
        mana_cost=0,
        cooldown=2,
        base_value=32.0,
        scaling_stat="agility",
        scaling_factor=1.6,
        crit_bonus=0.35,
        description="A stealth attack with lethal precision (+35% crit chance).",
    ),
    "poison_dart": Skill(
        id="poison_dart",
        name="Poison Dart",
        skill_type=SkillType.PHYSICAL,
        target_type=SkillTarget.ENEMY,
        stamina_cost=15,
        mana_cost=10,
        cooldown=1,
        base_value=15.0,
        scaling_stat="agility",
        scaling_factor=0.9,
        applies_effect=StatusEffect(
            id="poison_effect",
            name="Poisoned",
            effect_type=EffectType.POISON,
            duration=4,
            power=10.0,
            description="Suffering 10 poison damage each turn.",
        ),
        effect_chance=1.0,
        description="Shoots an envenomed needle dealing lasting poison damage.",
    ),
    "smoke_bomb": Skill(
        id="smoke_bomb",
        name="Smoke Bomb",
        skill_type=SkillType.BUFF,
        target_type=SkillTarget.SELF,
        stamina_cost=25,
        mana_cost=10,
        cooldown=4,
        base_value=0.0,
        scaling_stat="agility",
        scaling_factor=0.0,
        applies_effect=StatusEffect(
            id="smoke_dodge",
            name="Evasion",
            effect_type=EffectType.DODGE_BUFF,
            duration=2,
            power=60.0,  # +60% dodge chance
            description="Increases dodge chance by 60%.",
        ),
        description="Vanish into smoke, heavily boosting evasion for 2 turns.",
    ),

    # Paladin / Cleric Skills
    "holy_light": Skill(
        id="holy_light",
        name="Holy Light",
        skill_type=SkillType.HEAL,
        target_type=SkillTarget.SELF,
        stamina_cost=10,
        mana_cost=35,
        cooldown=3,
        base_value=45.0,
        scaling_stat="intelligence",
        scaling_factor=1.2,
        applies_effect=StatusEffect(
            id="holy_regen",
            name="Blessed Regen",
            effect_type=EffectType.REGEN,
            duration=2,
            power=15.0,
            description="Regenerates 15 HP each turn.",
        ),
        description="Restore direct HP and gain health regeneration for 2 turns.",
    ),
    "smite": Skill(
        id="smite",
        name="Holy Smite",
        skill_type=SkillType.MAGICAL,
        target_type=SkillTarget.ENEMY,
        stamina_cost=20,
        mana_cost=25,
        cooldown=2,
        base_value=30.0,
        scaling_stat="strength",
        scaling_factor=1.1,
        description="Strikes the foe with divine righteous fury.",
    ),
}
