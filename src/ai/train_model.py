"""
Moduł trenowania i ewaluacji modeli Sztucznej Inteligencji.
Trenuje Sieć Neuronową (Multi-Layer Perceptron) oraz modele porównawcze (Regresja Logistyczna, Random Forest),
przeprowadza rzetelną ewaluację bez przecieku danych (train/test split 80/20, skalowanie dopasowane tylko do train),
oblicza pełne metryki (Accuracy, Precision, Recall, F1, ROC-AUC, Confusion Matrix) i zapisuje model do wdrożenia w grze.
"""
import os
import json
import csv
from typing import Dict, Any, Tuple

try:
    import numpy as np
    from sklearn.model_selection import train_test_split
    from sklearn.preprocessing import StandardScaler
    from sklearn.neural_network import MLPClassifier
    from sklearn.linear_model import LogisticRegression
    from sklearn.ensemble import RandomForestClassifier
    from sklearn.metrics import (
        accuracy_score,
        precision_score,
        recall_score,
        f1_score,
        roc_auc_score,
        confusion_matrix,
        classification_report,
    )
    import joblib
except ImportError:
    pass


FEATURE_COLUMNS = [
    "player_class",
    "player_hp",
    "player_stamina",
    "player_mana",
    "player_strength",
    "player_agility",
    "player_intelligence",
    "player_defense",
    "player_dodge",
    "player_crit",
    "enemy_class",
    "enemy_hp",
    "enemy_stamina",
    "enemy_mana",
    "enemy_strength",
    "enemy_agility",
    "enemy_intelligence",
    "enemy_defense",
    "enemy_dodge",
    "enemy_crit",
]


