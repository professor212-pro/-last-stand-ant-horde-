from __future__ import annotations

from dataclasses import dataclass
from typing import Literal, Tuple

import pygame


@dataclass
class Enemy:
    kind: Literal["normal", "fast", "armored"]
    pos: pygame.Vector2
    hp: int
    damage: int
    speed: float
    radius: int = 12

    @property
    def color(self) -> Tuple[int, int, int]:
        if self.kind == "fast":
            return (255, 120, 120)
        if self.kind == "armored":
            return (200, 60, 60)
        return (255, 80, 80)

