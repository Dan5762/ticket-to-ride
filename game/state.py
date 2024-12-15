import random
from typing import List, Optional

from game.map import TicketToRideMap
from game.utils import CardColor


class GameState:
    def __init__(self, map_instance: TicketToRideMap, num_players: int):
        self.map = map_instance
        self.players = {i: {
            "player_id": i,  # Add player_id to state
            "hand": [],
            "claimed_routes": [],
            "destination_tickets": [],
            "remaining_trains": 45,
            "points": 0
        } for i in range(num_players)}
        self.current_player = 0
        self.turn_number = 0  # Initialize turn number
        self.train_deck = self._initialize_train_deck()
        self.face_up_cards = []
        self.draw_face_up_cards(5)  # Initial face-up cards
        self.drawn_tickets = []  # Track tickets that have been dealt
        self.final_round = False  # Flag to indicate if final round has started
        self.last_turn_player = None  # Player who triggered the final round

    def _initialize_train_deck(self) -> List[CardColor]:
        """Initialize the deck of train cards with the correct distribution."""
        cards = []
        # Explicitly list playable colors (excludes GREY)
        playable_colors = [
            CardColor.RED,
            CardColor.BLUE,
            CardColor.GREEN,
            CardColor.YELLOW,
            CardColor.BLACK,
            CardColor.WHITE,
            CardColor.ORANGE,
            CardColor.PINK
        ]

        # Add 12 of each regular color
        for color in playable_colors:
            cards.extend([color] * 12)

        # Add 14 wild cards
        cards.extend([CardColor.WILD] * 14)

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

    def initial_ticket_selection(self, player_id: int):
        # Give 5 destination tickets to the player
        tickets = self.map.draw_destination_tickets(5)
        # AI chooses 3 tickets to keep
        kept_tickets = self.players[player_id]['ai_agent'].choose_tickets_to_keep(tickets, min_keep=3)
        self.players[player_id]["destination_tickets"].extend(kept_tickets)
        # Return unkept tickets to the pool
        for ticket in tickets:
            if ticket not in kept_tickets:
                self.map.return_destination_ticket(ticket)

    def draw_destination_tickets(self, player_id: int):
        # Player draws 3 new tickets
        tickets = self.map.draw_destination_tickets(3)
        # AI chooses at least 1 ticket to keep
        kept_tickets = self.players[player_id]['ai_agent'].choose_tickets_to_keep(tickets, min_keep=1)
        self.players[player_id]["destination_tickets"].extend(kept_tickets)
        # Return unkept tickets to the pool
        for ticket in tickets:
            if ticket not in kept_tickets:
                self.map.return_destination_ticket(ticket)

    def check_end_game_condition(self, current_player: int):
        """Check if any player has 3 or fewer trains remaining."""
        if not self.final_round:
            remaining_trains = self.players[current_player]["remaining_trains"]
            if remaining_trains <= 3:
                self.final_round = True
                self.last_turn_player = current_player
                print(f"Player {current_player} has {remaining_trains} trains remaining. Final round begins!")
