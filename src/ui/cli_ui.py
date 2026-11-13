"""
Rich Terminal User Interface for System Walk RPG:
- Hub Header with persistent player stats (Gold, Level, EXP, HP/STA/MP)
- Tavern menu & combat trainer
- Quest bulletin board
- Arena enemy list
- Pre-Combat Win Probability Analysis (% Chance, Insights, [1] Walcz / [2] Odrzuć)
- Battle arena cards and combat logs
"""
from typing import Dict, Any, List
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

console = Console()


def create_progress_bar(current: float, maximum: float, color: str = "green", width: int = 20) -> str:
    pct = max(0.0, min(1.0, current / maximum if maximum > 0 else 0))
    filled_len = int(width * pct)
    empty_len = width - filled_len
    bar = f"[{color}]{'█' * filled_len}{'░' * empty_len}[/{color}] {current:.0f}/{maximum:.0f}"
    return bar


def render_hub_header(player_profile):
    p = player_profile
    char = p.character
    content = []
    content.append(
        f"[bold gold1]{p.name}[/bold gold1] (Poziom [bold cyan]{p.level}[/bold cyan]) | "
        f"Klasa: [bold magenta]{p.char_class.value}[/bold magenta] | "
        f"💰 Złoto: [bold yellow]{p.gold}[/bold yellow] | "
        f"EXP: [cyan]{p.exp}/{p.exp_to_next_level}[/cyan] | "
        f"Bilans: [green]{p.wins}W[/green] / [red]{p.losses}L[/red]"
    )
    content.append(
        f"HP: {create_progress_bar(char.current_hp, char.max_hp, 'red', 18)}   "
        f"STA: {create_progress_bar(char.current_stamina, char.max_stamina, 'yellow', 15)}   "
        f"MP: {create_progress_bar(char.current_mana, char.max_mana, 'cyan', 15)}"
    )
    console.print(Panel("\n".join(content), border_style="gold1", title="[bold white]STATUS WOJOWNIKA[/bold white]"))


def render_pre_combat_preview(analysis: Dict[str, Any], player, enemy):
    console.clear()
    pct = analysis["win_percentage"]
    col = analysis["color_code"]
    label = analysis["rating_label"]

    # Big Probability Gauge Panel
    gauge_text = (
        f"[bold {col} size=18]SZANSA NA WYGRANĄ: {pct}%[/bold {col} size=18]\n"
        f"[bold white]Ocena starcia: [{col}]{label}[/{col}][/bold white]\n"
        f"[dim]Efektywne Pule Życia (EHP): Ty: ~{analysis['player_ehp']} pkt  vs  Wróg: ~{analysis['enemy_ehp']} pkt[/dim]"
    )
    console.print(Panel(gauge_text, title="[bold gold1]📊 ANALIZA PRZEDWALKOWA[/bold gold1]", border_style=col, expand=True))

    # Comparison Table
    t = Table(title="[bold yellow]Porównanie Atrybutów Gladiatorów[/bold yellow]", expand=True)
    t.add_column("Atrybut", style="bold cyan")
    t.add_column(f"Ty ({player.name})", style="bold green")
    t.add_column(f"Przeciwnik ({enemy.name})", style="bold red")

    t.add_row("Punkty Życia (HP)", f"{player.current_hp:.0f} / {player.max_hp:.0f}", f"{enemy.current_hp:.0f} / {enemy.max_hp:.0f}")
    t.add_row("Pancerz (DEF)", f"{player.defense:.0f}", f"{enemy.defense:.0f}")
    t.add_row("Siła (STR)", f"{player.strength:.0f}", f"{enemy.strength:.0f}")
    t.add_row("Zręczność (AGI)", f"{player.agility:.0f}", f"{enemy.agility:.0f}")
    t.add_row("Inteligencja (INT)", f"{player.intelligence:.0f}", f"{enemy.intelligence:.0f}")
    t.add_row("Szansa na Unik", f"{player.get_effective_dodge()*100:.0f}%", f"{enemy.get_effective_dodge()*100:.0f}%")
    t.add_row("Szansa na Krytyk", f"{player.crit_chance*100:.0f}%", f"{enemy.crit_chance*100:.0f}%")
    console.print(t)

    # Tactical Insights
    insights = analysis.get("insights", [])
    if insights:
        ins_text = "\n".join(insights)
        console.print(Panel(ins_text, title="[bold cyan]💡 Wskazówki Taktyczne[/bold cyan]", border_style="cyan"))


