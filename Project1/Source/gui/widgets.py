"""
Reusable cute & bright UI widgets for Pygame GUI:
- Tactile 3D Pill Button with drop shadow, glossy highlight, hover lift, and active state
- Segmented Mode Toggle (2.5D Cute Style vs 2D Algorithm Vis)
- Styled Card Panel & Badge helpers
- Cute Scrollable Stage Selector Dropdown with Chevron & Auto-scroll
- Multi-Algorithm Benchmark Comparison Modal
Assigned to: Member 4 (GUI & Visualization)
"""

from typing import Tuple, Callable, Optional, List, Dict, Any
import pygame


def draw_soft_shadow(
    surface: pygame.Surface,
    rect: pygame.Rect,
    radius: int = 12,
    offset: Tuple[int, int] = (0, 4),
    alpha: int = 38,
    spread: int = 2,
):
    """Draws a multi-layered soft pastel drop shadow underneath a rectangular element."""
    ox, oy = offset
    for layer in range(2):
        pad = spread * (layer + 1)
        sh_rect = pygame.Rect(
            rect.left + ox - pad // 2,
            rect.top + oy - pad // 2,
            rect.width + pad,
            rect.height + pad,
        )
        sh_surf = pygame.Surface((max(1, sh_rect.width), max(1, sh_rect.height)), pygame.SRCALPHA)
        layer_alpha = max(8, alpha // (layer + 1))
        pygame.draw.rect(
            sh_surf,
            (68, 52, 96, layer_alpha),
            sh_surf.get_rect(),
            border_radius=radius + layer,
        )
        surface.blit(sh_surf, sh_rect.topleft)


def draw_pastel_card(
    surface: pygame.Surface,
    rect: pygame.Rect,
    bg_color: Tuple[int, int, int] = (246, 242, 255),
    border_color: Tuple[int, int, int] = (222, 214, 240),
    radius: int = 14,
    shadow: bool = True,
):
    """Draws a rounded pastel card with a soft shadow and subtle top inner highlight."""
    if shadow:
        draw_soft_shadow(surface, rect, radius=radius, offset=(0, 3), alpha=28, spread=2)
    pygame.draw.rect(surface, bg_color, rect, border_radius=radius)
    # Glossy top highlight strip
    if rect.height > 16 and rect.width > 20:
        hi_rect = pygame.Rect(rect.left + 4, rect.top + 2, rect.width - 8, 5)
        hi_surf = pygame.Surface((hi_rect.width, hi_rect.height), pygame.SRCALPHA)
        pygame.draw.rect(hi_surf, (255, 255, 255, 150), hi_surf.get_rect(), border_radius=4)
        surface.blit(hi_surf, hi_rect.topleft)
    pygame.draw.rect(surface, border_color, rect, width=2, border_radius=radius)


class Button:
    """
    Cute, tactile 3D clickable pill button with soft shadow, bottom lip,
    glossy highlight, hover bounce, and active badge state.
    Fully backwards-compatible with original Button signature.
    """

    def __init__(
        self,
        rect: Tuple[int, int, int, int],
        text: str,
        on_click: Optional[Callable[[], None]] = None,
        bg_color: Tuple[int, int, int] = (124, 156, 255),
        hover_color: Tuple[int, int, int] = (144, 174, 255),
        text_color: Tuple[int, int, int] = (255, 255, 255),
        font_size: int = 15,
        shadow_color: Optional[Tuple[int, int, int]] = None,
        border_radius: int = 11,
        is_active: bool = False,
        subtitle: Optional[str] = None,
    ):
        self.rect = pygame.Rect(rect)
        self.text = text
        self.subtitle = subtitle
        self.on_click = on_click
        self.bg_color = bg_color
        self.hover_color = hover_color
        self.text_color = text_color
        self.shadow_color = shadow_color or tuple(max(0, c - 42) for c in bg_color)
        self.border_radius = border_radius
        self.is_active = is_active

        self.font = pygame.font.SysFont("Trebuchet MS, Verdana, Arial", font_size, bold=True)
        self.sub_font = pygame.font.SysFont("Trebuchet MS, Verdana, Arial", max(10, font_size - 4), bold=False)
        self.is_hovered = False
        self.is_pressed = False

    def update(self, mouse_pos: Tuple[int, int]):
        self.is_hovered = self.rect.collidepoint(mouse_pos)
        if not self.is_hovered:
            self.is_pressed = False

    def handle_event(self, event: pygame.event.Event) -> bool:
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.rect.collidepoint(event.pos):
                self.is_pressed = True
                if self.on_click is not None:
                    self.on_click()
                return True
        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            self.is_pressed = False
        return False

    def draw(self, surface: pygame.Surface):
        # Tactile vertical offset based on hover / press state
        lip_h = 3
        if self.is_pressed:
            y_off = 2
        elif self.is_hovered:
            y_off = -1
        else:
            y_off = 0

        # Soft ambient shadow below button
        draw_soft_shadow(
            surface,
            self.rect,
            radius=self.border_radius,
            offset=(0, 3),
            alpha=35 if self.is_hovered else 22,
            spread=2,
        )

        # 3D bottom lip (darker base)
        base_rect = pygame.Rect(
            self.rect.left,
            self.rect.top + lip_h,
            self.rect.width,
            self.rect.height - 1,
        )
        pygame.draw.rect(surface, self.shadow_color, base_rect, border_radius=self.border_radius)

        # Main button face
        face_rect = pygame.Rect(
            self.rect.left,
            self.rect.top + y_off,
            self.rect.width,
            self.rect.height - lip_h,
        )
        fill = self.hover_color if self.is_hovered else self.bg_color
        pygame.draw.rect(surface, fill, face_rect, border_radius=self.border_radius)

        # Top glossy shine bar
        if face_rect.width > 16 and face_rect.height > 12:
            shine_rect = pygame.Rect(
                face_rect.left + 5,
                face_rect.top + 3,
                face_rect.width - 10,
                max(3, face_rect.height // 4),
            )
            shine_surf = pygame.Surface((shine_rect.width, shine_rect.height), pygame.SRCALPHA)
            pygame.draw.rect(
                shine_surf,
                (255, 255, 255, 95 if self.is_hovered else 65),
                shine_surf.get_rect(),
                border_radius=max(2, self.border_radius - 4),
            )
            surface.blit(shine_surf, shine_rect.topleft)

        # Crisp border (gold/berry glow when active, otherwise subtle shade)
        if self.is_active:
            pygame.draw.rect(
                surface,
                (255, 230, 105),
                face_rect,
                width=2,
                border_radius=self.border_radius,
            )
        else:
            border_c = tuple(max(0, c - 25) for c in fill)
            pygame.draw.rect(
                surface,
                border_c,
                face_rect,
                width=1,
                border_radius=self.border_radius,
            )

        # Text rendering with subtle drop shadow for dark/colored buttons
        is_light_text = sum(self.text_color) > 550
        if self.subtitle:
            main_surf = self.font.render(self.text, True, self.text_color)
            sub_surf = self.sub_font.render(self.subtitle, True, self.text_color)
            main_rect = main_surf.get_rect(center=(face_rect.centerx, face_rect.centery - 5))
            sub_rect = sub_surf.get_rect(center=(face_rect.centerx, face_rect.centery + 8))
            if is_light_text:
                sh_surf = self.font.render(self.text, True, self.shadow_color)
                surface.blit(sh_surf, (main_rect.left, main_rect.top + 1))
            surface.blit(main_surf, main_rect)
            surface.blit(sub_surf, sub_rect)
        else:
            text_surf = self.font.render(self.text, True, self.text_color)
            text_rect = text_surf.get_rect(center=face_rect.center)
            if is_light_text:
                sh_surf = self.font.render(self.text, True, self.shadow_color)
                surface.blit(sh_surf, (text_rect.left, text_rect.top + 1))
            surface.blit(text_surf, text_rect)


class ModeToggleSwitch:
    """
    Cute segmented pill switch for toggling between:
    - '2.5D' (Cute 2.5D Isometric/Diorama Mode)
    - '2D'   (Algorithm Visualization 2D Grid Mode)
    """

    def __init__(
        self,
        rect: Tuple[int, int, int, int],
        mode: str = "2.5D",
        on_change: Optional[Callable[[str], None]] = None,
    ):
        self.rect = pygame.Rect(rect)
        self.mode = mode
        self.on_change = on_change
        self.font = pygame.font.SysFont("Trebuchet MS, Verdana, Arial", 13, bold=True)
        self.hovered_half: Optional[str] = None

    @property
    def left_rect(self) -> pygame.Rect:
        half_w = (self.rect.width - 8) // 2
        return pygame.Rect(self.rect.left + 4, self.rect.top + 4, half_w, self.rect.height - 8)

    @property
    def right_rect(self) -> pygame.Rect:
        half_w = (self.rect.width - 8) // 2
        return pygame.Rect(
            self.rect.left + 4 + half_w,
            self.rect.top + 4,
            self.rect.width - 8 - half_w,
            self.rect.height - 8,
        )

    def update(self, mouse_pos: Tuple[int, int]):
        if self.left_rect.collidepoint(mouse_pos):
            self.hovered_half = "2.5D"
        elif self.right_rect.collidepoint(mouse_pos):
            self.hovered_half = "2D"
        else:
            self.hovered_half = None

    def handle_event(self, event: pygame.event.Event) -> bool:
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.left_rect.collidepoint(event.pos):
                if self.mode != "2.5D":
                    self.mode = "2.5D"
                    if self.on_change:
                        self.on_change(self.mode)
                return True
            elif self.right_rect.collidepoint(event.pos):
                if self.mode != "2D":
                    self.mode = "2D"
                    if self.on_change:
                        self.on_change(self.mode)
                return True
        return False

    def draw(self, surface: pygame.Surface):
        # Track background
        draw_soft_shadow(surface, self.rect, radius=14, offset=(0, 2), alpha=24, spread=1)
        pygame.draw.rect(surface, (232, 224, 246), self.rect, border_radius=14)
        pygame.draw.rect(surface, (206, 194, 228), self.rect, width=2, border_radius=14)

        # Active pill indicator
        active_rect = self.left_rect if self.mode == "2.5D" else self.right_rect
        active_color = (255, 122, 152) if self.mode == "2.5D" else (92, 168, 250)
        active_shadow = (212, 78, 110) if self.mode == "2.5D" else (58, 124, 208)

        # Pill bottom lip + face
        lip = pygame.Rect(active_rect.left, active_rect.top + 2, active_rect.width, active_rect.height)
        pygame.draw.rect(surface, active_shadow, lip, border_radius=10)
        face = pygame.Rect(active_rect.left, active_rect.top, active_rect.width, active_rect.height - 2)
        pygame.draw.rect(surface, active_color, face, border_radius=10)

        # Shine on active pill
        shine = pygame.Rect(face.left + 6, face.top + 2, face.width - 12, 4)
        sh_surf = pygame.Surface((max(1, shine.width), max(1, shine.height)), pygame.SRCALPHA)
        pygame.draw.rect(sh_surf, (255, 255, 255, 90), sh_surf.get_rect(), border_radius=2)
        surface.blit(sh_surf, shine.topleft)

        # Labels
        c_left = (255, 255, 255) if self.mode == "2.5D" else (105, 92, 132)
        c_right = (255, 255, 255) if self.mode == "2D" else (105, 92, 132)

        lbl_left = self.font.render("2.5D Cute Block", True, c_left)
        lbl_right = self.font.render("2D Algo Vis", True, c_right)

        surface.blit(lbl_left, lbl_left.get_rect(center=self.left_rect.center))
        surface.blit(lbl_right, lbl_right.get_rect(center=self.right_rect.center))


class Dropdown:
    """
    Cute & bright pastel Dropdown selector with smooth scrollable popup list.
    Supports chevron indicator, mouse wheel scrolling, scrollbar dragging,
    and outside-click closing.
    """

    def __init__(
        self,
        rect: Tuple[int, int, int, int],
        items: List[str],
        selected_idx: int = 0,
        on_select: Optional[Callable[[int], None]] = None,
        max_visible_items: int = 7,
        item_height: int = 28,
        bg_color: Tuple[int, int, int] = (255, 255, 255),
        border_color: Tuple[int, int, int] = (220, 210, 238),
        text_color: Tuple[int, int, int] = (58, 46, 78),
        font_size: int = 13,
    ):
        self.rect = pygame.Rect(rect)
        self.items = list(items)
        self.selected_idx = max(0, min(selected_idx, len(items) - 1)) if items else 0
        self.on_select = on_select
        self.max_visible_items = max_visible_items
        self.item_height = item_height
        self.bg_color = bg_color
        self.border_color = border_color
        self.text_color = text_color
        self.font_size = font_size

        self.font = pygame.font.SysFont("Trebuchet MS, Verdana, Arial", font_size, bold=False)
        self.font_bold = pygame.font.SysFont("Trebuchet MS, Verdana, Arial", font_size, bold=True)
        self.font_tiny = pygame.font.SysFont("Trebuchet MS, Verdana, Arial", max(10, font_size - 2), bold=False)

        self.is_open = False
        self.is_hovered = False
        self.scroll_offset = 0  # index offset for scrolling
        self.hovered_item_idx: Optional[int] = None
        self.is_dragging_scrollbar = False
        self.scrollbar_drag_start_y = 0
        self.scrollbar_drag_start_offset = 0

    def set_rect(self, rect: Tuple[int, int, int, int]):
        self.rect = pygame.Rect(rect)

    def set_items(self, items: List[str], selected_idx: Optional[int] = None):
        self.items = list(items)
        if selected_idx is not None:
            self.selected_idx = max(0, min(selected_idx, len(self.items) - 1)) if self.items else 0
        elif self.selected_idx >= len(self.items):
            self.selected_idx = max(0, len(self.items) - 1)
        self.scroll_offset = max(0, min(self.scroll_offset, max(0, len(self.items) - self.max_visible_items)))

    @property
    def selected_text(self) -> str:
        if 0 <= self.selected_idx < len(self.items):
            return self.items[self.selected_idx]
        return "Select Stage"

    def get_popup_rect(self, surface_rect: Optional[pygame.Rect] = None) -> pygame.Rect:
        vis = min(len(self.items), self.max_visible_items)
        h = vis * self.item_height + 8
        w = max(self.rect.width, 220)
        x = self.rect.left
        y = self.rect.bottom + 4
        if surface_rect:
            if x + w > surface_rect.right - 8:
                x = surface_rect.right - w - 8
            if y + h > surface_rect.bottom - 10:
                y = self.rect.top - h - 4
        return pygame.Rect(x, y, w, h)

    def update(self, mouse_pos: Tuple[int, int]):
        self.is_hovered = self.rect.collidepoint(mouse_pos)
        if self.is_open:
            popup_rect = self.get_popup_rect()
            if popup_rect.collidepoint(mouse_pos):
                rel_y = mouse_pos[1] - (popup_rect.top + 4)
                idx = self.scroll_offset + rel_y // self.item_height
                if 0 <= idx < len(self.items):
                    self.hovered_item_idx = idx
                else:
                    self.hovered_item_idx = None
            else:
                self.hovered_item_idx = None

    def handle_event(self, event: pygame.event.Event, surface_rect: Optional[pygame.Rect] = None) -> bool:
        popup_rect = self.get_popup_rect(surface_rect)

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.is_open:
                if popup_rect.collidepoint(event.pos):
                    # Check if click is on scrollbar
                    has_scroll = len(self.items) > self.max_visible_items
                    sb_w = 14 if has_scroll else 0
                    if has_scroll and event.pos[0] >= popup_rect.right - sb_w - 4:
                        self.is_dragging_scrollbar = True
                        self.scrollbar_drag_start_y = event.pos[1]
                        self.scrollbar_drag_start_offset = self.scroll_offset
                        return True

                    # Click on an item
                    rel_y = event.pos[1] - (popup_rect.top + 4)
                    clicked_item = self.scroll_offset + rel_y // self.item_height
                    if 0 <= clicked_item < len(self.items):
                        self.selected_idx = clicked_item
                        self.is_open = False
                        if self.on_select:
                            self.on_select(self.selected_idx)
                        return True
                    return True

                elif self.rect.collidepoint(event.pos):
                    self.is_open = False
                    return True
                else:
                    # Clicked outside popup
                    self.is_open = False
                    return True
            else:
                if self.rect.collidepoint(event.pos):
                    self.is_open = True
                    # Scroll so selected item is visible
                    if self.selected_idx >= self.scroll_offset + self.max_visible_items:
                        self.scroll_offset = max(0, self.selected_idx - self.max_visible_items + 1)
                    elif self.selected_idx < self.scroll_offset:
                        self.scroll_offset = self.selected_idx
                    return True

        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            if self.is_dragging_scrollbar:
                self.is_dragging_scrollbar = False
                return True

        elif event.type == pygame.MOUSEMOTION:
            if self.is_open and self.is_dragging_scrollbar:
                has_scroll = len(self.items) > self.max_visible_items
                if has_scroll:
                    max_scroll = len(self.items) - self.max_visible_items
                    dy = event.pos[1] - self.scrollbar_drag_start_y
                    track_h = popup_rect.height - 12
                    step = track_h / max(1, max_scroll)
                    new_offset = int(self.scrollbar_drag_start_offset + dy / step)
                    self.scroll_offset = max(0, min(max_scroll, new_offset))
                return True

        elif event.type == getattr(pygame, "MOUSEWHEEL", None) and self.is_open:
            mouse_pos = pygame.mouse.get_pos()
            if popup_rect.collidepoint(mouse_pos):
                wy = getattr(event, "y", 0)
                max_scroll = max(0, len(self.items) - self.max_visible_items)
                if wy > 0:
                    self.scroll_offset = max(0, self.scroll_offset - 1)
                elif wy < 0:
                    self.scroll_offset = min(max_scroll, self.scroll_offset + 1)
                return True

        elif event.type == pygame.MOUSEBUTTONDOWN and self.is_open:
            if event.button == 4:  # Wheel up
                if popup_rect.collidepoint(event.pos):
                    self.scroll_offset = max(0, self.scroll_offset - 1)
                    return True
            elif event.button == 5:  # Wheel down
                if popup_rect.collidepoint(event.pos):
                    max_scroll = max(0, len(self.items) - self.max_visible_items)
                    self.scroll_offset = min(max_scroll, self.scroll_offset + 1)
                    return True

        return False

    def draw(self, surface: pygame.Surface):
        """Draws the closed dropdown button."""
        draw_soft_shadow(surface, self.rect, radius=8, offset=(0, 2), alpha=20, spread=1)

        bg = (252, 248, 255) if self.is_hovered or self.is_open else self.bg_color
        border_c = (200, 184, 232) if self.is_hovered or self.is_open else self.border_color
        pygame.draw.rect(surface, bg, self.rect, border_radius=8)
        pygame.draw.rect(surface, border_c, self.rect, width=1, border_radius=8)

        # Chevron indicator
        chev_char = "▲" if self.is_open else "▼"
        chev_surf = self.font_tiny.render(chev_char, True, (138, 122, 160))
        chev_rect = chev_surf.get_rect(center=(self.rect.right - 14, self.rect.centery))
        surface.blit(chev_surf, chev_rect)

        # Truncate text if needed
        avail_w = self.rect.width - 28
        txt = self.selected_text
        txt_surf = self.font_bold.render(txt, True, self.text_color)
        if txt_surf.get_width() > avail_w:
            while len(txt) > 3 and self.font_bold.render(txt + "...", True, self.text_color).get_width() > avail_w:
                txt = txt[:-1]
            txt_surf = self.font_bold.render(txt + "...", True, self.text_color)

        t_rect = txt_surf.get_rect(midleft=(self.rect.left + 8, self.rect.centery))
        surface.blit(txt_surf, t_rect)

    def draw_popup(self, surface: pygame.Surface):
        """Draws the floating dropdown menu list on top."""
        if not self.is_open or not self.items:
            return

        popup_rect = self.get_popup_rect(surface.get_rect())
        draw_soft_shadow(surface, popup_rect, radius=12, offset=(0, 4), alpha=45, spread=3)
        pygame.draw.rect(surface, (255, 255, 255), popup_rect, border_radius=12)
        pygame.draw.rect(surface, (216, 204, 236), popup_rect, width=2, border_radius=12)

        has_scroll = len(self.items) > self.max_visible_items
        sb_w = 12 if has_scroll else 0
        item_w = popup_rect.width - 12 - sb_w

        vis_count = min(len(self.items), self.max_visible_items)
        for i in range(vis_count):
            idx = self.scroll_offset + i
            if idx >= len(self.items):
                break
            iy = popup_rect.top + 4 + i * self.item_height
            i_rect = pygame.Rect(popup_rect.left + 6, iy, item_w, self.item_height - 2)

            is_cur = (idx == self.selected_idx)
            is_hov = (idx == self.hovered_item_idx)

            if is_cur:
                pygame.draw.rect(surface, (255, 238, 245), i_rect, border_radius=6)
                pygame.draw.rect(surface, (244, 182, 205), i_rect, width=1, border_radius=6)
            elif is_hov:
                pygame.draw.rect(surface, (244, 240, 255), i_rect, border_radius=6)

            col = (212, 68, 108) if is_cur else ((58, 46, 78) if is_hov else (88, 76, 108))
            font = self.font_bold if is_cur else self.font

            label = self.items[idx]
            avail = item_w - 20
            l_surf = font.render(label, True, col)
            if l_surf.get_width() > avail:
                short_lbl = label
                while len(short_lbl) > 3 and font.render(short_lbl + "...", True, col).get_width() > avail:
                    short_lbl = short_lbl[:-1]
                l_surf = font.render(short_lbl + "...", True, col)

            if is_cur:
                bullet = self.font_tiny.render("●", True, (212, 68, 108))
                surface.blit(bullet, (i_rect.left + 6, i_rect.centery - bullet.get_height() // 2))
                surface.blit(l_surf, (i_rect.left + 18, i_rect.centery - l_surf.get_height() // 2))
            else:
                surface.blit(l_surf, (i_rect.left + 8, i_rect.centery - l_surf.get_height() // 2))

        # Scrollbar
        if has_scroll:
            track_rect = pygame.Rect(popup_rect.right - 12, popup_rect.top + 6, 6, popup_rect.height - 12)
            pygame.draw.rect(surface, (240, 236, 248), track_rect, border_radius=3)
            max_scroll = len(self.items) - self.max_visible_items
            thumb_h = max(16, int(track_rect.height * (self.max_visible_items / len(self.items))))
            thumb_y = track_rect.top + int((track_rect.height - thumb_h) * (self.scroll_offset / max(1, max_scroll)))
            thumb_rect = pygame.Rect(track_rect.left, thumb_y, track_rect.width, thumb_h)
            pygame.draw.rect(surface, (188, 172, 214), thumb_rect, border_radius=3)


class BenchmarkModal:
    """
    Cute & bright pastel comparison modal for 4 search algorithms:
    - Side-by-side comparison table (BFS, DFS, UCS, A*)
    - Metric columns: Status, Solution Moves, Cost, Time (ms), Peak Memory (KB), Nodes (Expanded / Generated)
    - Trophies / badges for: ⚡ Fastest, 🏆 Fewest Moves, 🎯 Efficient Search
    - One-click [▶ Replay] button to visualize any algorithm's solution path immediately!
    - Close button and outside-click dismiss.
    """

    def __init__(
        self,
        stage_name: str,
        results: List[Dict[str, Any]],
        on_replay: Optional[Callable[[str], None]] = None,
        on_close: Optional[Callable[[], None]] = None,
    ):
        self.stage_name = stage_name
        self.results = results
        self.on_replay = on_replay
        self.on_close = on_close

        self.font_title = pygame.font.SysFont("Trebuchet MS, Verdana, Arial", 20, bold=True)
        self.font_section = pygame.font.SysFont("Trebuchet MS, Verdana, Arial", 14, bold=True)
        self.font_text = pygame.font.SysFont("Trebuchet MS, Verdana, Arial", 13, bold=False)
        self.font_bold = pygame.font.SysFont("Trebuchet MS, Verdana, Arial", 13, bold=True)
        self.font_metric = pygame.font.SysFont("Consolas, Courier New, Monospace", 12, bold=True)
        self.font_tiny = pygame.font.SysFont("Trebuchet MS, Verdana, Arial", 11, bold=False)
        self.font_badge = pygame.font.SysFont("Trebuchet MS, Verdana, Arial", 10, bold=True)

        self.replay_buttons: List[Tuple[str, Button]] = []
        self.btn_close: Optional[Button] = None
        self.btn_x: Optional[Button] = None
        self.modal_rect = pygame.Rect(0, 0, 840, 480)

        self._analyze_results()

    def _analyze_results(self):
        """Calculates best metrics among solved runs for trophy highlighting."""
        successful = [r for r in self.results if r.get("success")]
        self.best_time = min((r["time_ms"] for r in successful), default=None)
        self.best_moves = min((r["moves"] for r in successful if r.get("moves") is not None), default=None)
        self.best_nodes = min((r["expanded_nodes"] for r in successful), default=None)
        self.best_mem = min((r["peak_mem_kb"] for r in successful), default=None)

        if successful:
            def score(r):
                m_score = (r.get("moves") or 9999) * 10
                t_score = r.get("time_ms", 9999)
                return m_score + t_score
            winner = min(successful, key=score)
            self.winner_algo = winner["algorithm"]
            moves_str = f"{winner.get('moves')} moves" if winner.get("moves") else ""
            time_str = f"{winner.get('time_ms', 0):.2f} ms"
            self.winner_summary = f"🌟 Overall Winner: {self.winner_algo} found an optimal path ({moves_str}) in just {time_str}!"
        else:
            self.winner_algo = None
            self.winner_summary = "⚠️ None of the algorithms found a solution within the search limits."

    def _layout(self, screen_rect: pygame.Rect):
        mw = min(860, screen_rect.width - 40)
        mh = min(490, screen_rect.height - 40)
        self.modal_rect = pygame.Rect(
            screen_rect.centerx - mw // 2,
            screen_rect.centery - mh // 2,
            mw,
            mh,
        )

        # X close button top right
        self.btn_x = Button(
            rect=(self.modal_rect.right - 42, self.modal_rect.top + 14, 28, 28),
            text="✕",
            on_click=self.on_close,
            bg_color=(255, 238, 242),
            hover_color=(255, 218, 226),
            shadow_color=(235, 185, 198),
            text_color=(198, 52, 82),
            font_size=13,
            border_radius=8,
        )

        # Bottom Close button
        self.btn_close = Button(
            rect=(self.modal_rect.centerx - 70, self.modal_rect.bottom - 46, 140, 32),
            text="Close (ESC)",
            on_click=self.on_close,
            bg_color=(240, 234, 248),
            hover_color=(248, 244, 255),
            shadow_color=(206, 196, 222),
            text_color=(68, 56, 88),
            font_size=13,
            border_radius=10,
        )

        # Replay buttons for each row
        self.replay_buttons = []
        table_top = self.modal_rect.top + 72
        row_h = 44
        for i, res in enumerate(self.results):
            ry = table_top + 34 + i * row_h
            algo = res["algorithm"]
            can_replay = res.get("success") and self.on_replay is not None
            if can_replay:
                btn_r = Button(
                    rect=(self.modal_rect.right - 105, ry + 6, 76, 28),
                    text="▶ Replay",
                    on_click=lambda a=algo: self._handle_replay(a),
                    bg_color=(88, 206, 164),
                    hover_color=(108, 222, 182),
                    shadow_color=(56, 164, 126),
                    text_color=(255, 255, 255),
                    font_size=11,
                    border_radius=8,
                )
                self.replay_buttons.append((algo, btn_r))

    def _handle_replay(self, algo_name: str):
        if self.on_replay:
            self.on_replay(algo_name)
        if self.on_close:
            self.on_close()

    def update(self, mouse_pos: Tuple[int, int]):
        if self.btn_x:
            self.btn_x.update(mouse_pos)
        if self.btn_close:
            self.btn_close.update(mouse_pos)
        for _, btn in self.replay_buttons:
            btn.update(mouse_pos)

    def handle_event(self, event: pygame.event.Event) -> bool:
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            if self.on_close:
                self.on_close()
            return True

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if not self.modal_rect.collidepoint(event.pos):
                if self.on_close:
                    self.on_close()
                return True

        if self.btn_x and self.btn_x.handle_event(event):
            return True
        if self.btn_close and self.btn_close.handle_event(event):
            return True
        for _, btn in self.replay_buttons:
            if btn.handle_event(event):
                return True

        if event.type in (pygame.MOUSEBUTTONDOWN, pygame.MOUSEBUTTONUP):
            return True
        return False

    def draw(self, surface: pygame.Surface):
        self._layout(surface.get_rect())

        # 1. Dark pastel backdrop scrim
        backdrop = pygame.Surface((surface.get_width(), surface.get_height()), pygame.SRCALPHA)
        backdrop.fill((34, 26, 48, 175))
        surface.blit(backdrop, (0, 0))

        # 2. Main modal card
        draw_pastel_card(
            surface,
            self.modal_rect,
            bg_color=(255, 252, 250),
            border_color=(220, 206, 238),
            radius=20,
            shadow=True,
        )

        # 3. Header
        t_surf = self.font_title.render("🏆 Algorithm Benchmark Comparison", True, (216, 68, 108))
        surface.blit(t_surf, (self.modal_rect.left + 24, self.modal_rect.top + 18))
        sub_txt = f"Stage: {self.stage_name}  |  Performance Evaluation across 4 Search Strategies"
        sub_surf = self.font_tiny.render(sub_txt, True, (132, 118, 150))
        surface.blit(sub_surf, (self.modal_rect.left + 24, self.modal_rect.top + 46))

        if self.btn_x:
            self.btn_x.draw(surface)

        # 4. Table Layout
        table_top = self.modal_rect.top + 72
        tbl_x = self.modal_rect.left + 20
        tbl_w = self.modal_rect.width - 40

        # Table Header Row
        th_rect = pygame.Rect(tbl_x, table_top, tbl_w, 32)
        pygame.draw.rect(surface, (244, 238, 252), th_rect, border_radius=8)

        cols = [
            ("Algorithm", 110),
            ("Status", 95),
            ("Moves", 80),
            ("Cost", 70),
            ("Time", 100),
            ("Memory", 95),
            ("Nodes (Exp / Gen)", 140),
            ("Action", 85),
        ]

        cx = tbl_x + 12
        for title, col_w in cols:
            hdr_surf = self.font_badge.render(title.upper(), True, (120, 105, 142))
            surface.blit(hdr_surf, (cx, th_rect.centery - hdr_surf.get_height() // 2))
            cx += col_w

        algo_colors = {
            "BFS": ((124, 156, 255), (235, 242, 255), (60, 92, 200)),
            "DFS": ((176, 142, 248), (244, 238, 255), (118, 78, 198)),
            "UCS": ((245, 185, 75), (255, 248, 230), (160, 108, 18)),
            "A*": ((72, 198, 152), (232, 252, 244), (24, 128, 88)),
        }

        # Table Data Rows
        row_h = 44
        for i, res in enumerate(self.results):
            ry = table_top + 34 + i * row_h
            r_rect = pygame.Rect(tbl_x, ry, tbl_w, row_h - 4)

            row_bg = (255, 255, 255) if i % 2 == 0 else (250, 248, 254)
            pygame.draw.rect(surface, row_bg, r_rect, border_radius=8)
            pygame.draw.rect(surface, (236, 230, 246), r_rect, width=1, border_radius=8)

            cx = tbl_x + 12
            algo = res["algorithm"]
            badge_border, badge_bg, badge_txt = algo_colors.get(algo, ((180, 180, 180), (240, 240, 240), (80, 80, 80)))

            # Col 1: Algorithm Pill Badge
            pill_rect = pygame.Rect(cx, ry + 7, 78, 24)
            pygame.draw.rect(surface, badge_bg, pill_rect, border_radius=6)
            pygame.draw.rect(surface, badge_border, pill_rect, width=1, border_radius=6)
            a_surf = self.font_bold.render(algo, True, badge_txt)
            surface.blit(a_surf, a_surf.get_rect(center=pill_rect.center))
            cx += 110

            # Col 2: Status
            ok = res.get("success", False)
            st_text = "✓ Solved" if ok else "✗ Failed"
            st_col = (32, 142, 86) if ok else (196, 48, 74)
            st_bg = (232, 250, 240) if ok else (255, 234, 238)
            st_pill = pygame.Rect(cx, ry + 8, 76, 22)
            pygame.draw.rect(surface, st_bg, st_pill, border_radius=6)
            st_surf = self.font_badge.render(st_text, True, st_col)
            surface.blit(st_surf, st_surf.get_rect(center=st_pill.center))
            cx += 95

            # Col 3: Moves
            moves = res.get("moves")
            m_str = f"{moves}" if (ok and moves is not None) else "-"
            m_surf = self.font_metric.render(m_str, True, (58, 46, 78))
            surface.blit(m_surf, (cx, ry + 12))
            if ok and moves is not None and self.best_moves is not None and moves == self.best_moves:
                t_badge = self.font_badge.render("★ BEST", True, (216, 68, 108))
                surface.blit(t_badge, (cx + m_surf.get_width() + 6, ry + 13))
            cx += 80

            # Col 4: Cost
            cost = res.get("cost")
            c_str = f"{cost:.1f}" if (ok and cost is not None) else "-"
            c_surf = self.font_metric.render(c_str, True, (58, 46, 78))
            surface.blit(c_surf, (cx, ry + 12))
            cx += 70

            # Col 5: Time (ms)
            t_ms = res.get("time_ms", 0.0)
            t_str = f"{t_ms:.2f} ms"
            t_surf = self.font_metric.render(t_str, True, (58, 46, 78))
            surface.blit(t_surf, (cx, ry + 12))
            if ok and self.best_time is not None and abs(t_ms - self.best_time) < 1e-3:
                f_badge = self.font_badge.render("⚡ FAST", True, (188, 130, 24))
                surface.blit(f_badge, (cx + t_surf.get_width() + 6, ry + 13))
            cx += 100

            # Col 6: Peak Memory
            mem = res.get("peak_mem_kb", 0.0)
            mem_str = f"{mem:.1f} KB"
            mem_surf = self.font_metric.render(mem_str, True, (58, 46, 78))
            surface.blit(mem_surf, (cx, ry + 12))
            cx += 95

            # Col 7: Nodes (Exp / Gen)
            exp = res.get("expanded_nodes", 0)
            gen = res.get("generated_nodes", 0)
            nod_str = f"{exp} / {gen}"
            nod_surf = self.font_metric.render(nod_str, True, (58, 46, 78))
            surface.blit(nod_surf, (cx, ry + 12))
            if ok and self.best_nodes is not None and exp == self.best_nodes:
                e_badge = self.font_badge.render("🎯 MIN", True, (24, 138, 92))
                surface.blit(e_badge, (cx + nod_surf.get_width() + 6, ry + 13))

        # 5. Draw Replay Buttons
        for _, btn in self.replay_buttons:
            btn.draw(surface)

        # 6. Winner Summary Card
        sum_y = table_top + 34 + len(self.results) * row_h + 8
        sum_rect = pygame.Rect(tbl_x, sum_y, tbl_w, 42)
        pygame.draw.rect(surface, (255, 245, 238), sum_rect, border_radius=10)
        pygame.draw.rect(surface, (248, 218, 204), sum_rect, width=1, border_radius=10)
        sum_surf = self.font_bold.render(self.winner_summary, True, (188, 72, 92))
        surface.blit(sum_surf, sum_surf.get_rect(center=sum_rect.center))

        # 7. Bottom Close Button
        if self.btn_close:
            self.btn_close.draw(surface)
