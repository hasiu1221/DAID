"""
Persistent Player Profile tracking character progression, level, gold, EXP,
and training upgrades at the Tavern.
"""
from typing import Dict, Any, List, Tuple
from src.core.character import Character, CharacterClass, create_character


class PlayerProfile:
    def __init__(self, name: str = "Geralt", char_class: CharacterClass = CharacterClass.WARRIOR):
        self.name = name
        self.char_class = char_class
        self.level = 1
        self.exp = 0
        self.gold = 75  # Starting gold
        self.wins = 0
        self.losses = 0

        # Create active character
        self.character = create_character("player_1", name, char_class)

        # Track upgrade counts
        self.stat_upgrades = {
            "strength": 0,
            "agility": 0,
            "intelligence": 0,
            "defense": 0,
            "max_hp": 0,
        }

    @property
    def exp_to_next_level(self) -> int:
        return self.level * 100

    def rest_in_tavern(self, cost: int = 20) -> Tuple[bool, str]:
        """Restores full HP, Stamina, and Mana for gold."""
        if self.gold < cost:
            return False, f"Za mało złota! Potrzebujesz {cost} sztuk złota na nocleg w izbie."
        self.gold -= cost
        self.character.current_hp = self.character.max_hp
        self.character.current_stamina = self.character.max_stamina
        self.character.current_mana = self.character.max_mana
        self.character.status_effects.clear()
        return True, "Odpocząłeś przy ciepłym kominku. Wszystkie punkty zdrowia i energii zostały w pełni odnowione!"

    def get_training_cost(self, stat_name: str) -> int:
        current_upg = self.stat_upgrades.get(stat_name, 0)
        return 40 + (current_upg * 30)

    def train_stat(self, stat_name: str) -> Tuple[bool, str]:
        """Permanently increases a stat at the tavern combat trainer."""
        cost = self.get_training_cost(stat_name)
        if self.gold < cost:
            return False, f"Brak złota! Trening wymaga {cost} sztuk złota."

        self.gold -= cost
        self.stat_upgrades[stat_name] += 1

        if stat_name == "max_hp":
            self.character.max_hp += 25.0
            self.character.current_hp += 25.0
            stat_display = "+25 Max HP"
        elif stat_name == "defense":
            self.character.defense += 4.0
            stat_display = "+4 Pancerza"
        elif stat_name == "strength":
            self.character.strength += 3.0
            stat_display = "+3 Siły"
        elif stat_name == "agility":
            self.character.agility += 3.0
            stat_display = "+3 Zręczności"
        elif stat_name == "intelligence":
            self.character.intelligence += 3.0
            stat_display = "+3 Inteligencji"
        else:
            return False, "Nieznana statystyka."

        return True, f"Trening zakończony sukcesem! Zyskałeś {stat_display}!"

    def award_victory(self, gold: int, exp: int) -> List[str]:
        self.wins += 1
        self.gold += gold
        self.exp += exp
        logs = [f"💰 Zdobyto {gold} sztuk złota i {exp} EXP!"]

        # Level up check
        while self.exp >= self.exp_to_next_level:
            self.exp -= self.exp_to_next_level
            self.level += 1
            # Auto boost base stats
            self.character.max_hp += 15.0
            self.character.current_hp = min(self.character.max_hp, self.character.current_hp + 15.0)
            self.character.strength += 2.0
            self.character.agility += 1.0
            self.character.intelligence += 2.0
            self.character.defense += 2.0
            logs.append(f"🎉 AWANS NA POZIOM {self.level}! Wszystkie Twoje statystyki wzrosły!")

        return logs

    def award_defeat(self):
        self.losses += 1
        # Set HP to 1 so player is alive to rest
        self.character.current_hp = 1.0
        self.character.status_effects.clear()
