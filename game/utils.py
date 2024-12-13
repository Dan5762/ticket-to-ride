from dataclasses import dataclass
from enum import Enum


class CardColor(Enum):
    RED = "red"
    BLUE = "blue"
    GREEN = "green"
    YELLOW = "yellow"
    BLACK = "black"
    WHITE = "white"
    ORANGE = "orange"
    PINK = "pink"
    WILD = "wild"
    GREY = "grey"


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