def load_dataset(csv_path: str = "data/combat_dataset.csv") -> Tuple[Any, Any]:
    X = []
    y = []
    with open(csv_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            features = [float(row[col]) for col in FEATURE_COLUMNS]
            label = int(row["win"])
            X.append(features)
            y.append(label)

    return np.array(X, dtype=np.float32), np.array(y, dtype=np.int32)


def evaluate_model(model, X_test, y_test) -> Dict[str, Any]:
    y_pred = model.predict(X_test)
    y_proba = model.predict_proba(X_test)[:, 1] if hasattr(model, "predict_proba") else y_pred

    cm = confusion_matrix(y_test, y_pred)
    tn, fp, fn, tp = cm.ravel()

    return {
        "accuracy": round(float(accuracy_score(y_test, y_pred)), 4),
        "precision": round(float(precision_score(y_test, y_pred, zero_division=0)), 4),
        "recall": round(float(recall_score(y_test, y_pred, zero_division=0)), 4),
        "f1_score": round(float(f1_score(y_test, y_pred, zero_division=0)), 4),
        "roc_auc": round(float(roc_auc_score(y_test, y_proba)), 4),
        "confusion_matrix": {
            "true_negatives": int(tn),
            "false_positives": int(fp),
            "false_negatives": int(fn),
            "true_positives": int(tp),
        },
    }


def train_and_evaluate(
    data_path: str = "data/combat_dataset.csv",
    model_save_dir: str = "models",
    random_seed: int = 42,
) -> Dict[str, Any]:
    os.makedirs(model_save_dir, exist_ok=True)
    X, y = load_dataset(data_path)

    print(f"Załadowano zbiór danych: {X.shape[0]} próbek, {X.shape[1]} cech.")
    class_balance = np.mean(y) * 100
    print(f"Balans klas (wygrane gracza): {class_balance:.1f}%")

    # 1. Podział na zbiór treningowy i testowy (80% / 20%) ze stratyfikacją
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.20, random_state=random_seed, stratify=y
    )
    print(f"Zbiór treningowy: {X_train.shape[0]} próbek | Zbiór testowy: {X_test.shape[0]} próbek")

    # 2. Skalowanie cech (Dopasowane wyłącznie na zbiorze treningowym - brak przecieku danych!)
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)

    # 3. Model 1: Sieć Neuronowa (Multi-Layer Perceptron Classifier)
    print("\nTrenowanie Modelu 1: Sieć Neuronowa (MLPClassifier, architektura: 64x32, ReLU, Adam)...")
    mlp_model = MLPClassifier(
        hidden_layer_sizes=(64, 32),
        activation="relu",
        solver="adam",
        alpha=0.001,
        max_iter=300,
        random_state=random_seed,
        early_stopping=True,
        validation_fraction=0.1,
    )
    mlp_model.fit(X_train_scaled, y_train)
    mlp_metrics = evaluate_model(mlp_model, X_test_scaled, y_test)

    # 4. Model 2: Regresja Logistyczna (Baseline porównawczy)
    print("Trenowanie Modelu 2: Regresja Logistyczna (Baseline)...")
    log_reg = LogisticRegression(max_iter=500, random_state=random_seed)
    log_reg.fit(X_train_scaled, y_train)
    log_metrics = evaluate_model(log_reg, X_test_scaled, y_test)

    # 5. Model 3: Random Forest (Klasyczne Uczenie Maszynowe)
    print("Trenowanie Modelu 3: Random Forest (Las Losowy)...")
    rf_model = RandomForestClassifier(n_estimators=100, max_depth=12, random_state=random_seed)
    rf_model.fit(X_train, y_train)  # Drzewa nie wymagają skalowania
    rf_metrics = evaluate_model(rf_model, X_test, y_test)

    # Wybór i zapis najlepszego modelu do wdrożenia
    # Wybieramy Sieć Neuronową MLP jako główny model projektu SI
    chosen_bundle = {
        "model": mlp_model,
        "scaler": scaler,
        "feature_names": FEATURE_COLUMNS,
        "model_type": "Multi-Layer Perceptron (Neural Network)",
        "architecture": "Input(20) -> Dense(64, ReLU) -> Dense(32, ReLU) -> Output(1, Sigmoid)",
        "metrics": mlp_metrics,
        "seed": random_seed,
    }

    bundle_path = os.path.join(model_save_dir, "combat_ai_model.joblib")
    joblib.dump(chosen_bundle, bundle_path)
    print(f"\n✅ Główny Model Sieci Neuronowej pomyślnie zapisany w: {bundle_path}")

    # Raport porównawczy do celów ewaluacji akademickiej
    comparison_report = {
        "dataset_samples": int(X.shape[0]),
        "features_count": int(X.shape[1]),
        "train_samples": int(X_train.shape[0]),
        "test_samples": int(X_test.shape[0]),
        "models_evaluation": {
            "Neural_Network_MLP": mlp_metrics,
            "Logistic_Regression_Baseline": log_metrics,
            "Random_Forest": rf_metrics,
        },
        "chosen_production_model": "Neural_Network_MLP",
    }

    metrics_path = os.path.join(model_save_dir, "metrics.json")
    with open(metrics_path, "w", encoding="utf-8") as f:
        json.dump(comparison_report, f, indent=4)
    print(f"📊 Metryki i macierze pomyłek zapisane w: {metrics_path}")

    print("\n" + "=" * 65)
    print("             WYNIKI EWALUACJI MODELI SI")
    print("=" * 65)
    print(f"{'Metryka':<18} | {'Sieć Neuronowa (MLP)':<20} | {'Regresja Logistyczna':<20}")
    print("-" * 65)
    print(f"{'Accuracy':<18} | {mlp_metrics['accuracy']*100:<19.2f}% | {log_metrics['accuracy']*100:<19.2f}%")
    print(f"{'Precision':<18} | {mlp_metrics['precision']*100:<19.2f}% | {log_metrics['precision']*100:<19.2f}%")
    print(f"{'Recall':<18} | {mlp_metrics['recall']*100:<19.2f}% | {log_metrics['recall']*100:<19.2f}%")
    print(f"{'F1-Score':<18} | {mlp_metrics['f1_score']*100:<19.2f}% | {log_metrics['f1_score']*100:<19.2f}%")
    print(f"{'ROC-AUC':<18} | {mlp_metrics['roc_auc']:<20.4f} | {log_metrics['roc_auc']:<20.4f}")
    print("=" * 65)

    return comparison_report


if __name__ == "__main__":
    train_and_evaluate()
