"""
Pygame Graphical Interface for System Walk RPG:
- Character Creation
- Tavern Hub (Rest & Stat Training with Combat Master)
- Quest Bulletin Board (Bounties and Rewards)
- Arena Matchmaking with varied monster tiers
- Pre-Combat Win Probability Analysis (% Chance, Insights, [WALCZ] / [ODRZUĆ])
- Interactive Turn-Based Battle Arena with floating damage particles and Victory/Defeat modals.
"""
import time
from typing import List, Dict, Any, Optional, Callable
import pygame

pygame.init()
pygame.font.init()

# Color Palette
BG_DARK = (16, 18, 24)
PANEL_BG = (26, 30, 42)
PANEL_BORDER = (50, 56, 76)
PANEL_ACTIVE_BORDER = (46, 204, 113)

TEXT_WHITE = (245, 245, 250)
TEXT_MUTED = (160, 165, 185)
TEXT_DIM = (110, 115, 130)

COLOR_RED = (231, 76, 60)
COLOR_RED_BG = (70, 25, 25)
COLOR_YELLOW = (241, 196, 15)
COLOR_YELLOW_BG = (75, 60, 15)
COLOR_CYAN = (52, 152, 219)
COLOR_CYAN_BG = (20, 50, 75)
COLOR_GREEN = (46, 204, 113)
COLOR_PURPLE = (155, 89, 182)
COLOR_GOLD = (255, 215, 0)

BTN_BG = (38, 44, 62)
BTN_HOVER = (58, 68, 94)
BTN_ACTIVE = (46, 204, 113)
BTN_DISABLED = (28, 30, 40)


