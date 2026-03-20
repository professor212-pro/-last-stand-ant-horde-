from __future__ import annotations

import random
from dataclasses import dataclass, field

from cards import Card


@dataclass
class Deck:
    cards: list[Card] = field(default_factory=list)

    def shuffle(self) -> None:
        random.shuffle(self.cards)

