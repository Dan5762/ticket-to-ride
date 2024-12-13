from typing import List, Dict, Set

from game.utils import Route, DestinationTicket, CardColor


class TicketToRideAI:
    def __init__(self):
        self.hand: List[CardColor] = []
        self.claimed_routes: List[Route] = []
        self.destination_tickets: List[DestinationTicket] = []
        self.remaining_trains = 45
        self.points = 0

    def evaluate_game_state(self) -> float:
        """
        Evaluate current game state and return a score.
        Higher scores indicate better positions.
        """
        score = 0.0

        # Factor 1: Progress on destination tickets
        for ticket in self.destination_tickets:
            completion_percentage = self._calculate_ticket_completion(ticket)
            score += ticket.points * completion_percentage

        # Factor 2: Current points from claimed routes
        score += self.points * 1.5  # Weight actual points more heavily

        # Factor 3: Remaining trains (penalize having too many unused)
        if self.remaining_trains > 20:
            score -= (self.remaining_trains - 20) * 2

        # Factor 4: Hand evaluation
        score += self._evaluate_hand()

        return score

    def _evaluate_hand(self) -> float:
        """
        Evaluate the potential of cards in hand.
        """
        score = 0.0
        color_counts = {}

        # Count cards by color
        for card in self.hand:
            color_counts[card] = color_counts.get(card, 0) + 1

        # Score sets of cards
        for color, count in color_counts.items():
            # Bigger sets are worth more
            if count >= 6:
                score += 15
            elif count >= 4:
                score += 8
            elif count >= 3:
                score += 4

        # Wild cards are valuable
        wild_count = color_counts.get(CardColor.WILD, 0)
        score += wild_count * 3

        return score

    def _calculate_ticket_completion(self, ticket: DestinationTicket) -> float:
        """
        Calculate how close we are to completing a destination ticket.
        Returns value between 0 and 1.
        """
        # Build graph of claimed routes
        graph = self._build_route_graph()

        # Check if cities are connected
        if self._cities_connected(ticket.city1, ticket.city2, graph):
            return 1.0

        # If not connected, estimate progress based on shortest path
        distance = self._estimate_remaining_distance(ticket.city1, ticket.city2, graph)
        max_possible_distance = 20  # approximate max distance in game

        return max(0, 1 - (distance / max_possible_distance))

    def choose_action(self) -> str:
        """
        Decide the best action to take in current game state.
        Returns one of: 'draw_cards', 'claim_route', 'draw_tickets'
        """
        # Calculate action scores
        draw_score = self._evaluate_drawing_cards()
        claim_score = self._evaluate_claiming_route()
        ticket_score = self._evaluate_drawing_tickets()

        # Return action with highest score
        scores = {
            'draw_cards': draw_score,
            'claim_route': claim_score,
            'draw_tickets': ticket_score
        }
        return max(scores.items(), key=lambda x: x[1])[0]

    def _evaluate_drawing_cards(self) -> float:
        """
        Evaluate value of drawing train cards.
        """
        score = 0.0

        # More valuable if we have few cards
        if len(self.hand) < 4:
            score += 10

        # More valuable if we're close to completing routes
        for ticket in self.destination_tickets:
            if self._calculate_ticket_completion(ticket) > 0.5:
                score += 5

        return score

    def _evaluate_claiming_route(self) -> float:
        """
        Evaluate value of claiming a route.
        """
        score = 0.0

        # Can't claim if too few trains
        if self.remaining_trains < 6:
            return -1000

        # More valuable if we can complete destination tickets
        for ticket in self.destination_tickets:
            if self._calculate_ticket_completion(ticket) > 0.8:
                score += 15

        # More valuable if we have lots of cards
        if len(self.hand) > 8:
            score += 10

        return score

    def _evaluate_drawing_tickets(self) -> float:
        """
        Evaluate value of drawing new destination tickets.
        """
        score = 0.0

        # Less valuable if we already have many uncompleted tickets
        incomplete_tickets = sum(1 for ticket in self.destination_tickets
                                 if self._calculate_ticket_completion(ticket) < 0.5)
        score -= incomplete_tickets * 5

        # More valuable early in game
        if self.remaining_trains > 35:
            score += 10

        return score

    def _build_route_graph(self) -> Dict[str, Set[str]]:
        """
        Build graph representation of claimed routes.
        """
        graph = {}
        for route in self.claimed_routes:
            if route.city1 not in graph:
                graph[route.city1] = set()
            if route.city2 not in graph:
                graph[route.city2] = set()

            graph[route.city1].add(route.city2)
            graph[route.city2].add(route.city1)

        return graph

    def _cities_connected(self, city1: str, city2: str, graph: Dict[str, Set[str]]) -> bool:
        """
        Check if two cities are connected in the graph using BFS.
        """
        if city1 not in graph or city2 not in graph:
            return False

        visited = set()
        queue = [city1]

        while queue:
            city = queue.pop(0)
            if city == city2:
                return True

            if city in visited:
                continue

            visited.add(city)
            queue.extend(graph[city] - visited)

        return False

    def _estimate_remaining_distance(self, city1: str, city2: str, graph: Dict[str, Set[str]]) -> int:
        """
        Estimate remaining distance needed to connect two cities.
        Uses a simple heuristic based on claimed routes.
        """
        # This would implement a more sophisticated pathfinding algorithm
        # For now, return a simple estimate
        return 5  # placeholder
