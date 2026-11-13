"""
Win probability calculation engine based on character attributes, defense mitigation,
damage scaling, agility initiative, and effective health pools.
"""
import math
from typing import Tuple, List, Dict, Any
from src.core.character import Character


def calculate_win_probability(player: Character, enemy: Character) -> Dict[str, Any]:
    """
    Computes real estimated win chance percentage (0% - 100%),
    difficulty classification, and tactical strengths/weaknesses.
    """
    # 1. Effective Health Pools (EHP) accounting for armor mitigation
    p_def = player.get_effective_defense()
    e_def = enemy.get_effective_defense()

    p_mitigation = min(0.70, p_def / (p_def + 75.0))
    e_mitigation = min(0.70, e_def / (e_def + 75.0))

    p_ehp = player.current_hp / max(0.1, (1.0 - p_mitigation))
    e_ehp = enemy.current_hp / max(0.1, (1.0 - e_mitigation))

    # 2. Expected Offensive Output per turn
    p_main_stat = max(player.strength, player.agility, player.intelligence)
    e_main_stat = max(enemy.strength, enemy.agility, enemy.intelligence)

    p_crit_factor = 1.0 + (player.crit_chance * (player.crit_multiplier - 1.0))
    e_crit_factor = 1.0 + (enemy.crit_chance * (enemy.crit_multiplier - 1.0))

    p_hit_chance = 1.0 - enemy.get_effective_dodge()
    e_hit_chance = 1.0 - player.get_effective_dodge()

    # Base damage estimate per action
    p_dmg_per_turn = (20.0 + (p_main_stat * 1.3)) * p_crit_factor * p_hit_chance
    e_dmg_per_turn = (20.0 + (e_main_stat * 1.3)) * e_crit_factor * e_hit_chance

    # 3. Turns needed to kill opponent
    turns_for_player_to_kill = max(1.0, e_ehp / max(1.0, p_dmg_per_turn))
    turns_for_enemy_to_kill = max(1.0, p_ehp / max(1.0, e_dmg_per_turn))

    # Agility initiative advantage (first strike bonus)
    speed_ratio = player.agility / max(1.0, (player.agility + enemy.agility))
    initiative_bonus = (speed_ratio - 0.5) * 0.4  # +/- 0.2 turns

    adjusted_player_turns = turns_for_player_to_kill - initiative_bonus
    adjusted_enemy_turns = turns_for_enemy_to_kill + initiative_bonus

    # Ratio of survival turns
    ratio = adjusted_enemy_turns / max(0.2, adjusted_player_turns)

    # Logistic function mapping ratio to probability
    # ratio = 1.0 -> 50%
    # ratio > 1.0 -> >50%
    k = 2.4
    raw_prob = 1.0 / (1.0 + math.exp(-k * (ratio - 1.0)))

    # Realistic bounds [4%, 96%] because RNG/crits always exist
    win_percentage = round(min(96.0, max(4.0, raw_prob * 100.0)), 1)

    # Tactical analysis tags
    insights = []
    if player.get_effective_defense() > enemy.get_effective_defense() * 1.3:
        insights.append("🛡️ Twój pancerz jest znacznie mocniejszy niż wroga.")
    elif enemy.get_effective_defense() > player.get_effective_defense() * 1.3:
        insights.append("⚠️ Wróg ma znacznie twardszy pancerz.")

    if player.agility > enemy.agility * 1.25:
        insights.append("💨 Przewaga zręczności: częściej unikasz ciosów i atakujesz pierwszy.")
    elif enemy.agility > player.agility * 1.25:
        insights.append("⚠️ Wróg jest bardzo szybki i może uniknąć Twoich ataków.")

    if p_main_stat > e_main_stat * 1.25:
        insights.append("⚔️ Twoje ataki zadają znacznie większe obrażenia.")
    elif e_main_stat > p_main_stat * 1.25:
        insights.append("⚠️ Przeciwnik uderza niesamowicie mocno!")

    if player.current_hp < player.max_hp * 0.6:
        insights.append("🩸 Twoje punkty życia są na wyczerpaniu! Odpocznij w Tawernie.")

    # Rating label & color tag
    if win_percentage >= 75.0:
        rating_label = "BARDZO WYSOKA (Łatwe zwycięstwo)"
        color_code = "green"
    elif win_percentage >= 55.0:
        rating_label = "KORZYSTNA (Przewaga po Twojej stronie)"
        color_code = "bright_green"
    elif win_percentage >= 40.0:
        rating_label = "WYRÓWNANA (Każdy błąd może kosztować życie)"
        color_code = "yellow"
    elif win_percentage >= 20.0:
        rating_label = "RYZYKOWNA (Przeciwnik ma znaczną przewagę)"
        color_code = "red"
    else:
        rating_label = "ŚMIERTELNIE NIEBEZPIECZNA (Niemal pewna porażka!)"
        color_code = "bold red"

    return {
        "win_percentage": win_percentage,
        "rating_label": rating_label,
        "color_code": color_code,
        "insights": insights,
        "player_ehp": round(p_ehp, 0),
        "enemy_ehp": round(e_ehp, 0),
        "player_dmg": round(p_dmg_per_turn, 0),
        "enemy_dmg": round(e_dmg_per_turn, 0),
    }
