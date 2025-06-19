"""UI module for warehouse simulator with Help panel, inbound/outbound dialogs, bot add/ove buttons and
preference‑based colour mapping. Assumes existence of:
    * config.py – geometry + colour constants
    * state.py  – SimulationState class holding shared flags / queues
    * grid.py   – Grid object exposing width/height + get_cell()
    * item.py   – Item class (code, preference)
The main loop must create UI(grid, bots, state) and call ui.handle_event(event) and ui.draw(screen) each frame.
"""
from __future__ import annotations
import pygame
import config
from state import SimulationState
from item import Item
from typing import List, Callable, Optional, Tuple

# ---------------------------------------------------------------------------
# Helper UI components
# ---------------------------------------------------------------------------
class Button:
    """Simple rectangular button with hover/press handling."""

    def __init__(self, rect: pygame.Rect, text: str, callback: Callable[[], None], *, font: pygame.font.Font):
        self.rect = rect
        self.text = text
        self.callback = callback
        self.font = font
        self.hover = False

    def handle_event(self, event: pygame.event.Event):
        if event.type == pygame.MOUSEMOTION:
            self.hover = self.rect.collidepoint(event.pos)
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.hover:
                self.callback()

    def draw(self, surface: pygame.Surface):
        base_colour = (180, 180, 180)
        hover_colour = (230, 230, 230)
        colour = hover_colour if self.hover else base_colour
        pygame.draw.rect(surface, colour, self.rect, border_radius=4)
        pygame.draw.rect(surface, (50, 50, 50), self.rect, 1, border_radius=4)
        label = self.font.render(self.text, True, (0, 0, 0))
        label_rect = label.get_rect(center=self.rect.center)
        surface.blit(label, label_rect)


class InputBox:
    """Single‑line text input box; optionally numeric‑only."""

    def __init__(self, rect: pygame.Rect, *, numeric: bool = False, max_len: int | None = None,
              font: pygame.font.Font):                                    # ← 추가
        self.rect = rect
        self.font = font
        self.numeric = numeric
        self.text: str = ""
        self.max_len = max_len
        self.active: bool = False
        self.hover: bool = False

    def handle_event(self, event: pygame.event.Event):
        if event.type == pygame.MOUSEMOTION:
            self.hover = self.rect.collidepoint(event.pos)
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            self.active = self.hover
        elif event.type == pygame.KEYDOWN and self.active:
            if event.key == pygame.K_RETURN:
                # finished editing handled by dialog
                pass
            elif event.key == pygame.K_BACKSPACE:
                self.text = self.text[:-1]
            else:
                char = event.unicode
                if self.numeric and not char.isdigit():
                    return
                # rudimentary length cap for aesthetics
                if self.max_len is None or len(self.text) < self.max_len:
                    self.text += char

    def draw(self, surface: pygame.Surface):
        border_colour = (0, 120, 255) if self.active else (100, 100, 100)
        pygame.draw.rect(surface, (255, 255, 255), self.rect, border_radius=3)
        pygame.draw.rect(surface, border_colour, self.rect, 2, border_radius=3)
        txt_surf = self.font.render(self.text or " ", True, (0, 0, 0))
        txt_rect = txt_surf.get_rect(midleft=(self.rect.x + 4, self.rect.centery))
        surface.blit(txt_surf, txt_rect)

    def get_value(self) -> str:
        return self.text.strip()


