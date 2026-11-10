"""
Unified Single-Player Game Session orchestrating the Tavern, Quests, Arena Matchmaking,
Win Probability calculation, and Battle Engine lifecycle.
"""
from typing import Optional, Dict, Any, List
from src.core.player import PlayerProfile
from src.core.character import CharacterClass, Character
from src.core.enemies import BESTIARY, EnemyTemplate
from src.core.quests import QuestManager, Quest
from src.core.calculator import calculate_win_probability
from src.core.engine import CombatEngine, BattleState


class GameSession:
    def __init__(self, player_name: str = "Geralt", char_class: CharacterClass = CharacterClass.WARRIOR):
        self.player = PlayerProfile(player_name, char_class)
        self.quest_manager = QuestManager()
        self.bestiary = BESTIARY
        self.active_enemy_template: Optional[EnemyTemplate] = None
        self.preview_enemy_char: Optional[Character] = None
        self.preview_analysis: Optional[Dict[str, Any]] = None
        self.combat_engine: Optional[CombatEngine] = None

    def select_arena_target(self, template_id: str) -> Dict[str, Any]:
        """Prepares pre-fight analysis and win percentage for the selected opponent."""
        if template_id not in self.bestiary:
            raise ValueError(f"Opponent {template_id} not found in Bestiary.")

        self.active_enemy_template = self.bestiary[template_id]
        self.preview_enemy_char = self.active_enemy_template.instantiate("enemy_preview")
        self.preview_analysis = calculate_win_probability(self.player.character, self.preview_enemy_char)
        return self.preview_analysis

    def decline_battle(self):
        """Declines the match, safely exiting pre-combat preview."""
        self.active_enemy_template = None
        self.preview_enemy_char = None
        self.preview_analysis = None

    def start_battle(self) -> List[str]:
        """Starts the actual battle between player character and the selected opponent."""
        if not self.active_enemy_template:
            raise ValueError("No active opponent selected.")

        real_enemy = self.active_enemy_template.instantiate("enemy_fighter")
        self.combat_engine = CombatEngine(battle_id="arena_duel", turn_timeout=30)
        self.combat_engine.add_character(self.player.character, "Gracz")
        self.combat_engine.add_character(real_enemy, "Arena")

        logs = self.combat_engine.start_battle()
        return logs

    def finish_battle(self) -> Dict[str, Any]:
        """Resolves battle end, awards bounties/quests, and handles progression."""
        if not self.combat_engine or self.combat_engine.state != BattleState.FINISHED:
            return {"ended": False}

        winner = self.combat_engine.winner_team
        is_victory = (winner == "Gracz")

        summary = {
            "is_victory": is_victory,
            "winner": winner,
            "gold_earned": 0,
            "exp_earned": 0,
            "completed_quest": None,
            "level_up_logs": [],
        }

        if is_victory and self.active_enemy_template:
            base_gold = self.active_enemy_template.reward_gold
            base_exp = self.active_enemy_template.reward_exp

            # Check quests
            completed_q = self.quest_manager.on_enemy_defeated(self.active_enemy_template.template_id)
            if completed_q:
                base_gold += completed_q.reward_gold
                base_exp += completed_q.reward_exp
                summary["completed_quest"] = completed_q.title

            logs = self.player.award_victory(base_gold, base_exp)
            summary["gold_earned"] = base_gold
            summary["exp_earned"] = base_exp
            summary["level_up_logs"] = logs
        else:
            self.player.award_defeat()

        return summary
