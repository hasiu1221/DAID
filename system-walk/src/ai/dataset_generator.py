"""
Generator syntetycznego zbioru danych (Monte Carlo Dataset Generator).
Symuluje tysiące pojedynków w silniku CombatEngine z losowymi konfiguracjami statystyk
oraz klas postaci, generując plik CSV do trenowania modeli uczenia maszynowego i sieci neuronowych.
"""
import os
import csv
import random
import copy
from typing import Dict, Any, List

from src.core.character import Character, CharacterClass, create_character
from src.core.engine import CombatEngine, BattleState
from src.core.skills import SKILL_REGISTRY


CLASS_MAP = {
    CharacterClass.WARRIOR: 0,
    CharacterClass.MAGE: 1,
    CharacterClass.ROGUE: 2,
    CharacterClass.PALADIN: 3,
}


def generate_random_character(char_id: str, name: str, level_scale: float = 1.0) -> Character:
    c_class = random.choice(list(CharacterClass))
    base = create_character(char_id, name, c_class)

    # Random stat perturbation according to level scale
    scale = random.uniform(0.7, 1.8) * level_scale
    base.max_hp = round(base.max_hp * scale, 1)
    base.current_hp = base.max_hp
    base.max_stamina = round(base.max_stamina * random.uniform(0.8, 1.3), 1)
    base.current_stamina = base.max_stamina
    base.max_mana = round(base.max_mana * random.uniform(0.8, 1.4), 1)
    base.current_mana = base.max_mana

    base.strength = round(base.strength * scale, 1)
    base.agility = round(base.agility * scale, 1)
    base.intelligence = round(base.intelligence * scale, 1)
    base.defense = round(base.defense * scale, 1)
    base.dodge_chance = min(0.40, max(0.04, base.dodge_chance * random.uniform(0.8, 1.4)))
    base.crit_chance = min(0.40, max(0.04, base.crit_chance * random.uniform(0.8, 1.4)))

    return base


def simulate_single_match(player: Character, enemy: Character) -> int:
    """Runs a fast automated turn-based duel until victory. Returns 1 if player wins, 0 if enemy wins."""
    engine = CombatEngine("sim_battle", turn_timeout=30)
    engine.add_character(player, "Gracz")
    engine.add_character(enemy, "Wróg")
    engine.start_battle()

    turns = 0
    max_turns = 80  # Safety cutoff against infinite stalemates

    while engine.state == BattleState.ACTIVE and turns < max_turns:
        turns += 1
        active = engine.get_active_character()
        if not active or not active.is_alive:
            break

        target_id = enemy.id if active.id == player.id else player.id

        valid = engine.get_valid_actions(active.id)
        usable = [a for a in valid if a["can_use"]]

        if not usable:
            engine.pass_turn(active.id)
        else:
            # Tactical heuristic: heal if low HP, else highest damage
            chosen = None
            if active.current_hp < active.max_hp * 0.4:
                defensive = [a for a in usable if a["skill"]["skill_type"] in ("HEAL", "BUFF")]
                if defensive:
                    chosen = defensive[0]
            if not chosen:
                chosen = max(usable, key=lambda a: a["skill"]["base_value"])

            skill_target = active.id if chosen["skill"]["target_type"] == "SELF" else target_id
            res = engine.execute_action(active.id, chosen["skill"]["id"], skill_target)
            if not res.success:
                engine.pass_turn(active.id)

    winner = engine.winner_team
    return 1 if winner == "Gracz" else 0


def extract_features(player: Character, enemy: Character, label: int) -> Dict[str, Any]:
    return {
        "player_class": CLASS_MAP[player.char_class],
        "player_hp": player.max_hp,
        "player_stamina": player.max_stamina,
        "player_mana": player.max_mana,
        "player_strength": player.strength,
        "player_agility": player.agility,
        "player_intelligence": player.intelligence,
        "player_defense": player.defense,
        "player_dodge": round(player.dodge_chance, 3),
        "player_crit": round(player.crit_chance, 3),
        # Enemy features
        "enemy_class": CLASS_MAP[enemy.char_class],
        "enemy_hp": enemy.max_hp,
        "enemy_stamina": enemy.max_stamina,
        "enemy_mana": enemy.max_mana,
        "enemy_strength": enemy.strength,
        "enemy_agility": enemy.agility,
        "enemy_intelligence": enemy.intelligence,
        "enemy_defense": enemy.defense,
        "enemy_dodge": round(enemy.dodge_chance, 3),
        "enemy_crit": round(enemy.crit_chance, 3),
        # Target Label
        "win": label,
    }


def generate_dataset(output_path: str = "data/combat_dataset.csv", num_samples: int = 5000, seed: int = 42):
    random.seed(seed)
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    rows = []
    print(f"Rozpoczynanie generowania {num_samples} symulacji walk...")

    for i in range(num_samples):
        # Generate balanced combatants
        p_scale = random.uniform(0.8, 1.4)
        e_scale = random.uniform(0.8, 1.4)

        player = generate_random_character("p", "Player", p_scale)
        enemy = generate_random_character("e", "Enemy", e_scale)

        # Snapshot stats before simulation
        p_copy = copy.deepcopy(player)
        e_copy = copy.deepcopy(enemy)

        win_label = simulate_single_match(player, enemy)
        row = extract_features(p_copy, e_copy, win_label)
        rows.append(row)

        if (i + 1) % 1000 == 0:
            print(f"Wygenerowano {i + 1}/{num_samples} próbek...")

    fieldnames = list(rows[0].keys())
    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    print(f"✅ Zbiór danych pomyślnie zapisany w: {output_path} ({len(rows)} wierszy)")
    return output_path


if __name__ == "__main__":
    generate_dataset(num_samples=5000)
