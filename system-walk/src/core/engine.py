"""
Core combat engine orchestrating turns, action resolution, damage calculation,
initiative ordering, win conditions, and combat logging.
"""
from enum import Enum
import random
import time
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass

from src.core.character import Character
from src.core.skills import SkillType, SkillTarget
from src.core.status_effects import EffectType


class BattleState(str, Enum):
    WAITING = "WAITING"
    ACTIVE = "ACTIVE"
    FINISHED = "FINISHED"


@dataclass
class TurnAction:
    actor_id: str
    skill_id: str
    target_id: str


@dataclass
class ActionResult:
    success: bool
    message: str
    actor_id: str
    target_id: Optional[str] = None
    skill_name: Optional[str] = None
    damage_dealt: float = 0.0
    healing_done: float = 0.0
    is_crit: bool = False
    is_dodged: bool = False
    shield_absorbed: float = 0.0
    status_applied: Optional[str] = None
    battle_ended: bool = False
    winner_team: Optional[str] = None


class CombatEngine:
    def __init__(self, battle_id: str, turn_timeout: int = 30):
        self.battle_id = battle_id
        self.turn_timeout = turn_timeout
        self.state = BattleState.WAITING
        self.teams: Dict[str, List[Character]] = {}   # team_id -> list of characters
        self.char_map: Dict[str, Character] = {}      # char_id -> Character
        self.char_team: Dict[str, str] = {}           # char_id -> team_id
        self.turn_order: List[str] = []               # list of char_ids in turn sequence
        self.current_turn_idx: int = 0
        self.round_number: int = 1
        self.turn_start_time: float = 0.0
        self.battle_log: List[str] = []
        self.winner_team: Optional[str] = None

    def add_character(self, character: Character, team_id: str):
        if self.state != BattleState.WAITING:
            raise ValueError("Cannot add combatants to an ongoing battle.")
        if team_id not in self.teams:
            self.teams[team_id] = []
        self.teams[team_id].append(character)
        self.char_map[character.id] = character
        self.char_team[character.id] = team_id

    def start_battle(self) -> List[str]:
        if len(self.teams) < 2:
            raise ValueError("At least 2 teams required to start battle.")
        
        self.state = BattleState.ACTIVE
        self.turn_start_time = time.time()
        self.round_number = 1
        self._calculate_turn_order()
        
        start_logs = [f"⚔️ Battle {self.battle_id} begins! Round {self.round_number}."]
        self.battle_log.extend(start_logs)

        # Apply start-of-turn ticks for the first character
        curr = self.get_active_character()
        if curr:
            curr_logs = self._on_turn_start(curr)
            start_logs.extend(curr_logs)

        return start_logs

    def _calculate_turn_order(self):
        # Order characters by agility + slight random roll for initiative
        living = [c for c in self.char_map.values() if c.is_alive]
        sorted_chars = sorted(
            living,
            key=lambda c: c.get_effective_stat("agility") + random.uniform(0, 5),
            reverse=True,
        )
        self.turn_order = [c.id for c in sorted_chars]
        self.current_turn_idx = 0

    def get_active_character(self) -> Optional[Character]:
        if not self.turn_order or self.state != BattleState.ACTIVE:
            return None
        char_id = self.turn_order[self.current_turn_idx]
        return self.char_map.get(char_id)

    def _on_turn_start(self, character: Character) -> List[str]:
        logs = []
        logs.append(f"▶️ It is now {character.name}'s turn ({character.char_class.value}).")
        
        # Restore small resources each turn
        character.restore_resources(stamina_amount=15.0, mana_amount=10.0)

        # Process status effects (DoT / Buff durations)
        effect_logs = character.tick_status_effects()
        logs.extend(effect_logs)
        self.battle_log.extend(effect_logs)

        # Check if DoT killed character
        if not character.is_alive:
            death_msg = f"💀 {character.name} has fallen to status effects!"
            logs.append(death_msg)
            self.battle_log.append(death_msg)
            if self._check_battle_end():
                return logs
            # Automatically advance
            next_logs = self._advance_turn()
            logs.extend(next_logs)
            return logs

        # Check if stunned
        if not character.can_act():
            stun_msg = f"💫 {character.name} is STUNNED and cannot act this turn!"
            logs.append(stun_msg)
            self.battle_log.append(stun_msg)
            next_logs = self._advance_turn()
            logs.extend(next_logs)

        return logs

    def execute_action(self, actor_id: str, skill_id: str, target_id: str) -> ActionResult:
        if self.state != BattleState.ACTIVE:
            return ActionResult(False, "Battle is not active.", actor_id)

        actor = self.get_active_character()
        if not actor or actor.id != actor_id:
            return ActionResult(False, "It is not this character's turn.", actor_id)

        if not actor.can_act():
            return ActionResult(False, "Character cannot act (stunned).", actor_id)

        # Find skill
        skill = next((s for s in actor.skills if s.id == skill_id), None)
        if not skill:
            return ActionResult(False, f"Skill '{skill_id}' not found on actor.", actor_id)

        if not skill.is_ready():
            return ActionResult(False, f"Skill '{skill.name}' is on cooldown ({skill.current_cooldown} turns left).", actor_id)

        if actor.current_stamina < skill.stamina_cost:
            return ActionResult(False, f"Not enough stamina ({actor.current_stamina:.0f}/{skill.stamina_cost}).", actor_id)

        if actor.current_mana < skill.mana_cost:
            return ActionResult(False, f"Not enough mana ({actor.current_mana:.0f}/{skill.mana_cost}).", actor_id)

        target = self.char_map.get(target_id)
        if not target or not target.is_alive:
            return ActionResult(False, "Invalid or dead target.", actor_id)

        actor_team = self.char_team[actor_id]
        target_team = self.char_team[target_id]

        if skill.target_type == SkillTarget.ENEMY and actor_team == target_team:
            return ActionResult(False, "Cannot target an ally with this offensive skill.", actor_id)

        if skill.target_type in (SkillTarget.SELF, SkillTarget.ALLY) and actor_team != target_team:
            return ActionResult(False, "Cannot target an enemy with this beneficial skill.", actor_id)

        # Deduct costs
        actor.current_stamina -= skill.stamina_cost
        actor.current_mana -= skill.mana_cost
        skill.start_cooldown()

        # Resolve skill effect
        result = self._resolve_skill(actor, skill, target)
        self.battle_log.append(result.message)

        # Check win/loss
        if self._check_battle_end():
            result.battle_ended = True
            result.winner_team = self.winner_team
            return result

        # Advance turn
        turn_logs = self._advance_turn()
        self.battle_log.extend(turn_logs)

        return result

    def pass_turn(self, character_id: str) -> ActionResult:
        """Allows a character to pass/rest their turn, recovering resources."""
        if self.state != BattleState.ACTIVE:
            return ActionResult(False, "Battle is not active.", character_id)

        actor = self.get_active_character()
        if not actor or actor.id != character_id:
            return ActionResult(False, "It is not this character's turn.", character_id)

        # Recover extra stamina when passing
        actor.current_stamina = min(actor.max_stamina, actor.current_stamina + 20.0)
        actor.current_mana = min(actor.max_mana, actor.current_mana + 10.0)

        msg = f"🛡️ {actor.name} zbiera siły i odpoczywa w tej turze (+20 Staminy, +10 Many)."
        self.battle_log.append(msg)

        turn_logs = self._advance_turn()
        self.battle_log.extend(turn_logs)

        return ActionResult(
            success=True,
            message=msg,
            actor_id=actor.id,
        )

    def _resolve_skill(self, actor: Character, skill, target: Character) -> ActionResult:
        # Damage / Healing calculation
        stat_val = actor.get_effective_stat(skill.scaling_stat)
        scaled_power = skill.base_value + (stat_val * skill.scaling_factor)

        # Critical hit roll
        crit_chance = actor.crit_chance + skill.crit_bonus
        is_crit = random.random() < crit_chance
        multiplier = actor.crit_multiplier if is_crit else 1.0

        total_value = scaled_power * multiplier

        if skill.skill_type in (SkillType.PHYSICAL, SkillType.MAGICAL):
            is_magic = skill.skill_type == SkillType.MAGICAL
            dmg, dodged, absorbed = target.take_damage(total_value, is_magic=is_magic, can_dodge=True)

            crit_tag = "💥 CRITICAL HIT! " if is_crit else ""
            if dodged:
                msg = f"💨 {actor.name} used {skill.name} on {target.name}, but {target.name} DODGED!"
                return ActionResult(
                    success=True,
                    message=msg,
                    actor_id=actor.id,
                    target_id=target.id,
                    skill_name=skill.name,
                    is_dodged=True,
                )
            
            shield_msg = f" (🛡️ {absorbed:.1f} absorbed)" if absorbed > 0 else ""
            msg = f"{crit_tag}⚔️ {actor.name} used {skill.name} on {target.name} dealing {dmg:.1f} damage!{shield_msg}"

            status_applied_name = None
            if skill.applies_effect and random.random() < skill.effect_chance and target.is_alive:
                eff_msg = target.apply_status_effect(skill.applies_effect)
                msg += f" {eff_msg}"
                status_applied_name = skill.applies_effect.name

            if not target.is_alive:
                msg += f" 💀 {target.name} has been defeated!"

            return ActionResult(
                success=True,
                message=msg,
                actor_id=actor.id,
                target_id=target.id,
                skill_name=skill.name,
                damage_dealt=dmg,
                is_crit=is_crit,
                shield_absorbed=absorbed,
                status_applied=status_applied_name,
            )

        elif skill.skill_type == SkillType.HEAL:
            healed = target.heal(total_value)
            crit_tag = "✨ CRITICAL HEAL! " if is_crit else ""
            msg = f"{crit_tag}💚 {actor.name} cast {skill.name} on {target.name}, restoring {healed:.1f} HP!"

            status_applied_name = None
            if skill.applies_effect and random.random() < skill.effect_chance:
                eff_msg = target.apply_status_effect(skill.applies_effect)
                msg += f" {eff_msg}"
                status_applied_name = skill.applies_effect.name

            return ActionResult(
                success=True,
                message=msg,
                actor_id=actor.id,
                target_id=target.id,
                skill_name=skill.name,
                healing_done=healed,
                is_crit=is_crit,
                status_applied=status_applied_name,
            )

        elif skill.skill_type in (SkillType.BUFF, SkillType.DEBUFF):
            status_applied_name = None
            msg = f"🛡️ {actor.name} used {skill.name} on {target.name}."
            if skill.applies_effect and random.random() < skill.effect_chance:
                eff_msg = target.apply_status_effect(skill.applies_effect)
                msg += f" {eff_msg}"
                status_applied_name = skill.applies_effect.name

            return ActionResult(
                success=True,
                message=msg,
                actor_id=actor.id,
                target_id=target.id,
                skill_name=skill.name,
                status_applied=status_applied_name,
            )

        return ActionResult(False, "Unknown skill type.", actor.id)

    def _advance_turn(self) -> List[str]:
        logs = []
        if self.state != BattleState.ACTIVE:
            return logs

        # Filter living fighters
        living_order = [cid for cid in self.turn_order if self.char_map[cid].is_alive]
        if not living_order:
            self._check_battle_end()
            return logs

        self.current_turn_idx += 1
        if self.current_turn_idx >= len(living_order):
            self.current_turn_idx = 0
            self.round_number += 1
            round_msg = f"--- 🔄 Round {self.round_number} ---"
            logs.append(round_msg)
            self.battle_log.append(round_msg)
            self._calculate_turn_order()

        self.turn_start_time = time.time()
        active = self.get_active_character()
        if active:
            start_logs = self._on_turn_start(active)
            logs.extend(start_logs)

        return logs

    def _check_battle_end(self) -> bool:
        # Check team survival
        teams_alive = {}
        for team_id, members in self.teams.items():
            alive_count = sum(1 for m in members if m.is_alive)
            if alive_count > 0:
                teams_alive[team_id] = alive_count

        if len(teams_alive) <= 1:
            self.state = BattleState.FINISHED
            if len(teams_alive) == 1:
                self.winner_team = list(teams_alive.keys())[0]
                end_msg = f"🏆 VICTORY for {self.winner_team}! Battle over."
            else:
                self.winner_team = None
                end_msg = "⚔️ DRAW! All fighters have perished."
            self.battle_log.append(end_msg)
            return True
        return False

    def get_valid_actions(self, char_id: str) -> List[Dict[str, Any]]:
        char = self.char_map.get(char_id)
        if not char or not char.is_alive or not char.can_act():
            return []

        valid = []
        actor_team = self.char_team[char_id]

        for s in char.skills:
            can_use = s.is_ready() and (char.current_stamina >= s.stamina_cost) and (char.current_mana >= s.mana_cost)
            # Find eligible targets
            possible_targets = []
            if s.target_type == SkillTarget.ENEMY:
                possible_targets = [c.id for c in self.char_map.values() if c.is_alive and self.char_team[c.id] != actor_team]
            elif s.target_type == SkillTarget.ALLY:
                possible_targets = [c.id for c in self.char_map.values() if c.is_alive and self.char_team[c.id] == actor_team]
            elif s.target_type == SkillTarget.SELF:
                possible_targets = [char.id]

            valid.append({
                "skill": s.to_dict(),
                "can_use": can_use,
                "targets": possible_targets,
            })
        return valid

    def to_dict(self) -> Dict[str, Any]:
        return {
            "battle_id": self.battle_id,
            "state": self.state.value,
            "round_number": self.round_number,
            "current_turn_char_id": self.turn_order[self.current_turn_idx] if self.turn_order and self.state == BattleState.ACTIVE else None,
            "turn_order": self.turn_order,
            "winner_team": self.winner_team,
            "teams": {tid: [c.to_dict() for c in chars] for tid, chars in self.teams.items()},
            "recent_logs": self.battle_log[-12:],
            "turn_timeout": self.turn_timeout,
        }
