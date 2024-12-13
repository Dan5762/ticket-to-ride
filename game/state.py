import random
from typing import List, Optional

from game.map import TicketToRideMap
from game.utils import CardColor


class GameState:
    def __init__(self, map_instance: TicketToRideMap, num_players: int):
        self.map = map_instance
        self.players = {i: {
            "hand": [],
            "claimed_routes": [],
            "destination_tickets": [],
            "remaining_trains": 45,
            "points": 0
        } for i in range(num_players)}
        self.current_player = 0
        self.train_deck = self._initialize_train_deck()
        self.face_up_cards = []
        self.draw_face_up_cards(5)  # Initial face-up cards

    def _initialize_train_deck(self) -> List[CardColor]:
        """Initialize the deck of train cards."""
        cards = []
        for color in CardColor:
            if color != CardColor.WILD:
                cards.extend([color] * 12)  # 12 of each regular color
        cards.extend([CardColor.WILD] * 14)  # 14 wild cards
        random.shuffle(cards)
        return cards

    def draw_face_up_cards(self, num_cards: int):
        """Draw cards to the face-up display."""
        while len(self.face_up_cards) < num_cards and self.train_deck:
            self.face_up_cards.append(self.train_deck.pop())

    def draw_train_card(self, player_id: int, face_up_index: Optional[int] = None) -> Optional[CardColor]:
        """Draw a train card, either from face-up cards or the deck."""
        if face_up_index is not None and 0 <= face_up_index < len(self.face_up_cards):
            card = self.face_up_cards.pop(face_up_index)
            self.draw_face_up_cards(5)  # Replenish face-up cards
        elif self.train_deck:
            card = self.train_deck.pop()
        else:
            return None

        self.players[player_id]["hand"].append(card)
        return card
