"""
Interactive Terminal Client for System Walk RPG:
- Character creation
- Tavern Hub (Healing bed & Stat trainer)
- Quest Bulletin Board
- Arena Matchmaking
- Pre-Combat Win Probability Analysis (% Chance, Insights, [1] Walcz / [2] Odrzuć)
- Full Turn-Based Battle Loop
"""
import time
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt
from rich.table import Table

from src.core.character import CharacterClass
from src.core.game_session import GameSession
from src.ui.cli_ui import (
    render_hub_header,
    render_pre_combat_preview,
    display_battle_screen,
    display_skill_menu,
)

console = Console()


class CLIRPGApp:
    def __init__(self):
        self.session: GameSession = None

    def run(self):
        console.clear()
        console.print(Panel("[bold gold1]⚔️ SYSTEM WALK — ARENA & TAWERNA RPG ⚔️[/bold gold1]", border_style="gold1"))

        # 1. Character Setup
        name = Prompt.ask("[cyan]Wprowadź imię swojego Gladiatora[/cyan]", default="Geralt")
        console.print("\n[bold yellow]Wybierz Klasę Początkową:[/bold yellow]")
        console.print("1. [red]WOJOWNIK[/red] — Wysokie HP, ciężki pancerz, ogłuszenie i tarcza żelazna.")
        console.print("2. [blue]MAG[/blue] — Niezrównana moc kuli ognia, błyskawice i bariery runiczne.")
        console.print("3. [green]ŁOTRZYK[/green] — Maksymalna zręczność, uniki, zatrute rzutki i zabójcze krytyki.")
        console.print("4. [bright_yellow]PALADYN[/bright_yellow] — Święty gniew, solidny pancerz oraz moc samoleczenia.")

        class_choice = Prompt.ask("Wybierz klasę [1-4]", choices=["1", "2", "3", "4"], default="1")
        class_map = {
            "1": CharacterClass.WARRIOR,
            "2": CharacterClass.MAGE,
            "3": CharacterClass.ROGUE,
            "4": CharacterClass.PALADIN,
        }
        self.session = GameSession(name, class_map[class_choice])
        console.print(f"\n[green]✅ Postać {name} ({self.session.player.char_class.value}) została utworzona![/green]")
        time.sleep(1)

        # 2. Main Hub Loop
        while True:
            console.clear()
            render_hub_header(self.session.player)

            console.print("\n[bold yellow]Główny Hub — Gdzie chcesz się udać?[/bold yellow]")
            console.print("1. 🍺 [bold gold1]Tawerna[/bold gold1] (Odpoczynek / Uleczenie, Trening Statystyk, Plotki)")
            console.print("2. 📜 [bold cyan]Tablica Zadań[/bold cyan] (Zlecenia, łowcy głów i nagrody)")
            console.print("3. ⚔️ [bold red]Arena Gladiatorów[/bold red] (Wybór przeciwnika i kalkulator szansy %)")
            console.print("4. 🚪 [dim]Wyjdź z gry[/dim]")

            hub_choice = Prompt.ask("Wybierz akcję [1-4]", choices=["1", "2", "3", "4"], default="3")

            if hub_choice == "1":
                self._tavern_menu()
            elif hub_choice == "2":
                self._quests_menu()
            elif hub_choice == "3":
                self._arena_flow()
            elif hub_choice == "4":
                console.print("[yellow]Do zobaczenia na arenie![/yellow]")
                break

    # -------------------------------------------------------------
    # TAVERN MENU
    # -------------------------------------------------------------
    def _tavern_menu(self):
        while True:
            console.clear()
            render_hub_header(self.session.player)
            p = self.session.player

            console.print(Panel(
                "[bold gold1]🍺 TAWERNA 'POD ZŁAMANYM MIECZEM'[/bold gold1]\n"
                "[dim]Ciepły kominek i kufelek piwa pozwalają uleczyć rany i wzmocnić ciało u trenera.[/dim]",
                border_style="gold1"
            ))

            console.print("1. 🛏️ [green]Odpocznij w izbie (-20 💰 złota)[/green] — W pełni odnawia HP, Staminę i Manę.")
            console.print("2. 🏋️ [yellow]Trener Bojowy[/yellow] — Permanentne ulepszanie statystyk za złoto.")
            console.print("3. 💬 [cyan]Porozmawiaj z Karczmarzem[/cyan] (Wskazówki taktyczne).")
            console.print("4. ⬅️ [dim]Powrót do Głównego Hubu[/dim]")

            t_choice = Prompt.ask("Wybierz opcję [1-4]", choices=["1", "2", "3", "4"], default="1")

            if t_choice == "1":
                success, msg = p.rest_in_tavern(cost=20)
                if success:
                    console.print(f"[bold green]✨ {msg}[/bold green]")
                else:
                    console.print(f"[bold red]❌ {msg}[/bold red]")
                time.sleep(1.5)

            elif t_choice == "2":
                self._trainer_menu()

            elif t_choice == "3":
                console.print("\n[bold cyan]Karczmarz mówi:[/bold cyan]")
                console.print("• 'Zawsze patrz na wyliczony procent szans na wygraną przed walką!'")
                console.print("• 'Jeśli szansa jest poniżej 40%, użyj przycisku ODRZUĆ i podtrenuj pancerz!'")
                console.print("• 'Wykonuj zlecenia z tablicy — dają górę złota i doświadczenia!'")
                Prompt.ask("\n[dim]Naciśnij Enter, aby kontynuować...[/dim]")

            elif t_choice == "4":
                break

    def _trainer_menu(self):
        p = self.session.player
        while True:
            console.clear()
            render_hub_header(p)

            t = Table(title="[bold gold1]🏋️ Trening Bojowy (Permanentne Wzmocnienia)[/bold gold1]", expand=True)
            t.add_column("#", style="cyan", width=3)
            t.add_column("Atrybut", style="bold white")
            t.add_column("Obecna Wartość", style="green")
            t.add_column("Koszt Ulepszenia", style="yellow")

            stats = [
                ("1", "max_hp", "Maksymalne Życie (+25 HP)", f"{p.character.max_hp:.0f}"),
                ("2", "defense", "Pancerz Obronny (+4 DEF)", f"{p.character.defense:.0f}"),
                ("3", "strength", "Siła Fizyczna (+3 STR)", f"{p.character.strength:.0f}"),
                ("4", "agility", "Zręczność & Uniki (+3 AGI)", f"{p.character.agility:.0f}"),
                ("5", "intelligence", "Inteligencja Zaklęć (+3 INT)", f"{p.character.intelligence:.0f}"),
            ]

            for num, key, label, val in stats:
                cost = p.get_training_cost(key)
                t.add_row(num, label, val, f"{cost} 💰 złota")

            console.print(t)
            console.print("6. ⬅️ Powrót do Tawerny")

            tr_choice = Prompt.ask("Wybierz trening [1-6]", choices=["1", "2", "3", "4", "5", "6"], default="6")
            if tr_choice == "6":
                break

            stat_key = stats[int(tr_choice) - 1][1]
            success, msg = p.train_stat(stat_key)
            if success:
                console.print(f"[bold green]💪 {msg}[/bold green]")
            else:
                console.print(f"[bold red]❌ {msg}[/bold red]")
            time.sleep(1.2)

    # -------------------------------------------------------------
    # QUESTS BULLETIN BOARD
    # -------------------------------------------------------------
    def _quests_menu(self):
        console.clear()
        render_hub_header(self.session.player)

        t = Table(title="[bold gold1]📜 TABLICA ZLECEŃ ARENY (BOUNTY BOARD)[/bold gold1]", expand=True)
        t.add_column("Status", width=12)
        t.add_column("Tytuł Zlecenia", style="bold white")
        t.add_column("Cel", style="bold cyan")
        t.add_column("Nagroda", style="yellow")
        t.add_column("Opis", style="dim")

        for q in self.session.quest_manager.get_all_quests():
            status_str = "[bold green]✅ UKOŃCZONE[/bold green]" if q.is_completed else "[yellow]⏳ W TOKU[/yellow]"
            reward_str = f"+{q.reward_gold} 💰  +{q.reward_exp} EXP"
            t.add_row(status_str, q.title, q.target_name, reward_str, q.description)

        console.print(t)
        Prompt.ask("\n[dim]Naciśnij Enter, aby powrócić do Hubu...[/dim]")

    # -------------------------------------------------------------
    # ARENA FLOW WITH PRE-COMBAT WIN % AND [WALCZ] / [ODRZUĆ]
    # -------------------------------------------------------------
    def _arena_flow(self):
        console.clear()
        render_hub_header(self.session.player)

        # 1. Opponent selection table
        enemies = list(self.session.bestiary.values())
        t = Table(title="[bold red]⚔️ WYBIERZ PRZECIWNIKA NA ARENIE[/bold red]", expand=True)
        t.add_column("#", style="cyan", width=3)
        t.add_column("Przeciwnik", style="bold white")
        t.add_column("Trudność", style="bold yellow")
        t.add_column("HP / Pancerz", style="magenta")
        t.add_column("Nagroda", style="gold1")
        t.add_column("Opis", style="dim")

        diff_tags = {
            "Łatwy": "[green]Łatwy[/green]",
            "Średni": "[yellow]Średni[/yellow]",
            "Trudny": "[red]Trudny[/red]",
            "BOSS": "[bold red blink]BOSS[/bold red blink]",
        }

        for idx, enemy in enumerate(enemies, 1):
            d_tag = diff_tags.get(enemy.difficulty, enemy.difficulty)
            hp_def = f"{enemy.max_hp:.0f} HP | {enemy.defense:.0f} DEF"
            bounty = f"+{enemy.reward_gold} 💰 / +{enemy.reward_exp} EXP"
            t.add_row(str(idx), enemy.name, d_tag, hp_def, bounty, enemy.description)

        console.print(t)
        console.print(f"{len(enemies) + 1}. ⬅️ Powrót do Hubu")

        choices = [str(i) for i in range(1, len(enemies) + 2)]
        choice = Prompt.ask("Wybierz gladiatora", choices=choices, default="1")

        if int(choice) == len(enemies) + 1:
            return

        chosen_template = enemies[int(choice) - 1]

        # 2. PRE-COMBAT ANALYSIS (WYŚWIETLANIE % SZANSY NA WYGRANĄ)
        analysis = self.session.select_arena_target(chosen_template.template_id)
        player_char = self.session.player.character
        enemy_preview = self.session.preview_enemy_char

        render_pre_combat_preview(analysis, player_char, enemy_preview)

        # 3. DWA PRZYCISKI: [WALCZ] lub [ODRZUĆ]
        console.print("\n[bold yellow]Co decydujesz?[/bold yellow]")
        console.print("1. [bold green]⚔️ WALCZ (Rozpocznij walkę na arenie)[/bold green]")
        console.print("2. [bold red]❌ ODRZUĆ (Bezpieczny powrót — nie podejmuj walki)[/bold red]")

        decision = Prompt.ask("Wybierz decyzję [1-2]", choices=["1", "2"], default="1")

        if decision == "2":
            self.session.decline_battle()
            console.print("\n[yellow]Odrzuciłeś wyzwanie. Wracasz bezpiecznie bez utraty zdrowia![/yellow]")
            time.sleep(1.5)
            return

        # 4. EXECUTE BATTLE
        self._run_battle_loop()

    # -------------------------------------------------------------
    # TURN-BASED BATTLE LOOP
    # -------------------------------------------------------------
    def _run_battle_loop(self):
        self.session.start_battle()
        engine = self.session.combat_engine
        player = self.session.player.character

        while engine.state.value == "ACTIVE":
            display_battle_screen(engine, player.id)

            active = engine.get_active_character()
            if not active:
                break

            if active.id == player.id:
                # Player Turn
                skills = player.skills
                console.print(display_skill_menu(skills, player))

                skill_choices = [str(i) for i in range(1, len(skills) + 1)]
                s_choice = Prompt.ask("Wybierz umiejętność [1-5]", choices=skill_choices, default="1")

                chosen_skill = skills[int(s_choice) - 1]
                target_id = player.id if chosen_skill.target_type.value == "SELF" else "enemy_fighter"

                res = engine.execute_action(player.id, chosen_skill.id, target_id)
                console.print(f"[bold green]▶ {res.message}[/bold green]")
                time.sleep(0.35)

            else:
                # Enemy AI Turn
                console.print(f"[yellow]⏳ {active.name} przygotowuje atak...[/yellow]")
                time.sleep(0.35)

                valid = engine.get_valid_actions(active.id)
                usable = [a for a in valid if a["can_use"]]
                if not usable:
                    res = engine.pass_turn(active.id)
                else:
                    chosen = max(usable, key=lambda a: a["skill"]["base_value"])
                    target_id = active.id if chosen["skill"]["target_type"] == "SELF" else player.id
                    res = engine.execute_action(active.id, chosen["skill"]["id"], target_id)
                    if not res.success:
                        res = engine.pass_turn(active.id)

                console.print(f"[bold red]💥 {res.message}[/bold red]")
                time.sleep(0.35)

        # 5. Battle conclusion & rewards
        display_battle_screen(engine, player.id)
        summary = self.session.finish_battle()

        if summary.get("is_victory"):
            win_panel = (
                f"[bold gold1]🏆 WSPANIAŁE ZWYCIĘSTWO! 🏆[/bold gold1]\n"
                f"Zdobyto: [bold yellow]+{summary['gold_earned']} 💰 złota[/bold yellow] i [bold cyan]+{summary['exp_earned']} EXP[/bold cyan]!\n"
            )
            if summary.get("completed_quest"):
                win_panel += f"🎯 [bold green]UKOŃCZONO ZADANIE: {summary['completed_quest']}![/bold green]\n"
            for lvl_log in summary.get("level_up_logs", []):
                win_panel += f"⭐ {lvl_log}\n"

            console.print(Panel(win_panel, border_style="gold1"))
        else:
            console.print(Panel(
                "[bold red]💀 PORAŻKA NA ARENIE! 💀[/bold red]\n"
                "Ledwo uszedłeś z życiem (1 HP). Udaj się do Tawerny, aby odpocząć w izbie i zregenerować siły!",
                border_style="red"
            ))

        Prompt.ask("\n[dim]Naciśnij Enter, aby powrócić do Hubu...[/dim]")


def main():
    app = CLIRPGApp()
    try:
        app.run()
    except KeyboardInterrupt:
        console.print("\n[yellow]Do zobaczenia![/yellow]")


if __name__ == "__main__":
    main()
