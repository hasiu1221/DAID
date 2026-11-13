"""
Unit tests for RPG systems: Bestiary, Win Probability Calculator,
Quests, Player Progression, and Tavern features.
"""
import pytest
from src.core.character import CharacterClass, create_character
from src.core.enemies import BESTIARY
from src.core.calculator import calculate_win_probability
from src.core.quests import QuestManager
from src.core.player import PlayerProfile
from src.core.game_session import GameSession


def test_bestiary_opponents():
    assert len(BESTIARY) >= 7
    goblin = BESTIARY["goblin"].instantiate()
    dragon = BESTIARY["dragon_champion"].instantiate()

    assert goblin.max_hp < dragon.max_hp
    assert dragon.strength > goblin.strength
    assert len(dragon.skills) >= 4


def test_win_probability_calculation():
    # Strong warrior vs weak goblin
    strong_warrior = create_character("p1", "Champion", CharacterClass.WARRIOR)
    strong_warrior.defense = 40.0
    strong_warrior.strength = 45.0
    strong_warrior.max_hp = 350.0
    strong_warrior.current_hp = 350.0

    goblin = BESTIARY["goblin"].instantiate()
    analysis_easy = calculate_win_probability(strong_warrior, goblin)

    assert analysis_easy["win_percentage"] > 70.0
    assert "insights" in analysis_easy
    assert any("pancerz" in i.lower() for i in analysis_easy["insights"])

    # Weak rogue vs Dragon Boss
    weak_rogue = create_character("p2", "Novice", CharacterClass.ROGUE)
    dragon = BESTIARY["dragon_champion"].instantiate()
    analysis_hard = calculate_win_probability(weak_rogue, dragon)

    assert analysis_hard["win_percentage"] < 35.0


def test_tavern_healing_and_training():
    player = PlayerProfile("Tester", CharacterClass.WARRIOR)
    player.gold = 100
    player.character.current_hp = 20.0

    # Rest in tavern
    success, msg = player.rest_in_tavern(cost=20)
    assert success is True
    assert player.character.current_hp == player.character.max_hp
    assert player.gold == 80

    # Train defense
    initial_def = player.character.defense
    success_train, msg_train = player.train_stat("defense")
    assert success_train is True
    assert player.character.defense > initial_def


def test_quest_completion_and_progression():
    session = GameSession("Hero", CharacterClass.WARRIOR)
    
    # Check goblin quest before fight
    goblin_q = next(q for q in session.quest_manager.get_all_quests() if q.target_template_id == "goblin")
    assert goblin_q.is_completed is False

    # Mark goblin defeated
    completed_q = session.quest_manager.on_enemy_defeated("goblin")
    assert completed_q is not None
    assert completed_q.id == "quest_goblin"
    assert completed_q.is_completed is True


def test_game_session_pre_combat_preview():
    session = GameSession("Hero", CharacterClass.MAGE)
    analysis = session.select_arena_target("dire_wolf")

    assert analysis is not None
    assert "win_percentage" in analysis
    assert session.preview_enemy_char is not None
    assert session.active_enemy_template.template_id == "dire_wolf"

    # Decline match
    session.decline_battle()
    assert session.active_enemy_template is None
    assert session.preview_analysis is None
