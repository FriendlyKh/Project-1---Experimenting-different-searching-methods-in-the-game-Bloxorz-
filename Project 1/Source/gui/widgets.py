"""
Reusable UI widgets for Pygame GUI: Button, Label, and Panel.
Assigned to: Member 4 (GUI & Visualization)
"""

from typing import Tuple, Callable, Optional
import pygame


class Button:
    """
    Interactive clickable button with hover state.
    """

    def __init__(
        self,
        rect: Tuple[int, int, int, int],
        text: str,
        on_click: Optional[Callable[[], None]] = None,
        bg_color: Tuple[int, int, int] = (60, 65, 85),
        hover_color: Tuple[int, int, int] = (85, 95, 125),
        text_color: Tuple[int, int, int] = (255, 255, 255),
        font_size: int = 18,
    ):
        self.rect = pygame.Rect(rect)
        self.text = text
        self.on_click = on_click
        self.bg_color = bg_color
        self.hover_color = hover_color
        self.text_color = text_color
        self.font = pygame.font.SysFont("Arial", font_size, bold=True)
        self.is_hovered = False

    def update(self, mouse_pos: Tuple[int, int]):
        self.is_hovered = self.rect.collidepoint(mouse_pos)

    def handle_event(self, event: pygame.event.Event) -> bool:
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.is_hovered and self.on_click is not None:
                self.on_click()
                return True
        return False

    def draw(self, surface: pygame.Surface):
        color = self.hover_color if self.is_hovered else self.bg_color
        # Draw rounded rectangle
        pygame.draw.rect(surface, color, self.rect, border_radius=6)
        pygame.draw.rect(surface, (120, 130, 160), self.rect, width=1, border_radius=6)

        text_surf = self.font.render(self.text, True, self.text_color)
        text_rect = text_surf.get_rect(center=self.rect.center)
        surface.blit(text_surf, text_rect)
