"""
Graphical Game Runner for System Walk RPG.
Integrates GameSession with Tavern, Stat Training, Quest Bulletin Board,
Arena Selection, Pre-Combat Win Probability Analysis ([WALCZ] / [ODRZUĆ]),
and Snappy, Non-blocking Turn-Based Combat.
"""
import time
import pygame
from src.core.character import CharacterClass
from src.core.game_session import GameSession
from src.ui.gui_ui import CombatGUI

# Responsive AI turn delay in seconds (snappy and fluid)
AI_TURN_DELAY = 0.30


class RPGApp:
    def __init__(self):
        self.gui = CombatGUI()
        self.session: GameSession = None
        self.running = True
        self.ai_turn_pending = False
        self.ai_turn_time = 0.0

        # Wire up GUI Callbacks
        self.gui.on_create_character_cb = self._on_create_character
        self.gui.on_rest_tavern_cb = self._on_rest_tavern
        self.gui.on_train_stat_cb = self._on_train_stat
        self.gui.on_select_enemy_cb = self._on_select_enemy
        self.gui.on_confirm_battle_cb = self._on_confirm_battle
        self.gui.on_decline_battle_cb = self._on_decline_battle
        self.gui.on_skill_action_cb = self._on_skill_action
        self.gui.on_return_hub_cb = self._on_return_hub

    def run(self):
        while self.running:
            if not self.gui.handle_events():
                self.running = False
                break

            # Handle automatic Enemy AI turn execution with quick delay
            if self.ai_turn_pending and time.time() >= self.ai_turn_time:
                self._execute_enemy_turn()

            # Render active screen
            if self.gui.current_screen == "CHAR_SELECT":
                self.gui.render_char_select()
            elif self.gui.current_screen == "TAVERN":
                self.gui.render_tavern()
            elif self.gui.current_screen == "QUESTS":
                self.gui.render_quests()
            elif self.gui.current_screen == "ARENA_LIST":
                self.gui.render_arena_list()
            elif self.gui.current_screen == "PRE_COMBAT":
                self.gui.render_pre_combat()
            elif self.gui.current_screen == "BATTLE":
                self.gui.render_battle()

            pygame.display.flip()
            self.clock_tick = self.gui.clock.tick(60)

        pygame.quit()

    # -------------------------------------------------------------
    # ACTION HANDLERS
    # -------------------------------------------------------------
    def _on_create_character(self, name: str, char_class_str: str):
        c_class = CharacterClass(char_class_str)
        self.session = GameSession(name, c_class)
        self.gui.session = self.session
        self.gui.current_screen = "TAVERN"
        self.gui.set_toast(f"Witaj w Tawernie, {name}! Twoja przygoda się rozpoczyna.")

    def _on_rest_tavern(self):
        if not self.session:
            return
        success, msg = self.session.player.rest_in_tavern(cost=20)
        self.gui.set_toast(msg)
        if success:
            self.gui.add_floating_text("✨ PEŁNE ULECZENIE! ✨", 260, 260, (46, 204, 113))

    def _on_train_stat(self, stat_name: str):
        if not self.session:
            return
        success, msg = self.session.player.train_stat(stat_name)
        self.gui.set_toast(msg)
        if success:
            self.gui.add_floating_text("💪 TRENING UKOŃCZONY!", 720, 240, (255, 215, 0))

    def _on_select_enemy(self, template_id: str):
        if not self.session:
            return
        self.session.select_arena_target(template_id)
        self.gui.current_screen = "PRE_COMBAT"

    def _on_decline_battle(self):
        if not self.session:
            return
        self.session.decline_battle()
        self.gui.current_screen = "ARENA_LIST"
        self.gui.set_toast("Odrzuciłeś pojedynek. Możesz wybrać innego wroga lub odpocząć.")

    def _on_confirm_battle(self):
        if not self.session or not self.session.active_enemy_template:
            return
        self.session.start_battle()
        self.gui.current_screen = "BATTLE"

        # Check if enemy has initiative on turn 1
        engine = self.session.combat_engine
        active = engine.get_active_character()
        if active and active.id != self.session.player.character.id:
            self.ai_turn_pending = True
            self.ai_turn_time = time.time() + AI_TURN_DELAY

    def _on_skill_action(self, skill_id: str):
        if not self.session or not self.session.combat_engine:
            return
        engine = self.session.combat_engine
        player = self.session.player.character
        enemy = engine.char_map.get("enemy_fighter")

        if not enemy or engine.state.value != "ACTIVE":
            return

        active = engine.get_active_character()
        if not active or active.id != player.id:
            return

        # Execute Player Action
        target_id = player.id if skill_id in ("guard", "iron_skin", "arcane_barrier", "holy_light", "smoke_bomb") else enemy.id
        result = engine.execute_action(player.id, skill_id, target_id)

        if not result.success:
            self.gui.set_toast(f"❌ {result.message}")
            return

        # Visual floating feedback
        if result.is_dodged:
            self.gui.add_floating_text("UNIK! (DODGE)", 750, 150, (100, 255, 255))
        elif result.damage_dealt > 0:
            crit = "💥 KRYTYK! " if result.is_crit else ""
            txt = f"{crit}-{result.damage_dealt:.0f}"
            col = (255, 215, 0) if result.is_crit else (255, 60, 60)
            self.gui.add_floating_text(txt, 750, 140, col)
        elif result.healing_done > 0:
            txt = f"💚 +{result.healing_done:.0f} HP"
            self.gui.add_floating_text(txt, 220, 140, (46, 204, 113))

        # Check if battle ended
        if result.battle_ended:
            self.session.finish_battle()
        else:
            # Check if it is now enemy's turn
            next_active = engine.get_active_character()
            if next_active and next_active.id == enemy.id:
                self.ai_turn_pending = True
                self.ai_turn_time = time.time() + AI_TURN_DELAY

    def _execute_enemy_turn(self):
        self.ai_turn_pending = False
        if not self.session or not self.session.combat_engine:
            return

        engine = self.session.combat_engine
        if engine.state.value != "ACTIVE":
            return

        enemy = engine.char_map.get("enemy_fighter")
        player = self.session.player.character
        if not enemy or not enemy.is_alive:
            return

        active = engine.get_active_character()
        if not active or active.id != enemy.id:
            return

        # Simple AI action decision with guaranteed progression
        valid = engine.get_valid_actions(enemy.id)
        usable = [a for a in valid if a["can_use"]]

        if not usable:
            # If no skills usable/stamina empty, pass turn safely
            res = engine.pass_turn(enemy.id)
        else:
            chosen = None
            if enemy.current_hp < enemy.max_hp * 0.4:
                defensive = [a for a in usable if a["skill"]["skill_type"] in ("HEAL", "BUFF")]
                if defensive:
                    chosen = defensive[0]
            if not chosen:
                chosen = max(usable, key=lambda a: a["skill"]["base_value"])

            target_id = enemy.id if chosen["skill"]["target_type"] == "SELF" else player.id
            res = engine.execute_action(enemy.id, chosen["skill"]["id"], target_id)
            if not res.success:
                res = engine.pass_turn(enemy.id)

        # Floating numbers on player
        if res.is_dodged:
            self.gui.add_floating_text("UNIKŁEŚ! (DODGE)", 220, 150, (100, 255, 255))
        elif res.damage_dealt > 0:
            crit = "💥 KRYTYK! " if res.is_crit else ""
            txt = f"{crit}-{res.damage_dealt:.0f}"
            col = (255, 215, 0) if res.is_crit else (255, 60, 60)
            self.gui.add_floating_text(txt, 220, 140, col)
        elif res.healing_done > 0:
            txt = f"💚 +{res.healing_done:.0f} HP"
            self.gui.add_floating_text(txt, 750, 140, (46, 204, 113))

        if res.battle_ended:
            self.session.finish_battle()
        else:
            # If next turn also belongs to enemy (e.g. player is stunned), schedule next turn
            next_active = engine.get_active_character()
            if next_active and next_active.id == enemy.id:
                self.ai_turn_pending = True
                self.ai_turn_time = time.time() + AI_TURN_DELAY

    def _on_return_hub(self):
        if self.session and self.session.combat_engine:
            self.session.combat_engine = None
        self.gui.current_screen = "TAVERN"


def main():
    app = RPGApp()
    app.run()


if __name__ == "__main__":
    main()