class TextInput:
    def __init__(self, rect: pygame.Rect, initial_text: str = "Geralt", max_len: int = 16):
        self.rect = rect
        self.text = initial_text
        self.max_len = max_len
        self.is_active = False

    def handle_event(self, event: pygame.event.Event) -> bool:
        if event.type == pygame.MOUSEBUTTONDOWN:
            self.is_active = self.rect.collidepoint(event.pos)
            return self.is_active
        elif event.type == pygame.KEYDOWN and self.is_active:
            if event.key == pygame.K_BACKSPACE:
                self.text = self.text[:-1]
            elif event.key in (pygame.K_RETURN, pygame.K_ESCAPE):
                self.is_active = False
            elif len(self.text) < self.max_len and event.unicode.isprintable():
                self.text += event.unicode
            return True
        return False

    def draw(self, surface: pygame.Surface, font: pygame.font.Font):
        border_col = COLOR_GOLD if self.is_active else PANEL_BORDER
        pygame.draw.rect(surface, (20, 23, 32), self.rect, border_radius=6)
        pygame.draw.rect(surface, border_col, self.rect, width=2, border_radius=6)
        display_text = self.text + ("|" if self.is_active and (int(time.time() * 2) % 2 == 0) else "")
        txt_surf = font.render(display_text, True, TEXT_WHITE)
        surface.blit(txt_surf, (self.rect.x + 10, self.rect.y + (self.rect.height - txt_surf.get_height()) // 2))


class Button:
    def __init__(self, rect: pygame.Rect, text: str, callback: Optional[Callable] = None, tag: Any = None):
        self.rect = rect
        self.text = text
        self.callback = callback
        self.tag = tag
        self.is_hovered = False
        self.is_enabled = True
        self.is_selected = False
        self.bg_color = BTN_BG
        self.accent_color = COLOR_GOLD

    def handle_event(self, event: pygame.event.Event) -> bool:
        if not self.is_enabled:
            return False
        if event.type == pygame.MOUSEMOTION:
            self.is_hovered = self.rect.collidepoint(event.pos)
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.rect.collidepoint(event.pos):
                if self.callback:
                    self.callback(self.tag) if self.tag is not None else self.callback()
                return True
        return False

    def draw(self, surface: pygame.Surface, font: pygame.font.Font):
        if not self.is_enabled:
            bg = BTN_DISABLED
            border = (42, 45, 55)
            txt_col = TEXT_DIM
        elif self.is_selected:
            bg = (32, 75, 48)
            border = COLOR_GREEN
            txt_col = TEXT_WHITE
        elif self.is_hovered:
            bg = BTN_HOVER
            border = self.accent_color
            txt_col = TEXT_WHITE
        else:
            bg = self.bg_color
            border = PANEL_BORDER
            txt_col = TEXT_WHITE

        pygame.draw.rect(surface, bg, self.rect, border_radius=8)
        border_w = 2 if (self.is_hovered or self.is_selected) else 1
        pygame.draw.rect(surface, border, self.rect, width=border_w, border_radius=8)

        txt_surf = font.render(self.text, True, txt_col)
        surface.blit(txt_surf, (self.rect.centerx - txt_surf.get_width() // 2, self.rect.centery - txt_surf.get_height() // 2))


class FloatingText:
    def __init__(self, text: str, x: int, y: int, color: tuple, font: pygame.font.Font, duration: float = 1.6):
        self.text = text
        self.x = x
        self.y = y
        self.color = color
        self.font = font
        self.created_at = time.time()
        self.duration = duration

    def update(self) -> bool:
        elapsed = time.time() - self.created_at
        if elapsed >= self.duration:
            return False
        self.y -= 40 * (1.0 / 60.0)
        return True

    def draw(self, surface: pygame.Surface):
        elapsed = time.time() - self.created_at
        alpha = max(0, int(255 * (1.0 - (elapsed / self.duration))))
        surf = self.font.render(self.text, True, self.color)
        surf.set_alpha(alpha)
        surface.blit(surf, (self.x, self.y))


class CombatGUI:
    def __init__(self, width: int = 1040, height: int = 740):
        self.width = width
        self.height = height
        self.screen = pygame.display.set_mode((width, height))
        pygame.display.set_caption("System Walk — Arena Gladiatorów i Tawerna")
        self.clock = pygame.time.Clock()

        # Fonts
        self.font_title = pygame.font.SysFont("Segoe UI", 25, bold=True)
        self.font_header = pygame.font.SysFont("Segoe UI", 18, bold=True)
        self.font_bold = pygame.font.SysFont("Segoe UI", 14, bold=True)
        self.font_normal = pygame.font.SysFont("Segoe UI", 13)
        self.font_small = pygame.font.SysFont("Segoe UI", 11)
        self.font_floating = pygame.font.SysFont("Segoe UI", 22, bold=True)
        self.font_big_percent = pygame.font.SysFont("Segoe UI", 38, bold=True)

        # Active Screen State: "CHAR_SELECT", "TAVERN", "QUESTS", "ARENA_LIST", "PRE_COMBAT", "BATTLE"
        self.current_screen = "CHAR_SELECT"

        # Character Selection Inputs
        self.name_input = TextInput(pygame.Rect(260, 90, 240, 36), initial_text="Geralt")
        self.selected_class_name = "WARRIOR"

        # Callbacks connecting to GameSession
        self.on_create_character_cb = None
        self.on_rest_tavern_cb = None
        self.on_train_stat_cb = None
        self.on_select_enemy_cb = None
        self.on_confirm_battle_cb = None
        self.on_decline_battle_cb = None
        self.on_skill_action_cb = None
        self.on_return_hub_cb = None

        # Floating texts & visual effects
        self.floating_texts: List[FloatingText] = []
        self.message_toast: Optional[str] = None
        self.message_toast_time: float = 0.0

        # Dynamic Button Caches
        self.active_buttons: List[Button] = []
        self.skill_buttons: List[Button] = []

        # Reference to GameSession
        self.session = None

    def set_toast(self, text: str):
        self.message_toast = text
        self.message_toast_time = time.time()

    def add_floating_text(self, text: str, x: int, y: int, color: tuple):
        self.floating_texts.append(FloatingText(text, x, y, color, self.font_floating))

    def draw_bar(self, x: int, y: int, w: int, h: int, cur: float, max_v: float, fg_col: tuple, bg_col: tuple, label: str):
        pct = max(0.0, min(1.0, cur / max_v if max_v > 0 else 0))
        pygame.draw.rect(self.screen, bg_col, (x, y, w, h), border_radius=4)
        fill_w = int(w * pct)
        if fill_w > 0:
            pygame.draw.rect(self.screen, fg_col, (x, y, fill_w, h), border_radius=4)
        pygame.draw.rect(self.screen, (38, 42, 56), (x, y, w, h), width=1, border_radius=4)
        txt = self.font_small.render(f"{label}: {cur:.0f} / {max_v:.0f}", True, TEXT_WHITE)
        self.screen.blit(txt, (x + 8, y + (h - txt.get_height()) // 2))

    # -------------------------------------------------------------
    # EVENT HANDLING
    # -------------------------------------------------------------
    def handle_events(self) -> bool:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False

            if self.current_screen == "CHAR_SELECT":
                self.name_input.handle_event(event)
                for btn in self.active_buttons:
                    btn.handle_event(event)
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    for c_name, _, rect in self.class_cards:
                        if rect.collidepoint(event.pos):
                            self.selected_class_name = c_name

            elif self.current_screen in ("TAVERN", "QUESTS", "ARENA_LIST", "PRE_COMBAT"):
                for btn in self.active_buttons:
                    btn.handle_event(event)

            elif self.current_screen == "BATTLE":
                if self.session and self.session.combat_engine and self.session.combat_engine.state.value == "FINISHED":
                    for btn in self.active_buttons:
                        btn.handle_event(event)
                else:
                    for btn in self.skill_buttons:
                        btn.handle_event(event)

                    # Number key shortcuts 1-5
                    if event.type == pygame.KEYDOWN and pygame.K_1 <= event.key <= pygame.K_5:
                        idx = event.key - pygame.K_1
                        if idx < len(self.skill_buttons):
                            btn = self.skill_buttons[idx]
                            if btn.is_enabled and self.on_skill_action_cb:
                                self.on_skill_action_cb(btn.tag["id"])

        return True

    # -------------------------------------------------------------
    # HEADER NAVIGATION BAR (Always visible in Hub screens)
    # -------------------------------------------------------------
    def _draw_hub_header(self):
        # Header background
        header_rect = pygame.Rect(40, 15, self.width - 80, 70)
        pygame.draw.rect(self.screen, PANEL_BG, header_rect, border_radius=10)
        pygame.draw.rect(self.screen, PANEL_BORDER, header_rect, width=1, border_radius=10)

        p = self.session.player
        # Player summary
        name_txt = f"{p.name} (Poziom {p.level})"
        self.screen.blit(self.font_header.render(name_txt, True, COLOR_GOLD), (60, 25))
        class_txt = f"Klasa: {p.char_class.value} | Zwycięstwa: {p.wins} | Porażki: {p.losses}"
        self.screen.blit(self.font_small.render(class_txt, True, TEXT_MUTED), (60, 52))

        # Gold & EXP
        gold_txt = f"💰 Złoto: {p.gold}"
        self.screen.blit(self.font_header.render(gold_txt, True, COLOR_YELLOW), (380, 25))
        exp_txt = f"EXP: {p.exp} / {p.exp_to_next_level}"
        self.screen.blit(self.font_small.render(exp_txt, True, COLOR_CYAN), (380, 52))

        # Health / Mana mini indicators
        hp_str = f"❤️ HP: {p.character.current_hp:.0f}/{p.character.max_hp:.0f}"
        self.screen.blit(self.font_bold.render(hp_str, True, COLOR_RED), (560, 25))
        sta_str = f"⚡ STA: {p.character.current_stamina:.0f} | MP: {p.character.current_mana:.0f}"
        self.screen.blit(self.font_small.render(sta_str, True, COLOR_GREEN), (560, 52))

        # Hub Tab Buttons
        self.btn_tab_tavern = Button(
            pygame.Rect(720, 25, 80, 48), "🍺 Tawerna",
            callback=lambda: setattr(self, "current_screen", "TAVERN")
        )
        self.btn_tab_tavern.is_selected = (self.current_screen == "TAVERN")

        self.btn_tab_quests = Button(
            pygame.Rect(810, 25, 85, 48), "📜 Zadania",
            callback=lambda: setattr(self, "current_screen", "QUESTS")
        )
        self.btn_tab_quests.is_selected = (self.current_screen == "QUESTS")

        self.btn_tab_arena = Button(
            pygame.Rect(905, 25, 75, 48), "⚔️ Arena",
            callback=lambda: setattr(self, "current_screen", "ARENA_LIST")
        )
        self.btn_tab_arena.is_selected = (self.current_screen in ("ARENA_LIST", "PRE_COMBAT"))
        self.btn_tab_arena.accent_color = COLOR_GREEN

        self.btn_tab_tavern.draw(self.screen, self.font_bold)
        self.btn_tab_quests.draw(self.screen, self.font_bold)
        self.btn_tab_arena.draw(self.screen, self.font_bold)

        self.active_buttons.extend([self.btn_tab_tavern, self.btn_tab_quests, self.btn_tab_arena])

    # -------------------------------------------------------------
    # SCREEN 1: CHARACTER CREATION
    # -------------------------------------------------------------
    def render_char_select(self):
        self.screen.fill(BG_DARK)
        self.active_buttons = []

        title = self.font_title.render("⚔️ SYSTEM WALK — TWÓJ GLADIATOR ⚔️", True, COLOR_GOLD)
        self.screen.blit(title, ((self.width - title.get_width()) // 2, 30))

        # Name Input
        self.screen.blit(self.font_header.render("Imię Wojownika:", True, TEXT_WHITE), (60, 95))
        self.name_input.draw(self.screen, self.font_header)

        # Classes
        self.screen.blit(self.font_header.render("Wybierz Klasę Początkową:", True, COLOR_YELLOW), (60, 155))

        classes = [
            ("WARRIOR", "Wojownik — Potężna obrona, ogromne HP, ciężki pancerz, ogłuszenie i tarcza."),
            ("MAGE", "Mag — Niezrównana siła zaklęć ognia i piorunów, bariery ochronne, wysoka mana."),
            ("ROGUE", "Łotrzyk — Maksymalna zręczność, śmiertelne ciosy krytyczne, trucizny i uniki."),
            ("PALADIN", "Paladyn — Wyważony obrońca wiary, święty gniew oraz potężne leczenie."),
        ]
        self.class_cards = []
        for i, (c_name, c_desc) in enumerate(classes):
            rect = pygame.Rect(60, 195 + (i * 85), 920, 72)
            self.class_cards.append((c_name, c_desc, rect))

            is_sel = (c_name == self.selected_class_name)
            bg = (34, 45, 62) if is_sel else PANEL_BG
            border = COLOR_GOLD if is_sel else PANEL_BORDER
            pygame.draw.rect(self.screen, bg, rect, border_radius=8)
            pygame.draw.rect(self.screen, border, rect, width=2 if is_sel else 1, border_radius=8)

            badge = "★ WYBRANA" if is_sel else "KLIKNIJ ABY WYBRAĆ"
            b_surf = self.font_small.render(badge, True, COLOR_GREEN if is_sel else TEXT_MUTED)
            self.screen.blit(b_surf, (rect.right - b_surf.get_width() - 15, rect.y + 12))

            name_surf = self.font_header.render(c_name, True, COLOR_GOLD if is_sel else TEXT_WHITE)
            self.screen.blit(name_surf, (rect.x + 20, rect.y + 12))

            desc_surf = self.font_normal.render(c_desc, True, TEXT_WHITE if is_sel else TEXT_MUTED)
            self.screen.blit(desc_surf, (rect.x + 20, rect.y + 42))

        # Start Button
        def on_start():
            if self.on_create_character_cb:
                self.on_create_character_cb(self.name_input.text.strip() or "Geralt", self.selected_class_name)

        btn_start = Button(pygame.Rect(self.width // 2 - 180, 570, 360, 56), "ROZPOCZNIJ PRZYGODĘ ⚔️", callback=on_start)
        btn_start.accent_color = COLOR_GREEN
        btn_start.draw(self.screen, self.font_header)
        self.active_buttons.append(btn_start)

    # -------------------------------------------------------------
    # SCREEN 2: TAVERN (Odpoczynek + Trening Statystyk)
    # -------------------------------------------------------------
    def render_tavern(self):
        self.screen.fill(BG_DARK)
        self.active_buttons = []
        self._draw_hub_header()

        # Tavern Intro Box
        box = pygame.Rect(40, 100, self.width - 80, 95)
        pygame.draw.rect(self.screen, PANEL_BG, box, border_radius=8)
        pygame.draw.rect(self.screen, PANEL_BORDER, box, width=1, border_radius=8)

        self.screen.blit(self.font_header.render("🍺 TAWERNA 'POD ZŁAMANYM MIECZEM'", True, COLOR_GOLD), (60, 112))
        intro_desc = (
            "Ciepły kominek, gęste piwo i bezpieczne schronienie przed brutalnością areny. "
            "Możesz tu zregenerować swoje siły lub udać się do mistrza fechtunku, aby na stałe ulepszyć statystyki!"
        )
        self.screen.blit(self.font_normal.render(intro_desc, True, TEXT_MUTED), (60, 142))

        # Rest Section
        rest_rect = pygame.Rect(40, 210, 440, 180)
        pygame.draw.rect(self.screen, PANEL_BG, rest_rect, border_radius=8)
        pygame.draw.rect(self.screen, PANEL_BORDER, rest_rect, width=1, border_radius=8)

        self.screen.blit(self.font_header.render("🛏️ Nocleg w Izbie (Regeneracja)", True, COLOR_YELLOW), (60, 225))
        self.screen.blit(self.font_normal.render("Koszt: 20 sztuk złota", True, COLOR_GOLD), (60, 255))
        self.screen.blit(self.font_small.render("W pełni odnawia Twoje HP, Staminę i Manę oraz usuwa rany.", True, TEXT_MUTED), (60, 280))

        btn_rest = Button(
            pygame.Rect(60, 315, 400, 50),
            "Odpocznij i Ulecz Rany (-20 💰)",
            callback=lambda: self.on_rest_tavern_cb() if self.on_rest_tavern_cb else None
        )
        btn_rest.accent_color = COLOR_GREEN
        btn_rest.draw(self.screen, self.font_bold)
        self.active_buttons.append(btn_rest)

        # Gossip / Tips Section
        gossip_rect = pygame.Rect(40, 405, 440, 240)
        pygame.draw.rect(self.screen, PANEL_BG, gossip_rect, border_radius=8)
        pygame.draw.rect(self.screen, PANEL_BORDER, gossip_rect, width=1, border_radius=8)

        self.screen.blit(self.font_header.render("💬 Plotki Karczmarza", True, COLOR_CYAN), (60, 420))
        tips = [
            "• 'Zanim wejdziesz na Arenę, zawsze sprawdź swój szacowany % szansy!'",
            "• 'Jeśli procent wygranej jest poniżej 40%, lepiej odrzuć walkę i podtrenuj.'",
            "• 'Wilk i Berserker rozszarpują pancerz krwawieniem — miej zapas HP!'",
            "• 'Zadania z tablicy ogłoszeń dają dodatkowe złoto i EXP za wygraną.'",
            "• 'Inwestuj złoto u Trenera — siła i pancerz drastycznie zwiększają szanse.'",
        ]
        for idx, tip in enumerate(tips):
            self.screen.blit(self.font_small.render(tip, True, TEXT_WHITE), (60, 455 + (idx * 30)))

        # Training Master Section (Right Column)
        train_rect = pygame.Rect(500, 210, 500, 435)
        pygame.draw.rect(self.screen, PANEL_BG, train_rect, border_radius=8)
        pygame.draw.rect(self.screen, PANEL_BORDER, train_rect, width=1, border_radius=8)

        self.screen.blit(self.font_header.render("🏋️ Trener Bojowy (Ulepszanie Postaci)", True, COLOR_GOLD), (520, 225))
        self.screen.blit(self.font_small.render("Płać złotem za permanentne wzmocnienie swoich cech bojowych:", True, TEXT_MUTED), (520, 252))

        p = self.session.player
        trainable_stats = [
            ("max_hp", "Maksymalne Życie (+25 HP)", p.character.max_hp),
            ("defense", "Pancerz Obronny (+4 DEF)", p.character.defense),
            ("strength", "Siła Fizyczna (+3 STR)", p.character.strength),
            ("agility", "Zręczność & Uniki (+3 AGI)", p.character.agility),
            ("intelligence", "Inteligencja Zaklęć (+3 INT)", p.character.intelligence),
        ]

        for idx, (s_key, s_label, cur_val) in enumerate(trainable_stats):
            y = 280 + (idx * 68)
            cost = p.get_training_cost(s_key)

            # Stat description line
            self.screen.blit(self.font_bold.render(s_label, True, TEXT_WHITE), (520, y + 4))
            val_txt = f"Obecna wartość: {cur_val:.0f}"
            self.screen.blit(self.font_small.render(val_txt, True, COLOR_CYAN), (520, y + 26))

            btn_tr = Button(
                pygame.Rect(800, y, 180, 45),
                f"Ulepsz ({cost} 💰)",
                callback=lambda k=s_key: self.on_train_stat_cb(k) if self.on_train_stat_cb else None
            )
            btn_tr.is_enabled = (p.gold >= cost)
            btn_tr.accent_color = COLOR_YELLOW
            btn_tr.draw(self.screen, self.font_bold)
            self.active_buttons.append(btn_tr)

        # Message Toast
        self._draw_toast()

    # -------------------------------------------------------------
    # SCREEN 3: QUESTS (Tablica Zadań)
    # -------------------------------------------------------------
    def render_quests(self):
        self.screen.fill(BG_DARK)
        self.active_buttons = []
        self._draw_hub_header()

        title_box = pygame.Rect(40, 100, self.width - 80, 50)
        pygame.draw.rect(self.screen, PANEL_BG, title_box, border_radius=8)
        self.screen.blit(self.font_header.render("📜 TABLICA ZLECEŃ I NAGRÓD (BOUNTY BOARD)", True, COLOR_GOLD), (60, 112))

        quests = self.session.quest_manager.get_all_quests()
        for idx, q in enumerate(quests[:6]):
            y = 165 + (idx * 84)
            card = pygame.Rect(40, y, self.width - 80, 74)
            is_comp = q.is_completed

            bg = (24, 40, 30) if is_comp else PANEL_BG
            border = COLOR_GREEN if is_comp else PANEL_BORDER
            pygame.draw.rect(self.screen, bg, card, border_radius=8)
            pygame.draw.rect(self.screen, border, card, width=1, border_radius=8)

            # Title & Target
            self.screen.blit(self.font_header.render(q.title, True, COLOR_GOLD if not is_comp else COLOR_GREEN), (60, y + 10))
            self.screen.blit(self.font_small.render(q.description, True, TEXT_WHITE), (60, y + 36))

            # Rewards
            r_str = f"Nagroda: +{q.reward_gold} 💰 | +{q.reward_exp} EXP"
            self.screen.blit(self.font_bold.render(r_str, True, COLOR_YELLOW), (600, y + 12))

            # Status Tag / Go to Arena button
            if is_comp:
                badge = self.font_bold.render("✅ UKOŃCZONE", True, COLOR_GREEN)
                self.screen.blit(badge, (850, y + 24))
            else:
                def go_arena(t_id=q.target_template_id):
                    self.current_screen = "ARENA_LIST"
                    if self.on_select_enemy_cb:
                        self.on_select_enemy_cb(t_id)

                btn_hunt = Button(pygame.Rect(820, y + 14, 160, 44), "Poluj na Arenie ⚔️", callback=go_arena)
                btn_hunt.accent_color = COLOR_RED
                btn_hunt.draw(self.screen, self.font_bold)
                self.active_buttons.append(btn_hunt)

    # -------------------------------------------------------------
    # SCREEN 4: ARENA OPPONENT SELECTION LIST
    # -------------------------------------------------------------
    def render_arena_list(self):
        self.screen.fill(BG_DARK)
        self.active_buttons = []
        self._draw_hub_header()

        title_box = pygame.Rect(40, 100, self.width - 80, 48)
        pygame.draw.rect(self.screen, PANEL_BG, title_box, border_radius=8)
        self.screen.blit(self.font_header.render("⚔️ WYBIERZ PRZECIWNIKA NA ARENIE GLADIATORÓW", True, COLOR_GOLD), (60, 112))

        enemies = list(self.session.bestiary.values())
        diff_colors = {
            "Łatwy": COLOR_GREEN,
            "Średni": COLOR_YELLOW,
            "Trudny": COLOR_RED,
            "BOSS": COLOR_PURPLE,
        }

        for idx, enemy in enumerate(enemies[:7]):
            y = 160 + (idx * 75)
            card = pygame.Rect(40, y, self.width - 80, 66)
            pygame.draw.rect(self.screen, PANEL_BG, card, border_radius=8)
            pygame.draw.rect(self.screen, PANEL_BORDER, card, width=1, border_radius=8)

            # Name & Difficulty Badge
            d_col = diff_colors.get(enemy.difficulty, TEXT_WHITE)
            self.screen.blit(self.font_header.render(enemy.name, True, TEXT_WHITE), (60, y + 10))
            d_txt = f"[{enemy.difficulty.upper()}] | Klasa: {enemy.char_class.value}"
            self.screen.blit(self.font_small.render(d_txt, True, d_col), (60, y + 36))

            # Stats Preview
            stats_str = f"HP: {enemy.max_hp:.0f} | DEF: {enemy.defense:.0f} | STR: {enemy.strength:.0f} | AGI: {enemy.agility:.0f}"
            self.screen.blit(self.font_small.render(stats_str, True, TEXT_MUTED), (420, y + 22))

            # Bounty
            bounty_str = f"+{enemy.reward_gold} 💰  +{enemy.reward_exp} EXP"
            self.screen.blit(self.font_bold.render(bounty_str, True, COLOR_GOLD), (650, y + 22))

            # Select button
            def select_opp(t_id=enemy.template_id):
                if self.on_select_enemy_cb:
                    self.on_select_enemy_cb(t_id)

            btn_sel = Button(pygame.Rect(840, y + 10, 140, 46), "Wybierz ⚔️", callback=select_opp)
            btn_sel.accent_color = COLOR_GOLD
            btn_sel.draw(self.screen, self.font_bold)
            self.active_buttons.append(btn_sel)

    # -------------------------------------------------------------
    # SCREEN 5: PRE-COMBAT WIN PROBABILITY & DECISION ([WALCZ] / [ODRZUĆ])
    # -------------------------------------------------------------
    def render_pre_combat(self):
        self.screen.fill(BG_DARK)
        self.active_buttons = []

        title = self.font_title.render("📊 ANALIZA PRZEDWALKOWA & SZANSA NA WYGRANĄ", True, COLOR_GOLD)
        self.screen.blit(title, ((self.width - title.get_width()) // 2, 25))

        player = self.session.player.character
        enemy = self.session.preview_enemy_char
        analysis = self.session.preview_analysis

        if not enemy or not analysis:
            return

        # Fighter Comparison Panels
        # Left Panel: Twoja Postać
        p_rect = pygame.Rect(60, 75, 430, 240)
        pygame.draw.rect(self.screen, PANEL_BG, p_rect, border_radius=10)
        pygame.draw.rect(self.screen, COLOR_GREEN, p_rect, width=2, border_radius=10)

        self.screen.blit(self.font_header.render(f"🛡️ TWOJA POSTAĆ: {player.name}", True, COLOR_GOLD), (80, 90))
        self.screen.blit(self.font_small.render(f"Klasa: {player.char_class.value}", True, COLOR_CYAN), (80, 116))

        self.draw_bar(80, 140, 390, 20, player.current_hp, player.max_hp, COLOR_RED, COLOR_RED_BG, "HP")
        self.draw_bar(80, 168, 390, 18, player.current_stamina, player.max_stamina, COLOR_YELLOW, COLOR_YELLOW_BG, "STAMINA")
        self.draw_bar(80, 192, 390, 18, player.current_mana, player.max_mana, COLOR_CYAN, COLOR_CYAN_BG, "MANA")

        p_stats = f"STR: {player.strength:.0f} | AGI: {player.agility:.0f} | INT: {player.intelligence:.0f} | DEF: {player.defense:.0f}"
        self.screen.blit(self.font_bold.render(p_stats, True, TEXT_WHITE), (80, 222))
        p_ehp = f"Efektywne Pule Życia (EHP): ~{analysis['player_ehp']} pkt"
        self.screen.blit(self.font_small.render(p_ehp, True, TEXT_MUTED), (80, 250))

        # Right Panel: Przeciwnik
        e_rect = pygame.Rect(550, 75, 430, 240)
        pygame.draw.rect(self.screen, PANEL_BG, e_rect, border_radius=10)
        pygame.draw.rect(self.screen, COLOR_RED, e_rect, width=2, border_radius=10)

        self.screen.blit(self.font_header.render(f"💀 PRZECIWNIK: {enemy.name}", True, COLOR_RED), (570, 90))
        self.screen.blit(self.font_small.render(f"Klasa: {enemy.char_class.value} | Trudność: {self.session.active_enemy_template.difficulty}", True, COLOR_YELLOW), (570, 116))

        self.draw_bar(570, 140, 390, 20, enemy.current_hp, enemy.max_hp, COLOR_RED, COLOR_RED_BG, "HP")
        self.draw_bar(570, 168, 390, 18, enemy.current_stamina, enemy.max_stamina, COLOR_YELLOW, COLOR_YELLOW_BG, "STAMINA")
        self.draw_bar(570, 192, 390, 18, enemy.current_mana, enemy.max_mana, COLOR_CYAN, COLOR_CYAN_BG, "MANA")

        e_stats = f"STR: {enemy.strength:.0f} | AGI: {enemy.agility:.0f} | INT: {enemy.intelligence:.0f} | DEF: {enemy.defense:.0f}"
        self.screen.blit(self.font_bold.render(e_stats, True, TEXT_WHITE), (570, 222))
        e_ehp = f"Efektywne Pule Życia (EHP): ~{analysis['enemy_ehp']} pkt"
        self.screen.blit(self.font_small.render(e_ehp, True, TEXT_MUTED), (570, 250))

        # Center VS Badge
        vs_surf = self.font_title.render("VS", True, COLOR_RED)
        self.screen.blit(vs_surf, (self.width // 2 - vs_surf.get_width() // 2, 175))

        # Central Probability Gauge Banner
        prob_rect = pygame.Rect(60, 335, 920, 130)
        pygame.draw.rect(self.screen, PANEL_BG, prob_rect, border_radius=10)
        prob_col = COLOR_GREEN if analysis["win_percentage"] >= 60 else (COLOR_YELLOW if analysis["win_percentage"] >= 40 else COLOR_RED)
        pygame.draw.rect(self.screen, prob_col, prob_rect, width=2, border_radius=10)

        # Big percentage text
        pct_text = f"SZANSA NA WYGRANĄ: {analysis['win_percentage']}%"
        pct_surf = self.font_big_percent.render(pct_text, True, prob_col)
        self.screen.blit(pct_surf, (self.width // 2 - pct_surf.get_width() // 2, 350))

        # Rating label
        rat_surf = self.font_header.render(f"Ocena pojedynku: {analysis['rating_label']}", True, TEXT_WHITE)
        self.screen.blit(rat_surf, (self.width // 2 - rat_surf.get_width() // 2, 400))

        # Tactical Insights Box
        info_rect = pygame.Rect(60, 480, 920, 130)
        pygame.draw.rect(self.screen, PANEL_BG, info_rect, border_radius=8)
        pygame.draw.rect(self.screen, PANEL_BORDER, info_rect, width=1, border_radius=8)

        self.screen.blit(self.font_bold.render("💡 ANALIZA TAKTYCZNA STATYSTYK:", True, COLOR_CYAN), (80, 492))
        insights = analysis.get("insights", [])
        if insights:
            for i_idx, ins in enumerate(insights[:3]):
                self.screen.blit(self.font_normal.render(ins, True, TEXT_WHITE), (80, 520 + (i_idx * 26)))
        else:
            self.screen.blit(self.font_normal.render("Obaj gladiatorzy mają zbliżone parametry bojowe.", True, TEXT_MUTED), (80, 525))

        # TWO KEY BUTTONS: [WALCZ] and [ODRZUĆ]
        btn_fight = Button(
            pygame.Rect(self.width // 2 - 310, 630, 280, 65),
            "⚔️ WALCZ (Rozpocznij Walkę)",
            callback=self.on_confirm_battle_cb
        )
        btn_fight.bg_color = (30, 75, 45)
        btn_fight.accent_color = COLOR_GREEN

        btn_decline = Button(
            pygame.Rect(self.width // 2 + 30, 630, 280, 65),
            "❌ ODRZUĆ (Bezpieczny Powrót)",
            callback=self.on_decline_battle_cb
        )
        btn_decline.bg_color = (75, 30, 35)
        btn_decline.accent_color = COLOR_RED

        btn_fight.draw(self.screen, self.font_header)
        btn_decline.draw(self.screen, self.font_header)
        self.active_buttons.extend([btn_fight, btn_decline])

    # -------------------------------------------------------------
    # SCREEN 6: BATTLE SCREEN
    # -------------------------------------------------------------
    def render_battle(self):
        self.screen.fill(BG_DARK)
        self.active_buttons = []
        self.skill_buttons = []

        if not self.session or not self.session.combat_engine:
            return

        engine = self.session.combat_engine
        player = self.session.player.character
        enemy = engine.char_map.get("enemy_fighter")

        # Top Banner
        round_rect = pygame.Rect(40, 15, self.width - 80, 48)
        pygame.draw.rect(self.screen, (34, 30, 20), round_rect, border_radius=8)
        pygame.draw.rect(self.screen, COLOR_GOLD, round_rect, width=2, border_radius=8)

        r_txt = f"⚔️ ARENA OF CHAMPIONS — RUNDA {engine.round_number} ⚔️"
        b_surf = self.font_header.render(r_txt, True, COLOR_GOLD)
        self.screen.blit(b_surf, (self.width // 2 - b_surf.get_width() // 2, 26))

        active_char = engine.get_active_character()
        is_my_turn = (active_char and active_char.id == player.id)

        # Draw Fighter Panels
        self._draw_battle_fighter_panel(player, 40, 75, is_active=is_my_turn, is_player=True)
        if enemy:
            self._draw_battle_fighter_panel(enemy, self.width - 480, 75, is_active=(not is_my_turn and engine.state.value == "ACTIVE"), is_player=False)

        # Center VS
        vs_rect = pygame.Rect(self.width // 2 - 35, 175, 70, 40)
        pygame.draw.rect(self.screen, (40, 20, 25), vs_rect, border_radius=6)
        pygame.draw.rect(self.screen, COLOR_RED, vs_rect, width=1, border_radius=6)
        self.screen.blit(self.font_header.render("VS", True, COLOR_RED), (self.width // 2 - 13, 182))

        # Turn indicator banner
        ind_rect = pygame.Rect(40, 318, self.width - 80, 34)
        ind_bg = (20, 48, 30) if is_my_turn else (30, 32, 42)
        ind_border = COLOR_GREEN if is_my_turn else PANEL_BORDER
        pygame.draw.rect(self.screen, ind_bg, ind_rect, border_radius=6)
        pygame.draw.rect(self.screen, ind_border, ind_rect, width=1, border_radius=6)

        if engine.state.value == "FINISHED":
            turn_msg = f"🏁 POJEDYNEK ZAKOŃCZONY! Zwycięzca: {engine.winner_team}"
            turn_col = COLOR_GOLD
        elif is_my_turn:
            turn_msg = "⚔️ TWOJA TURA! Wybierz umiejętność (kliknij lub wciśnij klawisz [1] - [5]):"
            turn_col = COLOR_GREEN
        else:
            turn_msg = f"⏳ Tura przeciwnika ({enemy.name if enemy else 'Wróg'})..."
            turn_col = TEXT_MUTED
        self.screen.blit(self.font_bold.render(turn_msg, True, turn_col), (55, 324))

        # Skill Table (Buttons 1-5)
        skills = player.skills
        btn_w = 180
        btn_h = 92
        spacing = 15
        start_x = 40
        start_y = 360

        for idx, s in enumerate(skills):
            bx = start_x + (idx * (btn_w + spacing))
            rect = pygame.Rect(bx, start_y, btn_w, btn_h)

            cd = s.current_cooldown
            sta_cost = s.stamina_cost
            mana_cost = s.mana_cost
            can_afford = (player.current_stamina >= sta_cost) and (player.current_mana >= mana_cost) and (cd == 0) and is_my_turn and (engine.state.value == "ACTIVE")

            def make_cb(skill_id=s.id):
                if self.on_skill_action_cb:
                    self.on_skill_action_cb(skill_id)

            btn = Button(rect, "", callback=make_cb, tag={"id": s.id, "target_type": s.target_type.value})
            btn.is_enabled = can_afford
            btn.draw(self.screen, self.font_bold)
            self._draw_skill_content(rect, s, idx + 1, can_afford)
            self.skill_buttons.append(btn)

        # Combat Log Panel
        log_rect = pygame.Rect(40, 465, self.width - 80, 245)
        pygame.draw.rect(self.screen, PANEL_BG, log_rect, border_radius=8)
        pygame.draw.rect(self.screen, PANEL_BORDER, log_rect, width=1, border_radius=8)

        self.screen.blit(self.font_bold.render("📜 DZIENNIK ARENY (COMBAT LOG)", True, COLOR_CYAN), (55, 475))
        recent_logs = engine.battle_log[-8:]
        for idx, line in enumerate(recent_logs):
            txt = self.font_small.render(line, True, TEXT_WHITE)
            self.screen.blit(txt, (55, 502 + (idx * 23)))

        # Draw floating damage numbers
        surviving = []
        for ft in self.floating_texts:
            if ft.update():
                ft.draw(self.screen)
                surviving.append(ft)
        self.floating_texts = surviving

        # Game Over Modal
        if engine.state.value == "FINISHED":
            self._render_battle_end_modal()

    def _draw_battle_fighter_panel(self, char: Any, x: int, y: int, is_active: bool, is_player: bool):
        w = 440
        h = 230
        rect = pygame.Rect(x, y, w, h)
        border_col = COLOR_GREEN if is_active else (COLOR_CYAN if is_player else PANEL_BORDER)
        pygame.draw.rect(self.screen, PANEL_BG, rect, border_radius=10)
        pygame.draw.rect(self.screen, border_col, rect, width=2 if is_active else 1, border_radius=10)

        tag = "(TY)" if is_player else ""
        self.screen.blit(self.font_header.render(f"{char.name} {tag}", True, COLOR_GOLD if is_active else TEXT_WHITE), (x + 18, y + 12))
        self.screen.blit(self.font_bold.render(f"Klasa: {char.char_class.value}", True, COLOR_CYAN), (x + 18, y + 38))

        if is_active:
            self.screen.blit(self.font_small.render("★ AKTYWNA TURA", True, COLOR_GREEN), (rect.right - 120, y + 14))

        bx = x + 18
        bw = w - 36
        self.draw_bar(bx, y + 65, bw, 20, char.current_hp, char.max_hp, COLOR_RED, COLOR_RED_BG, "HP")
        self.draw_bar(bx, y + 90, bw, 18, char.current_stamina, char.max_stamina, COLOR_YELLOW, COLOR_YELLOW_BG, "STAMINA")
        self.draw_bar(bx, y + 113, bw, 18, char.current_mana, char.max_mana, COLOR_CYAN, COLOR_CYAN_BG, "MANA")

        stats_str = f"STR: {char.strength:.0f} | AGI: {char.agility:.0f} | INT: {char.intelligence:.0f} | DEF: {char.defense:.0f}"
        self.screen.blit(self.font_small.render(stats_str, True, TEXT_MUTED), (bx, y + 142))

        effects = char.status_effects
        if effects:
            eff_strs = [f"{e.name}({e.duration}t, {e.power:.0f})" for e in effects]
            self.screen.blit(self.font_small.render("Efekty: " + ", ".join(eff_strs), True, COLOR_PURPLE), (bx, y + 170))
        else:
            self.screen.blit(self.font_small.render("Efekty: Brak", True, TEXT_DIM), (bx, y + 170))

    def _draw_skill_content(self, rect: pygame.Rect, skill: Any, key_idx: int, can_afford: bool):
        self.screen.blit(self.font_bold.render(f"[{key_idx}] {skill.name}", True, COLOR_GOLD if can_afford else TEXT_DIM), (rect.x + 8, rect.y + 6))
        cost_txt = f"STA: {skill.stamina_cost} | MP: {skill.mana_cost}"
        self.screen.blit(self.font_small.render(cost_txt, True, COLOR_YELLOW if can_afford else TEXT_DIM), (rect.x + 8, rect.y + 30))
        type_txt = f"{skill.skill_type.value} ({skill.target_type.value})"
        self.screen.blit(self.font_small.render(type_txt, True, COLOR_CYAN if can_afford else TEXT_DIM), (rect.x + 8, rect.y + 50))

        if skill.current_cooldown > 0:
            st_txt = f"⏳ CD: {skill.current_cooldown}t"
            col = COLOR_RED
        elif can_afford:
            st_txt = "✓ GOTOWY"
            col = COLOR_GREEN
        else:
            st_txt = "✗ BRAK ZASOBÓW"
            col = COLOR_RED
        self.screen.blit(self.font_small.render(st_txt, True, col), (rect.x + 8, rect.y + 70))

    def _render_battle_end_modal(self):
        overlay = pygame.Surface((self.width, self.height))
        overlay.set_alpha(190)
        overlay.fill((8, 10, 16))
        self.screen.blit(overlay, (0, 0))

        m_rect = pygame.Rect(self.width // 2 - 270, self.height // 2 - 130, 540, 260)
        pygame.draw.rect(self.screen, PANEL_BG, m_rect, border_radius=12)

        winner = self.session.combat_engine.winner_team
        is_vic = (winner == "Gracz")
        b_col = COLOR_GOLD if is_vic else COLOR_RED
        pygame.draw.rect(self.screen, b_col, m_rect, width=2, border_radius=12)

        title = "🏆 WSPANIAŁE ZWYCIĘSTWO! 🏆" if is_vic else "💀 PORAŻKA NA ARENIE 💀"
        self.screen.blit(self.font_title.render(title, True, b_col), (self.width // 2 - 180, m_rect.y + 25))

        if is_vic and self.session.active_enemy_template:
            r_str = f"Nagroda: +{self.session.active_enemy_template.reward_gold} 💰 Złota | +{self.session.active_enemy_template.reward_exp} EXP"
            self.screen.blit(self.font_bold.render(r_str, True, COLOR_YELLOW), (self.width // 2 - 150, m_rect.y + 75))
            self.screen.blit(self.font_small.render("Zadania zostały sprawdzone i zaktualizowane w Tawernie!", True, COLOR_GREEN), (self.width // 2 - 170, m_rect.y + 105))
        else:
            self.screen.blit(self.font_normal.render("Ledwo uszedłeś z życiem. Odwiedź Tawernę, aby uleczyć rany!", True, TEXT_WHITE), (self.width // 2 - 200, m_rect.y + 85))

        btn_hub = Button(
            pygame.Rect(self.width // 2 - 150, m_rect.y + 160, 300, 56),
            "Powrót do Tawerny / Areny",
            callback=self.on_return_hub_cb
        )
        btn_hub.accent_color = COLOR_GOLD
        btn_hub.draw(self.screen, self.font_bold)
        self.active_buttons.append(btn_hub)

    def _draw_toast(self):
        if self.message_toast and (time.time() - self.message_toast_time < 3.5):
            t_rect = pygame.Rect(self.width // 2 - 250, 670, 500, 40)
            pygame.draw.rect(self.screen, (24, 60, 35), t_rect, border_radius=6)
            pygame.draw.rect(self.screen, COLOR_GREEN, t_rect, width=1, border_radius=6)
            t_surf = self.font_bold.render(self.message_toast, True, COLOR_GOLD)
            self.screen.blit(t_surf, (self.width // 2 - t_surf.get_width() // 2, 680))
