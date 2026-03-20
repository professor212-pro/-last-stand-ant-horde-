from __future__ import annotations

from dataclasses import dataclass
from typing import Tuple

import pygame


@dataclass
class Player:
    pos: pygame.Vector2
    hp: int = 100
    score: int = 0
    move_speed: float = 240.0
    radius: int = 14

    @property
    def color(self) -> Tuple[int, int, int]:
        return (60, 140, 255)

    def clamp_to_arena(self, width: int, height: int) -> None:
        r = self.radius
        self.pos.x = max(r, min(width - r, self.pos.x))
        self.pos.y = max(r, min(height - r, self.pos.y))