class Dialog:
    """Modal dialog with two input boxes (code + quantity) and OK/Cancel buttons."""

    def __init__(self, title: str, ok_callback: Callable[[str, int], None], font: pygame.font.Font):
        self.title = title
        self.ok_callback = ok_callback
        # Dialog geometry (fixed size)
        self.width, self.height = 300, 180
        self.rect = pygame.Rect(0, 0, self.width, self.height)
        # Will be centered later in draw()
        self.font = font
        self.code_box = InputBox(pygame.Rect(0, 0, 180, 28), font=font, max_len=7)
        self.qty_box = InputBox(pygame.Rect(0, 0, 80, 28), numeric=True, font=font)
        # Buttons
        self.buttons: List[Button] = []
        # Filled in layout()
        self._build_buttons()

    def _build_buttons(self):
        btn_font = self.font
        ok_rect = pygame.Rect(0, 0, 80, 30)
        cancel_rect = pygame.Rect(0, 0, 80, 30)
        self.ok_button = Button(ok_rect, "OK", self._on_ok, font=btn_font)
        self.cancel_button = Button(cancel_rect, "Cancel", self._on_cancel, font=btn_font)
        self.buttons = [self.ok_button, self.cancel_button]

    def _on_ok(self):
        code = self.code_box.get_value()
        qty_text = self.qty_box.get_value()
        try:
            qty = int(qty_text)
        except ValueError:
            qty = 0
        if code and qty > 0:
            self.ok_callback(code, qty)
        self.close()

    def _on_cancel(self):
        self.close()

    def close(self):
        # External owner should set dialog reference to None
        self._closing = True

    # ---------------- Event / Draw ----------------
    def handle_event(self, event: pygame.event.Event):
        if getattr(self, "_closing", False):
            return
        self.code_box.handle_event(event)
        self.qty_box.handle_event(event)
        for btn in self.buttons:
            btn.handle_event(event)

    def draw(self, screen: pygame.Surface):
        if getattr(self, "_closing", False):
            return
        # Center dialog each frame (in case window resized)
        win_rect = screen.get_rect()
        self.rect.center = win_rect.center
        # Backdrop (semi‑transparent)
        overlay = pygame.Surface(win_rect.size, pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 160))
        screen.blit(overlay, (0, 0))
        # Dialog background
        pygame.draw.rect(screen, (240, 240, 240), self.rect, border_radius=6)
        pygame.draw.rect(screen, (80, 80, 80), self.rect, 2, border_radius=6)
        # Title
        title_surf = self.font.render(self.title, True, (0, 0, 0))
        title_rect = title_surf.get_rect(center=(self.rect.centerx, self.rect.y + 20))
        screen.blit(title_surf, title_rect)
        # Layout input boxes
        self.code_box.rect.topleft = (self.rect.x + 20, self.rect.y + 60)
        self.qty_box.rect.topleft = (self.rect.x + 20, self.rect.y + 100)
        self.code_box.draw(screen)
        self.qty_box.draw(screen)
        # Labels
        label_code = self.font.render("Item Code", True, (0, 0, 0))
        screen.blit(label_code, (self.code_box.rect.right + 10, self.code_box.rect.y + 5))
        label_qty = self.font.render("Qty", True, (0, 0, 0))
        screen.blit(label_qty, (self.qty_box.rect.right + 10, self.qty_box.rect.y + 5))
        # Layout buttons
        self.ok_button.rect.bottomright = (self.rect.right - 20, self.rect.bottom - 20)
        self.cancel_button.rect.bottomright = (self.ok_button.rect.left - 10, self.rect.bottom - 20)
        for btn in self.buttons:
            btn.draw(screen)

    # Dialog owner checks this to know if closed
    @property
    def closed(self) -> bool:
        return getattr(self, "_closing", False)


class HelpOverlay:
    """Displays help text until closed."""

    def __init__(self, font: pygame.font.Font):
        self.font = font
        self.visible = False
        self.lines = [
            "[P]  : Toggle path display",
            "[A]  : Automatic mode",
            "[M]  : Manual mode",
            "[B]  : Add bot (or use +Bot button)",
            "[R]  : Remove bot (or use -Bot button)",
            "Click inbound : add items",
            "Click storage : view preferences",
        ]

    def toggle(self):
        self.visible = not self.visible

    def draw(self, screen: pygame.Surface):
        if not self.visible:
            return
        win = screen.get_rect()

        # ---- 패널 위치·크기 ----
        width, height = 260, 160
        panel = pygame.Rect(win.right - width - 20,   # 오른쪽 여백 20
                            win.bottom - height - 20, # 하단  여백 20
                            width, height)

        # ---- 배경 & 테두리 ----
        pygame.draw.rect(screen, (30, 30, 30, 200), panel, border_radius=6)
        pygame.draw.rect(screen, (200, 200, 200), panel, 1, border_radius=6)

        # ---- 텍스트 ----
        y = panel.y + 12
        for ln in self.lines:
            surf = self.font.render(ln, True, (255, 255, 255))
            screen.blit(surf, (panel.x + 12, y))
            y += 24
        tip = self.font.render("Click Help to close", True, (180, 180, 180))
        screen.blit(tip, (panel.x + 12, panel.bottom - 28))


