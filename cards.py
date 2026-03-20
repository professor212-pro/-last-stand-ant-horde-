from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Card:
    name: str
    kind: str  # attack | defense | heal | bonus | special


