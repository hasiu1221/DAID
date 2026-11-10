"""
Quest and bounty system for the Tavern bulletin board.
Tracks active bounties, targets, rewards, and completion status.
"""
from dataclasses import dataclass
from typing import Dict, List, Optional


@dataclass
class Quest:
    id: str
    title: str
    target_template_id: str
    target_name: str
    reward_gold: int
    reward_exp: int
    description: str
    is_completed: bool = False
    is_claimed: bool = False

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "title": self.title,
            "target_template_id": self.target_template_id,
            "target_name": self.target_name,
            "reward_gold": self.reward_gold,
            "reward_exp": self.reward_exp,
            "description": self.description,
            "is_completed": self.is_completed,
            "is_claimed": self.is_claimed,
        }


DEFAULT_QUESTS: List[Quest] = [
    Quest(
        id="quest_goblin",
        title="Zlecenie: Podstępny Złodziej",
        target_template_id="goblin",
        target_name="Goblin Szabrownik",
        reward_gold=60,
        reward_exp=65,
        description="Jeden z goblinów okradał zapasy w tawernie. Pokonaj go na arenie!",
    ),
    Quest(
        id="quest_wolf",
        title="Zlecenie: Bestia z Pustkowi",
        target_template_id="dire_wolf",
        target_name="Wilk Pustkowi",
        reward_gold=80,
        reward_exp=90,
        description="Dziki wilk terroryzuje okolicznych kupców. Zlikwiduj zagrożenie.",
    ),
    Quest(
        id="quest_bandit",
        title="List Gończy: Watażka Bandytów",
        target_template_id="bandit_leader",
        target_name="Kapitan Bandytów",
        reward_gold=150,
        reward_exp=160,
        description="Za głowę herszta banitów wyznaczono sowitą nagrodę w złocie.",
    ),
    Quest(
        id="quest_cultist",
        title="Polowanie: Mroczny Okultyzm",
        target_template_id="cultist_sorcerer",
        target_name="Mroczny Czarnoksiężnik",
        reward_gold=190,
        reward_exp=200,
        description="Mag odprawia nielegalne rytuały. Przerwij jego czarne praktyki.",
    ),
    Quest(
        id="quest_orc",
        title="Wyzwanie Siły: Ork Rzeźnik",
        target_template_id="orc_berserker",
        target_name="Ork Rzeźnik (Berserker)",
        reward_gold=280,
        reward_exp=300,
        description="Udowodnij swoją potęgę w starciu z bezlitosnym orczym berserkerem.",
    ),
    Quest(
        id="quest_death_knight",
        title="Święta Krucjata: Nieumarły Rycerz",
        target_template_id="death_knight",
        target_name="Nieumarły Rycerz Śmierci",
        reward_gold=400,
        reward_exp=450,
        description="Odeślij do grobu potężnego upiora zakutego w przeklętą stal.",
    ),
    Quest(
        id="quest_dragon",
        title="Legenda Areny: Pogromca Smoka",
        target_template_id="dragon_champion",
        target_name="Smoczy Czempion (BOSS)",
        reward_gold=800,
        reward_exp=900,
        description="Zostań niekwestionowanym Mistrzem Areny pokonując ziejącą ogniem bestię!",
    ),
]


class QuestManager:
    def __init__(self):
        self.quests: Dict[str, Quest] = {q.id: Quest(**q.to_dict()) for q in DEFAULT_QUESTS}

    def get_all_quests(self) -> List[Quest]:
        return list(self.quests.values())

    def on_enemy_defeated(self, enemy_template_id: str) -> Optional[Quest]:
        """Marks matching quest as completed and returns it if newly completed."""
        for q in self.quests.values():
            if q.target_template_id == enemy_template_id and not q.is_completed:
                q.is_completed = True
                return q
        return None
