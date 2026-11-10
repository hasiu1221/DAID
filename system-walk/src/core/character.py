"""
Character model and archetypes for the combat system.
Manages attributes, resources, active status effects, damage mitigation, and skill usage.
"""
from dataclasses import dataclass, field
from enum import Enum
import copy
import random
from typing import List, Dict, Any, Optional, Tuple

from src.core.status_effects import StatusEffect, EffectType
from src.core.skills import Skill, SKILL_REGISTRY


class CharacterClass(str, Enum):
    WARRIOR = "WARRIOR"
    MAGE = "MAGE"
    ROGUE = "ROGUE"
    PALADIN = "PALADIN"


@dataclass
class Character:
    id: str
    name: str
    char_class: CharacterClass
    max_hp: float
    current_hp: float
    max_stamina: float
    current_stamina: float
    max_mana: float
    current_mana: float
    strength: float
    agility: float
    intelligence: float
    defense: float
    dodge_chance: float = 0.05
    crit_chance: float = 0.05
    crit_multiplier: float = 1.5
    skills: List[Skill] = field(default_factory=list)
    status_effects: List[StatusEffect] = field(default_factory=list)

    @property
    def is_alive(self) -> bool:
        return self.current_hp > 0

    def get_effective_stat(self, stat_name: str) -> float:
        base = getattr(self, stat_name, 0.0)
        # Apply stat buffs/debuffs
        multiplier = 1.0
        for eff in self.status_effects:
            if eff.effect_type == EffectType.ATTACK_BUFF and stat_name in ("strength", "agility", "intelligence"):
                multiplier += eff.power / 100.0
        return max(1.0, base * multiplier)

    def get_effective_dodge(self) -> float:
        dodge = self.dodge_chance + (self.agility * 0.005)
        for eff in self.status_effects:
            if eff.effect_type == EffectType.DODGE_BUFF:
                dodge += eff.power / 100.0
        return min(0.75, max(0.0, dodge))  # Max 75% cap

    def get_effective_defense(self) -> float:
        def_val = self.defense
        for eff in self.status_effects:
            if eff.effect_type == EffectType.DEFENSE_BUFF:
                def_val += eff.power
            elif eff.effect_type == EffectType.BURN:
                def_val = max(0.0, def_val - (eff.power * 0.5))
        return max(0.0, def_val)

    def can_act(self) -> bool:
        if not self.is_alive:
            return False
        return not any(eff.effect_type == EffectType.STUN for eff in self.status_effects)

    def take_damage(self, raw_damage: float, is_magic: bool = False, can_dodge: bool = True) -> Tuple[float, bool, float]:
        """
        Applies incoming damage taking dodge, shields, and defense into account.
        Returns: (actual_hp_damage, was_dodged, damage_absorbed_by_shield)
        """
        if not self.is_alive:
            return (0.0, False, 0.0)

        # Check dodge
        if can_dodge and random.random() < self.get_effective_dodge():
            return (0.0, True, 0.0)

        # Defense mitigation
        effective_def = self.get_effective_defense()
        if is_magic:
            mitigation_pct = min(0.60, effective_def / (effective_def + 100.0))
        else:
            mitigation_pct = min(0.75, effective_def / (effective_def + 75.0))

        dmg_after_armor = max(1.0, raw_damage * (1.0 - mitigation_pct))

        # Check shield effects
        absorbed = 0.0
        remaining_dmg = dmg_after_armor

        for eff in self.status_effects:
            if eff.effect_type == EffectType.SHIELD and eff.power > 0:
                if eff.power >= remaining_dmg:
                    absorbed += remaining_dmg
                    eff.power -= remaining_dmg
                    remaining_dmg = 0.0
                    break
                else:
                    absorbed += eff.power
                    remaining_dmg -= eff.power
                    eff.power = 0.0

        # Remove broken shields
        self.status_effects = [e for e in self.status_effects if not (e.effect_type == EffectType.SHIELD and e.power <= 0)]

        # Apply to HP
        actual_dmg = remaining_dmg
        self.current_hp = max(0.0, self.current_hp - actual_dmg)
        return (round(actual_dmg, 1), False, round(absorbed, 1))

    def heal(self, amount: float) -> float:
        if not self.is_alive:
            return 0.0
        prev_hp = self.current_hp
        self.current_hp = min(self.max_hp, self.current_hp + amount)
        return round(self.current_hp - prev_hp, 1)

    def restore_resources(self, stamina_amount: float = 15.0, mana_amount: float = 10.0):
        if not self.is_alive:
            return
        self.current_stamina = min(self.max_stamina, self.current_stamina + stamina_amount)
        self.current_mana = min(self.max_mana, self.current_mana + mana_amount)

    def apply_status_effect(self, effect: StatusEffect) -> str:
        # Check if already present to refresh duration
        for existing in self.status_effects:
            if existing.id == effect.id:
                existing.duration = max(existing.duration, effect.duration)
                if effect.effect_type == EffectType.SHIELD:
                    existing.power = max(existing.power, effect.power)
                return f"{self.name}'s {effect.name} was refreshed ({existing.duration} turns)!"

        # Copy to avoid shared mutation
        new_eff = copy.deepcopy(effect)
        self.status_effects.append(new_eff)
        return f"{self.name} gained effect: {effect.name} ({effect.duration} turns)!"

    def tick_status_effects(self) -> List[str]:
        """
        Runs at turn start for the character.
        Applies DoT / HoT and decreases duration.
        """
        logs = []
        surviving_effects = []

        for eff in self.status_effects:
            # Apply DoT / HoT
            if eff.effect_type == EffectType.BLEED:
                dmg, _, _ = self.take_damage(eff.power, is_magic=False, can_dodge=False)
                logs.append(f"🩸 {self.name} bleeds for {dmg} damage!")
            elif eff.effect_type == EffectType.BURN:
                dmg, _, _ = self.take_damage(eff.power, is_magic=True, can_dodge=False)
                logs.append(f"🔥 {self.name} burns for {dmg} magic damage!")
            elif eff.effect_type == EffectType.POISON:
                dmg, _, _ = self.take_damage(eff.power, is_magic=True, can_dodge=False)
                logs.append(f"🧪 {self.name} suffers {dmg} poison damage!")
            elif eff.effect_type == EffectType.REGEN:
                healed = self.heal(eff.power)
                logs.append(f"✨ {self.name} regenerates {healed} HP!")

            # Decrease duration
            eff.duration -= 1
            if eff.duration > 0 and (eff.effect_type != EffectType.SHIELD or eff.power > 0):
                surviving_effects.append(eff)
            else:
                logs.append(f"⌛ {self.name}'s {eff.name} effect expired.")

        self.status_effects = surviving_effects

        # Tick skill cooldowns
        for s in self.skills:
            s.tick_cooldown()

        return logs

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "char_class": self.char_class.value,
            "max_hp": self.max_hp,
            "current_hp": round(self.current_hp, 1),
            "max_stamina": self.max_stamina,
            "current_stamina": round(self.current_stamina, 1),
            "max_mana": self.max_mana,
            "current_mana": round(self.current_mana, 1),
            "strength": self.strength,
            "agility": self.agility,
            "intelligence": self.intelligence,
            "defense": self.defense,
            "dodge_chance": self.dodge_chance,
            "crit_chance": self.crit_chance,
            "skills": [s.to_dict() for s in self.skills],
            "status_effects": [e.to_dict() for e in self.status_effects],
            "is_alive": self.is_alive,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Character":
        skills = [Skill.from_dict(s) for s in data.get("skills", [])]
        effects = [StatusEffect.from_dict(e) for e in data.get("status_effects", [])]
        return cls(
            id=data["id"],
            name=data["name"],
            char_class=CharacterClass(data["char_class"]),
            max_hp=data["max_hp"],
            current_hp=data["current_hp"],
            max_stamina=data["max_stamina"],
            current_stamina=data["current_stamina"],
            max_mana=data["max_mana"],
            current_mana=data["current_mana"],
            strength=data["strength"],
            agility=data["agility"],
            intelligence=data["intelligence"],
            defense=data["defense"],
            dodge_chance=data.get("dodge_chance", 0.05),
            crit_chance=data.get("crit_chance", 0.05),
            crit_multiplier=data.get("crit_multiplier", 1.5),
            skills=skills,
            status_effects=effects,
        )


