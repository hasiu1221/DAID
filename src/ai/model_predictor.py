"""
Moduł inferencji (predykcji) w czasie rzeczywistym.
Ładuje wytrenowany model Sieci Neuronowej (MLP) i wykonuje szybką predykcję szansy na wygraną
dla dowolnej pary gladiatorów na Arenie.
"""
import os
from typing import Dict, Any, Optional
import numpy as np

try:
    import joblib
except ImportError:
    joblib = None

from src.core.character import Character, CharacterClass


CLASS_MAP = {
    CharacterClass.WARRIOR: 0,
    CharacterClass.MAGE: 1,
    CharacterClass.ROGUE: 2,
    CharacterClass.PALADIN: 3,
}

_MODEL_BUNDLE: Optional[Dict[str, Any]] = None


def get_or_load_ai_model(model_path: str = "models/combat_ai_model.joblib") -> Optional[Dict[str, Any]]:
    global _MODEL_BUNDLE
    if _MODEL_BUNDLE is not None:
        return _MODEL_BUNDLE

    if joblib is not None and os.path.exists(model_path):
        try:
            _MODEL_BUNDLE = joblib.load(model_path)
            return _MODEL_BUNDLE
        except Exception as e:
            print(f"Błąd ładowania modelu SI: {e}")
            return None
    return None


def extract_features_vector(player: Character, enemy: Character) -> np.ndarray:
    vector = [
        CLASS_MAP[player.char_class],
        player.current_hp,
        player.current_stamina,
        player.current_mana,
        player.strength,
        player.agility,
        player.intelligence,
        player.defense,
        player.dodge_chance,
        player.crit_chance,
        CLASS_MAP[enemy.char_class],
        enemy.current_hp,
        enemy.current_stamina,
        enemy.current_mana,
        enemy.strength,
        enemy.agility,
        enemy.intelligence,
        enemy.defense,
        enemy.dodge_chance,
        enemy.crit_chance,
    ]
    return np.array([vector], dtype=np.float32)


def predict_combat_with_ai(player: Character, enemy: Character) -> Dict[str, Any]:
    bundle = get_or_load_ai_model()

    p_ehp = player.current_hp / max(0.1, (1.0 - min(0.70, player.defense / (player.defense + 75.0))))
    e_ehp = enemy.current_hp / max(0.1, (1.0 - min(0.70, enemy.defense / (enemy.defense + 75.0))))

    # Jeśli model SI jest wytrenowany i dostępny, pobierz prawdopodobieństwo z Sieci Neuronowej!
    if bundle is not None and "model" in bundle and "scaler" in bundle:
        model = bundle["model"]
        scaler = bundle["scaler"]
        X_raw = extract_features_vector(player, enemy)
        X_scaled = scaler.transform(X_raw)

        # Predykcja z Sieci Neuronowej MLP
        proba = model.predict_proba(X_scaled)[0][1]
        win_percentage = round(min(97.0, max(3.0, proba * 100.0)), 1)
        model_used = bundle.get("model_type", "Sieć Neuronowa (MLP)")
        ai_powered = True
    else:
        # Rezerwowy kalkulator deterministyczny, jeśli model nie został jeszcze skompilowany
        ratio = (p_ehp * max(player.strength, player.agility, player.intelligence)) / max(0.1, (e_ehp * max(enemy.strength, enemy.agility, enemy.intelligence)))
        import math
        raw = 1.0 / (1.0 + math.exp(-2.2 * (ratio - 1.0)))
        win_percentage = round(min(96.0, max(4.0, raw * 100.0)), 1)
        model_used = "Deterministyczny Model Rezerwowy"
        ai_powered = False

    # Analiza taktyczna dla gracza
    insights = []
    if player.defense > enemy.defense * 1.25:
        insights.append(f"🛡️ Model SI wykrył przewagę pancerza: Twój DEF ({player.defense:.0f}) vs ({enemy.defense:.0f}).")
    elif enemy.defense > player.defense * 1.25:
        insights.append(f"⚠️ Wróg ma znacznie wyższy pancerz ({enemy.defense:.0f}). Twoje ataki fizyczne będą osłabione.")

    if player.agility > enemy.agility * 1.25:
        insights.append(f"💨 Przewaga inicjatywy: wyższa zręczność ({player.agility:.0f}) zwiększa szansę na unik i pierwszy atak.")
    elif enemy.agility > player.agility * 1.25:
        insights.append(f"⚠️ Wróg jest bardzo zwinny ({enemy.agility:.0f}) — istnieje ryzyko spudłowania.")

    p_pow = max(player.strength, player.agility, player.intelligence)
    e_pow = max(enemy.strength, enemy.agility, enemy.intelligence)
    if p_pow > e_pow * 1.25:
        insights.append(f"⚔️ Twój główny atrybut bojowy ({p_pow:.0f}) przewyższa parametry przeciwnika.")

    if player.current_hp < player.max_hp * 0.5:
        insights.append("🩸 Uwaga: Masz poniżej 50% zdrowia! Sieć neuronowa obniżyła szanse na wygraną.")

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
        "model_used": model_used,
        "ai_powered": ai_powered,
    }