def render_character_card(char_data: Any, is_active: bool = False) -> Panel:
    name = char_data.name
    c_class = char_data.char_class.value
    hp = char_data.current_hp
    max_hp = char_data.max_hp
    sta = char_data.current_stamina
    max_sta = char_data.max_stamina
    mana = char_data.current_mana
    max_mana = char_data.max_mana

    active_marker = " ⚔️ [bold green][AKTYWNA TURA][/bold green]" if is_active else ""
    content = [
        f"Klasa: [bold cyan]{c_class}[/bold cyan]{active_marker}",
        f"HP:      {create_progress_bar(hp, max_hp, 'red')}",
        f"Stamina: {create_progress_bar(sta, max_sta, 'yellow')}",
        f"Mana:    {create_progress_bar(mana, max_mana, 'cyan')}",
        f"STR: [red]{char_data.strength:.0f}[/red] | AGI: [green]{char_data.agility:.0f}[/green] | INT: [blue]{char_data.intelligence:.0f}[/blue] | DEF: [white]{char_data.defense:.0f}[/white]"
    ]

    effects = char_data.status_effects
    if effects:
        eff_strs = [f"[magenta]{e.name}[/magenta] ({e.duration}t, {e.power:.0f})" for e in effects]
        content.append("Efekty: " + ", ".join(eff_strs))
    else:
        content.append("Efekty: [dim]Brak[/dim]")

    border_style = "bold green" if is_active else "bright_blue"
    return Panel("\n".join(content), title=f"[bold white]{name}[/bold white]", border_style=border_style)


def display_battle_screen(engine, player_id: str):
    console.clear()
    round_num = engine.round_number
    active = engine.get_active_character()
    active_id = active.id if active else None

    console.print(Panel(
        f"[bold gold1]⚔️ ARENA OF CHAMPIONS — RUNDA {round_num} ⚔️[/bold gold1]\n"
        f"[dim]Kto wykonuje ruch: {active.name if active else 'Nikt'}[/dim]",
        style="bold black on bright_yellow",
        expand=True
    ))

    # Cards
    player = engine.char_map.get(player_id)
    enemy = next((c for c in engine.char_map.values() if c.id != player_id), None)

    table = Table.grid(expand=True, padding=(0, 2))
    table.add_column(ratio=1)
    table.add_column(ratio=1)

    card_p = render_character_card(player, is_active=(active_id == player.id)) if player else ""
    card_e = render_character_card(enemy, is_active=(active_id == enemy.id)) if enemy else ""
    table.add_row(card_p, card_e)
    console.print(table)

    # Combat Log
    logs = engine.battle_log[-7:]
    log_text = "\n".join(logs) if logs else "[dim]Oczekiwanie na wydarzenia...[/dim]"
    console.print(Panel(log_text, title="[bold cyan]📜 Dziennik Walki[/bold cyan]", border_style="cyan"))


def display_skill_menu(skills: list, my_char: Any) -> Table:
    t = Table(title="[bold yellow]⚡ Wybierz Umiejętność (Klawisze [1] - [5])[/bold yellow]", expand=True)
    t.add_column("#", style="cyan", width=3)
    t.add_column("Umiejętność", style="bold white")
    t.add_column("Typ", style="magenta")
    t.add_column("Koszt (STA / MP)", style="yellow")
    t.add_column("Czas Odnowienia", style="green")
    t.add_column("Opis", style="dim")

    for i, s in enumerate(skills, 1):
        cd_str = "[bold green]Gotowy[/bold green]" if s.current_cooldown == 0 else f"[red]{s.current_cooldown} tur[/red]"
        cost_str = f"{s.stamina_cost} STA / {s.mana_cost} MP"
        can_afford = (my_char.current_stamina >= s.stamina_cost) and (my_char.current_mana >= s.mana_cost) and (s.current_cooldown == 0)

        num_str = f"[bold green]{i}[/bold green]" if can_afford else f"[dim]{i}[/dim]"
        name_str = f"[bold white]{s.name}[/bold white]" if can_afford else f"[dim strike]{s.name}[/dim strike]"

        t.add_row(num_str, name_str, s.skill_type.value, cost_str, cd_str, s.description)
    return t
