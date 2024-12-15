from dataclasses import dataclass
from enum import Enum


class CardColor(Enum):
    """
    Colors for train cards and routes.
    Note: GREY is only used for routes and cannot appear in the deck or player hands.
    WILD and GREY are special cases:
    - WILD: Can be used as any color when claiming routes
    - GREY: Used only for routes that can be claimed with any matching set of colored cards
    """
    RED = "red"
    BLUE = "blue"
    GREEN = "green"
    YELLOW = "yellow"
    BLACK = "black"
    WHITE = "white"
    ORANGE = "orange"
    PINK = "pink"
    WILD = "wild"
    GREY = "grey"  # Special case: only used for routes, never appears in deck/hands


@dataclass
class City:
    name: str
    x: int  # x-coordinate for visualization
    y: int  # y-coordinate for visualization


@dataclass
class Route:
    city1: str
    city2: str
    length: int
    color: CardColor
    claimed_by: int | None = None


@dataclass
class DestinationTicket:
    city1: str
    city2: str
    points: int
