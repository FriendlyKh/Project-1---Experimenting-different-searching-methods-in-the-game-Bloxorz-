"""
Reusable cute & bright UI widgets for Pygame GUI:
- Tactile 3D Pill Button with drop shadow, glossy highlight, hover lift, and active state
- Segmented Mode Toggle (2.5D Cute Style vs 2D Algorithm Vis)
- Styled Card Panel & Badge helpers
Assigned to: Member 4 (GUI & Visualization)
"""

from typing import Tuple, Callable, Optional, List
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
        sh_surf = pygame.Surface(( max(1, sh_rect.width), max(1, sh_rect.height) ), pygame.SRCALPHA)
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