# ---------------------------------------------------------------------------
# UI main class
# ---------------------------------------------------------------------------
class UI:
    def __init__(self, grid, bots, state: SimulationState):
        pygame.font.init()
        self.grid = grid
        self.bots = bots
        self.state = state
        self.font = pygame.font.SysFont(None, 20)
        self.large_font = pygame.font.SysFont(None, 24)
        self.help_overlay = HelpOverlay(self.large_font)
        # Buttons (Help, +Bot, -Bot)
        self.buttons: List[Button] = []
        self._build_buttons()
        # Dialogs
        self.active_dialog: Optional[Dialog] = None
        # Selected cell for preference view
        self.selected_cell = None

    # ------------------------------------------------------------------
    # Buttons construction
    def _build_buttons(self):
        button_w, button_h = 80, 30
        # Place buttons at right panel region (grid width * spacing + margin)
        panel_x = self.grid.width * config.CELL_SPACING + 20
        y = 20
        # Help
        help_btn_rect = pygame.Rect(panel_x, y, button_w, button_h)
        help_btn = Button(help_btn_rect, "Help", self.help_overlay.toggle, font=self.font)
        y += button_h + 10
        # Add bot
        add_btn_rect = pygame.Rect(panel_x, y, button_w, button_h)
        add_bot_btn = Button(add_btn_rect, "+ Bot", self._on_add_bot, font=self.font)
        y += button_h + 10
        # Remove bot
        rm_btn_rect = pygame.Rect(panel_x, y, button_w, button_h)
        rm_bot_btn = Button(rm_btn_rect, "- Bot", self._on_remove_bot, font=self.font)
        y += button_h + 10
        # Auto inbound toggle
        auto_in_rect = pygame.Rect(panel_x, y, button_w, button_h)
        auto_in_btn = Button(auto_in_rect, "Auto In", self._on_auto_inbound_toggle, font=self.font)
        y += button_h + 10
        # Auto outbound toggle
        auto_out_rect = pygame.Rect(panel_x, y, button_w, button_h)
        auto_out_btn = Button(auto_out_rect, "Auto Out", self._on_auto_outbound_toggle, font=self.font)
        self.buttons = [help_btn, add_bot_btn, rm_bot_btn, auto_in_btn, auto_out_btn]

    # Callback implementations
    def _on_add_bot(self):
        self.state.request_add_bot = True

    def _on_remove_bot(self):
        self.state.request_remove_bot = True

    def _on_auto_inbound_toggle(self):
        self.state.auto_inbound = not self.state.auto_inbound

    def _on_auto_outbound_toggle(self):
        self.state.auto_outbound = not self.state.auto_outbound

    # ------------------------------------------------------------------
    # Event handling
    def handle_event(self, event: pygame.event.Event):
        # First, if dialog active, forward exclusively
        if self.active_dialog:
            self.active_dialog.handle_event(event)
            if self.active_dialog.closed:
                self.active_dialog = None
            return  # while dialog open ignore other events
        # Help overlay reacts to help button only (already toggled)
        # Buttons
        for btn in self.buttons:
            btn.handle_event(event)
        # Grid interactions
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mx, my = event.pos
            grid_x = mx // config.CELL_SPACING
            grid_y = my // config.CELL_SPACING
            if 0 <= grid_x < self.grid.width and 0 <= grid_y < self.grid.height:
                cell = self.grid.get_cell(grid_x, grid_y)
                if cell.type == "inbound":
                    # Open inbound dialog
                    self._open_inbound_dialog(cell)
                elif cell.type == "storage":
                    self.selected_cell = cell
                else:
                    self.selected_cell = None
        # Keyboard shortcuts still handled outside (main loop) for mode toggles/path etc.

    # ------------------------------------------------------------------
    # Dialog open helpers
    def _open_inbound_dialog(self, cell):
        def _ok(code: str, qty: int):
            for _ in range(qty):
                cell.add_item(Item(code))
        self.active_dialog = Dialog("Inbound: Add Items", _ok, font=self.large_font)

    def _open_outbound_dialog(self):
        def _ok(code: str, qty: int):
            self.state.manual_requests.append((code, qty))
            self.state.auto_mode = False  # ensure manual mode
        self.active_dialog = Dialog("Outbound: Request", _ok, font=self.large_font)

    # ------------------------------------------------------------------
    # Drawing helper
    def _pref_to_colour(self, pref: int) -> Tuple[int, int, int]:
        # Map 1..100 → red→yellow→green via linear HSV hue mapping (0°..120°)
        import colorsys
        norm = max(0.0, min(1.0, (pref - 1) / 99))
        h = (120 * norm) / 360.0  # convert deg→0..1
        r, g, b = colorsys.hsv_to_rgb(h, 1.0, 1.0)
        return int(r * 255), int(g * 255), int(b * 255)

    # ------------------------------------------------------------------
    # Main draw
    def draw(self, screen: pygame.Surface):
        # Clear
        screen.fill(config.BACKGROUND_COLOR)
        # Draw cells
        for x in range(self.grid.width):
            for y in range(self.grid.height):
                cell = self.grid.get_cell(x, y)
                if cell.type == "inbound":
                    colour = config.INBOUND_COLOR
                elif cell.type == "outbound":
                    colour = config.OUTBOUND_COLOR
                else:
                    colour = config.CELL_COLOR
                rect = pygame.Rect(x * config.CELL_SPACING, y * config.CELL_SPACING, config.CELL_SIZE, config.CELL_SIZE)
                # If storage cell and has items, blend with top item's preference colour
                if cell.type == "storage" and cell.items:
                    colour = self._pref_to_colour(cell.items[0].preference)
                pygame.draw.rect(screen, colour, rect)
                pygame.draw.rect(screen, (50, 50, 50), rect, 1)

        # Highlight selected storage cell
        if self.selected_cell:
            srect = pygame.Rect(self.selected_cell.x * config.CELL_SPACING, self.selected_cell.y * config.CELL_SPACING,
                                 config.CELL_SIZE, config.CELL_SIZE)
            pygame.draw.rect(screen, (255, 255, 0), srect, 3)
            # Draw preference panel for selected cell (top/bottom 10)
            self._draw_preference_panel(screen)

        # Draw bots
        for bot in self.bots:
            bx = bot.pos[0] * config.CELL_SPACING
            by = bot.pos[1] * config.CELL_SPACING
            bot_rect = pygame.Rect(bx, by, config.CELL_SIZE, config.CELL_SIZE)
            bot_surf = pygame.Surface((config.CELL_SIZE, config.CELL_SIZE), pygame.SRCALPHA)
            bot_surf.fill((*config.BOT_COLOR, 128))
            screen.blit(bot_surf, bot_rect)
            # Bot ID label
            id_surf = self.font.render(bot.bot_id, True, (0, 0, 0))
            screen.blit(id_surf, (bx + 4, by + 4))
            # Path display
            if bot.show_path and bot.target_path:
                pts = [(bot.pos[0] * config.CELL_SPACING + config.CELL_SIZE // 2,
                        bot.pos[1] * config.CELL_SPACING + config.CELL_SIZE // 2)]
                for px, py in bot.target_path:
                    pts.append((px * config.CELL_SPACING + config.CELL_SIZE // 2,
                                 py * config.CELL_SPACING + config.CELL_SIZE // 2))
                pygame.draw.lines(screen, config.PATH_COLOR, False, pts, 2)

        # Draw side buttons
        for btn in self.buttons:
            btn.draw(screen)

        # Draw help overlay (may cover whole screen)
        self.help_overlay.draw(screen)
        # Draw active dialog on top
        if self.active_dialog:
            self.active_dialog.draw(screen)

    # ------------------------------------------------------------------
    def _draw_preference_panel(self, screen: pygame.Surface):
        cell = self.selected_cell
        if not cell or cell.type != "storage":
            return
        sorted_items = sorted(cell.items, key=lambda it: it.preference, reverse=True)
        top_items = sorted_items[:10]
        
        remain = len(sorted_items) - 10          # 10개 초과분
        if remain > 0:
            slice_ = sorted_items[-min(remain, 10):]  # 남은 아이템 최대 10개
            bottom_items = list(reversed(slice_))     # 낮은 선호도부터 표시
        else:
            bottom_items = []
        # Panel origin (right side)
        panel_x = self.grid.width * config.CELL_SPACING + 20
        panel_y = 200
        size = 18
        for i, item in enumerate(top_items):
            colour = self._pref_to_colour(item.preference)
            rect = pygame.Rect(panel_x + i * (size + 4), panel_y, size, size)
            pygame.draw.rect(screen, colour, rect)
            pygame.draw.rect(screen, (30, 30, 30), rect, 1)
        for i, item in enumerate(bottom_items):
            colour = self._pref_to_colour(item.preference)
            rect = pygame.Rect(panel_x + i * (size + 4), panel_y + size + 6, size, size)
            pygame.draw.rect(screen, colour, rect)
            pygame.draw.rect(screen, (30, 30, 30), rect, 1)

