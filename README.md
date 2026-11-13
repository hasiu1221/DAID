# ⚔️ System Walki Gladiatorów — Tawerna, Zadania i Arena RPG

Zaawansowany turowy system walki RPG w języku **Python 3.12**, wyposażony w interfejs graficzny 2D ([PyGame](https://www.pygame.org/)) oraz interfejs konsolowy ([Rich](https://github.com/Textualize/rich)).

---

## 🌟 Główne Funkcje Systemu

### 1. 📊 Kalkulator Szansy na Wygraną (% Win Probability)
Przed każdą walką na Arenie system dokonuje szczegółowej analizy Twoich statystyk i cech przeciwnika:
- Wylicza dokładny **procent szansy na zwycięstwo** (np. `76.5%`) w oparciu o:
  - Efektywne punkty życia (EHP uwzględniające redukcję pancerza DEF).
  - Szacowane obrażenia na turę i skalowanie atrybutów (STR, AGI, INT).
  - Szansę na uniki i trafienia krytyczne.
  - Inicjatywę i szybkość ataków.
- Wyświetla **wskazówki taktyczne** (np. *„Twój pancerz jest znacznie mocniejszy”*, *„Wróg ma wyższą zręczność i może uniknąć ataków”*).
- Zapewnia wybór strategiczny:
  - ⚔️ **[WALCZ]** — potwierdza pojedynek i wkracza na Arenę.
  - ❌ **[ODRZUĆ]** — bezpiecznie wycofuje się do Tawerny lub listy bez utraty punktów życia.

---

### 2. 🍺 Tawerna „Pod Złamanym Mieczem” (Hub Gracza)
- **Nocleg w izbie**: Pełna regeneracja HP, Staminy i Many oraz usunięcie ran za 20 sztuk złota.
- **Trener Bojowy**: Możliwość wydawania zdobytego złota na stałe podnoszenie statystyk:
  - `Maksymalne Życie (+25 HP)`
  - `Pancerz Obronny (+4 DEF)`
  - `Siła Fizyczna (+3 STR)`
  - `Zręczność & Uniki (+3 AGI)`
  - `Inteligencja Zaklęć (+3 INT)`
- **Plotki karczmarza**: Praktyczne wskazówki dotyczące mechanik walki.

---

### 3. 📜 Tablica Zadań (Bounty Board)
- Zlecenia na potwory i gladiatorów o zróżnicowanym stopniu trudności:
  - *Zlecenie: Podstępny Złodziej (Goblin)*
  - *Zlecenie: Bestia z Pustkowi (Wilk Pustkowi)*
  - *List Gończy: Watażka Bandytów (Kapitan Bandytów)*
  - *Polowanie: Mroczny Okultyzm (Mroczny Czarnoksiężnik)*
  - *Wyzwanie Siły: Ork Rzeźnik (Berserker)*
  - *Święta Krucjata: Nieumarły Rycerz (Rycerz Śmierci)*
  - *Legenda Areny: Pogromca Smoka (BOSS Smoczy Czempion)*
- Każde zrealizowane zadanie nagradza pokaźną ilością złota i punktami doświadczenia (EXP).

---

### 4. 💀 Bestiariusz Areny (7 Unikalnych Przeciwników)
1. **Goblin Szabrownik** *(Łatwy)* – wysoki unik, atakuje zatrutym sztyletem (Poison).
2. **Wilk Pustkowi** *(Łatwy)* – rozszarpujące szpony wywołujące krwotok (Bleed).
3. **Kapitan Bandytów** *(Średni)* – tarcza żelazna, potężne uderzenie i ogłuszenie (Stun).
4. **Mroczny Czarnoksiężnik** *(Średni)* – bariery runiczne, klątwa cienia i kule ognia (Burn).
5. **Ork Rzeźnik** *(Trudny)* – potężny Berserker o niszczycielskich ciosach krytycznych.
6. **Nieumarły Rycerz Śmierci** *(Trudny)* – kradzież życia (Life Drain) i tarcza kościana.
7. **Smoczy Czempion (BOSS)** – ziejący ogniem czempion areny o gigantycznym HP i sile.

---

## 🚀 Jak Uruchomić Grę

Projekt działa w 100% lokalnie i nie wymaga uruchamiania żadnego zewnętrznego serwera!

### Opcja 1: Graficzny Interfejs 2D (Pygame)
Kliknij dwukrotnie w folderze projektu:
👉 [**`start_gui.bat`**](file:///c:/Users/kanal/Desktop/system-walk/start_gui.bat)

Lub w terminalu PowerShell:
```powershell
.\.venv\Scripts\python.exe run_gui.py
```

### Opcja 2: Kolorowy Interfejs Konsolowy (Rich TUI)
Kliknij dwukrotnie:
👉 [**`start_cli.bat`**](file:///c:/Users/kanal/Desktop/system-walk/start_cli.bat)

Lub w terminalu PowerShell:
```powershell
.\.venv\Scripts\python.exe run_cli.py
```

---

## 🧪 Testy Jednostkowe
Wszystkie systemy (kalkulator szansy, bestiariusz, tawerna, zadania i silnik walki) są objęte automatycznymi testami:
```powershell
.\.venv\Scripts\python.exe -m pytest tests/ -v
```
Wynik: **11 passed in 1.77s**.