def create_character(char_id: str, name: str, char_class: CharacterClass) -> Character:
    """Factory creating balanced characters for each archetype."""
    if char_class == CharacterClass.WARRIOR:
        skills = [
            copy.deepcopy(SKILL_REGISTRY["basic_attack"]),
            copy.deepcopy(SKILL_REGISTRY["guard"]),
            copy.deepcopy(SKILL_REGISTRY["heavy_slam"]),
            copy.deepcopy(SKILL_REGISTRY["rend"]),
            copy.deepcopy(SKILL_REGISTRY["iron_skin"]),
        ]
        return Character(
            id=char_id,
            name=name,
            char_class=CharacterClass.WARRIOR,
            max_hp=220.0,
            current_hp=220.0,
            max_stamina=120.0,
            current_stamina=120.0,
            max_mana=40.0,
            current_mana=40.0,
            strength=24.0,
            agility=10.0,
            intelligence=8.0,
            defense=22.0,
            dodge_chance=0.05,
            crit_chance=0.08,
            skills=skills,
        )

    elif char_class == CharacterClass.MAGE:
        skills = [
            copy.deepcopy(SKILL_REGISTRY["basic_attack"]),
            copy.deepcopy(SKILL_REGISTRY["guard"]),
            copy.deepcopy(SKILL_REGISTRY["fireball"]),
            copy.deepcopy(SKILL_REGISTRY["arcane_barrier"]),
            copy.deepcopy(SKILL_REGISTRY["chain_lightning"]),
        ]
        return Character(
            id=char_id,
            name=name,
            char_class=CharacterClass.MAGE,
            max_hp=150.0,
            current_hp=150.0,
            max_stamina=60.0,
            current_stamina=60.0,
            max_mana=180.0,
            current_mana=180.0,
            strength=8.0,
            agility=14.0,
            intelligence=28.0,
            defense=10.0,
            dodge_chance=0.08,
            crit_chance=0.15,
            skills=skills,
        )

    elif char_class == CharacterClass.ROGUE:
        skills = [
            copy.deepcopy(SKILL_REGISTRY["basic_attack"]),
            copy.deepcopy(SKILL_REGISTRY["guard"]),
            copy.deepcopy(SKILL_REGISTRY["backstab"]),
            copy.deepcopy(SKILL_REGISTRY["poison_dart"]),
            copy.deepcopy(SKILL_REGISTRY["smoke_bomb"]),
        ]
        return Character(
            id=char_id,
            name=name,
            char_class=CharacterClass.ROGUE,
            max_hp=170.0,
            current_hp=170.0,
            max_stamina=140.0,
            current_stamina=140.0,
            max_mana=50.0,
            current_mana=50.0,
            strength=14.0,
            agility=26.0,
            intelligence=10.0,
            defense=12.0,
            dodge_chance=0.20,
            crit_chance=0.25,
            skills=skills,
        )

    elif char_class == CharacterClass.PALADIN:
        skills = [
            copy.deepcopy(SKILL_REGISTRY["basic_attack"]),
            copy.deepcopy(SKILL_REGISTRY["guard"]),
            copy.deepcopy(SKILL_REGISTRY["smite"]),
            copy.deepcopy(SKILL_REGISTRY["holy_light"]),
            copy.deepcopy(SKILL_REGISTRY["iron_skin"]),
        ]
        return Character(
            id=char_id,
            name=name,
            char_class=CharacterClass.PALADIN,
            max_hp=200.0,
            current_hp=200.0,
            max_stamina=90.0,
            current_stamina=90.0,
            max_mana=110.0,
            current_mana=110.0,
            strength=18.0,
            agility=10.0,
            intelligence=18.0,
            defense=18.0,
            dodge_chance=0.06,
            crit_chance=0.10,
            skills=skills,
        )

    raise ValueError(f"Unknown class: {char_class}")
