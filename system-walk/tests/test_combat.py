"""
Unit tests for the Combat Engine, character progression, skills, status effects, and network protocol.
"""
import pytest
import asyncio
from src.core.character import CharacterClass, create_character
from src.core.status_effects import StatusEffect, EffectType
from src.core.skills import SKILL_REGISTRY, SkillType, SkillTarget
from src.core.engine import CombatEngine, BattleState


def test_character_creation():
    warrior = create_character("w1", "Thor", CharacterClass.WARRIOR)
    mage = create_character("m1", "Gandalf", CharacterClass.MAGE)
    rogue = create_character("r1", "Loki", CharacterClass.ROGUE)
    paladin = create_character("p1", "Uther", CharacterClass.PALADIN)

    assert warrior.max_hp == 220.0
    assert mage.max_mana == 180.0
    assert rogue.agility > warrior.agility
    assert paladin.defense > mage.defense
    assert len(warrior.skills) >= 4


def test_damage_and_shield_mitigation():
    char = create_character("c1", "Defender", CharacterClass.WARRIOR)
    initial_hp = char.current_hp

    # Give shield of 50 HP
    shield = StatusEffect(
        id="test_shield",
        name="Barrier",
        effect_type=EffectType.SHIELD,
        duration=2,
        power=50.0,
    )
    char.apply_status_effect(shield)

    # Deal 40 raw damage - should be absorbed by shield completely
    hp_dmg, dodged, absorbed = char.take_damage(40.0, can_dodge=False)
    assert hp_dmg == 0.0
    assert absorbed > 0.0
    assert char.current_hp == initial_hp


def test_status_effects_dot():
    char = create_character("c1", "Victim", CharacterClass.WARRIOR)
    bleed = StatusEffect(
        id="bleed",
        name="Bleeding",
        effect_type=EffectType.BLEED,
        duration=2,
        power=20.0,
    )
    char.apply_status_effect(bleed)

    initial_hp = char.current_hp
    logs = char.tick_status_effects()
    assert char.current_hp < initial_hp
    assert any("bleeds" in log for log in logs)


def test_combat_engine_duel():
    c1 = create_character("p1", "Player1", CharacterClass.WARRIOR)
    c2 = create_character("p2", "Player2", CharacterClass.MAGE)

    engine = CombatEngine("test_battle")
    engine.add_character(c1, "Team1")
    engine.add_character(c2, "Team2")

    logs = engine.start_battle()
    assert engine.state == BattleState.ACTIVE
    assert len(engine.turn_order) == 2

    active = engine.get_active_character()
    target_id = c2.id if active.id == c1.id else c1.id

    # Execute basic attack
    res = engine.execute_action(active.id, "basic_attack", target_id)
    assert res.success is True
    assert res.damage_dealt >= 0.0
