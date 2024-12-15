from typing import List, Dict, Set

from game.utils import DestinationTicket, CardColor


class TicketToRideAI:
    def __init__(self, player_state, game_map):
        self.player_state = player_state  # Hold reference to player's state
        self.game_map = game_map  # Add reference to the game map
        self.face_up_cards = []  # Add face_up_cards attribute

    def set_face_up_cards(self, face_up_cards):
        """Update the face-up cards that the AI can see."""
        self.face_up_cards = face_up_cards

    def evaluate_game_state(self) -> float:
        """
        Evaluate current game state and return a score.
        Higher scores indicate better positions.
        """
        score = 0.0

        # Factor 1: Progress on destination tickets (with penalty for incomplete)
        for ticket in self.player_state["destination_tickets"]:
            completion_percentage = self._calculate_ticket_completion(ticket)
            if completion_percentage >= 1.0:
                score += ticket.points * 2  # Double bonus for completed tickets
            else:
                # Heavy penalty for potential incomplete tickets
                score -= (ticket.points * (1 - completion_percentage) * 2)

        # Factor 2: Current points from claimed routes
        score += self.player_state["points"] * 1.5  # Access points from player_state

        # Factor 3: Remaining trains (penalize having too many unused)
        if self.player_state["remaining_trains"] > 20:
            excess_trains = self.player_state["remaining_trains"] - 20
            score -= excess_trains * 2

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
        for card in self.player_state["hand"]:
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

    def choose_tickets_to_keep(self, tickets: List[DestinationTicket], min_keep: int) -> List[DestinationTicket]:
        """
        Decide which destination tickets to keep.
        Must keep at least min_keep tickets.
        """
        # Simple strategy: Keep tickets with the highest point values
        sorted_tickets = sorted(tickets, key=lambda t: t.points, reverse=True)
        return sorted_tickets[:min_keep]

    def _evaluate_drawing_cards(self) -> float:
        """Evaluate value of drawing train cards."""
        score = 0.0
        
        # Find cards needed for completing destination tickets
        needed_colors = self._get_colors_needed_for_tickets()
        
        # Check if any needed colors are in face-up cards
        if any(color in self.face_up_cards for color in needed_colors):
            score += 20
        else:
            score += 8

        # Reduce incentive to draw cards in late game
        if self.player_state["remaining_trains"] <= 20:
            score -= 10

        # Less incentive to draw if hand is already large
        if len(self.player_state["hand"]) > 8:
            score -= 15
        elif len(self.player_state["hand"]) < 4:
            score += 15

        return score

    def _evaluate_claiming_route(self) -> float:
        """Evaluate the value of claiming a route."""
        if self.player_state["remaining_trains"] <= 0:
            return -1000

        best_route_score = -1000
        urgency_bonus = 0

        # Calculate completion status of all tickets
        incomplete_tickets = []
        for ticket in self.player_state["destination_tickets"]:
            if not self._cities_connected(ticket.city1, ticket.city2, self._build_route_graph()):
                incomplete_tickets.append(ticket)
                urgency_bonus += ticket.points  # Add urgency based on potential points loss

        # First, identify routes that would help complete destination tickets
        for ticket in incomplete_tickets:
            path = self._find_best_path(ticket.city1, ticket.city2)
            if path:
                for i in range(len(path) - 1):
                    city1, city2 = path[i], path[i + 1]
                    route = self._find_unclaimed_route(city1, city2)
                    if route and self.game_map.has_enough_cards(self.player_state["hand"], route):
                        # Increase score based on ticket points at risk
                        route_score = self._score_route(route, is_path_route=True) + (ticket.points * 2)
                        best_route_score = max(best_route_score, route_score)

        # If no routes found for tickets, consider any claimable route
        if best_route_score == -1000:
            for route in self.game_map.routes:
                if route.claimed_by is None and self.game_map.has_enough_cards(self.player_state["hand"], route):
                    route_score = self._score_route(route, is_path_route=False)
                    best_route_score = max(best_route_score, route_score)

        # Add urgency bonus if we have incomplete tickets
        if incomplete_tickets:
            best_route_score += urgency_bonus

        # Late game bonuses
        if self.player_state["remaining_trains"] <= 30:
            best_route_score += 15
        if self.player_state["remaining_trains"] <= 15:
            best_route_score += 25

        return best_route_score

    def _evaluate_drawing_tickets(self) -> float:
        """
        Evaluate value of drawing new destination tickets.
        """
        score = 0.0

        # Very negative score if we have incomplete tickets
        incomplete_tickets = sum(1 for ticket in self.player_state["destination_tickets"]
                               if self._calculate_ticket_completion(ticket) < 0.5)
        score -= incomplete_tickets * 15  # Increased penalty

        # Only valuable very early in game with no incomplete tickets
        if self.player_state["remaining_trains"] > 35 and incomplete_tickets == 0:
            score += 10
        else:
            score -= 20  # Strong penalty against drawing more tickets if we have incomplete ones

        return score

    def _build_route_graph(self) -> Dict[str, Set[str]]:
        """
        Build graph representation of claimed routes.
        """
        graph = {}
        for route in self.player_state["claimed_routes"]:
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
        """Estimate remaining distance needed to connect two cities using Dijkstra's algorithm."""
        if city1 == city2:
            return 0

        distances = {city: float('infinity') for city in self.game_map.cities.keys()}
        distances[city1] = 0
        unvisited = set(self.game_map.cities.keys())

        while unvisited:
            # Get closest unvisited city
            current = min(unvisited, key=lambda city: distances[city])
            if current == city2:
                return int(distances[city2])

            if distances[current] == float('infinity'):
                break

            unvisited.remove(current)

            # Check all routes from current city
            for route in self.game_map.routes:
                if route.city1 == current and route.city2 in unvisited:
                    new_dist = distances[current] + route.length
                    if new_dist < distances[route.city2]:
                        distances[route.city2] = new_dist
                elif route.city2 == current and route.city1 in unvisited:
                    new_dist = distances[current] + route.length
                    if new_dist < distances[route.city1]:
                        distances[route.city1] = new_dist

        return int(distances[city2]) if distances[city2] != float('infinity') else 10

    def _get_colors_needed_for_tickets(self) -> Set[CardColor]:
        """Identify colors needed to complete destination tickets."""
        needed_colors = set()
        
        for ticket in self.player_state["destination_tickets"]:
            if not self._cities_connected(ticket.city1, ticket.city2, self._build_route_graph()):
                path = self._find_best_path(ticket.city1, ticket.city2)
                if path:
                    for i in range(len(path) - 1):
                        route = self._find_unclaimed_route(path[i], path[i + 1])
                        if route:
                            if route.color != CardColor.GREY:
                                needed_colors.add(route.color)
                            else:
                                # For grey routes, add any color we have most of
                                color_counts = {}
                                for card in self.player_state["hand"]:
                                    if card != CardColor.WILD:
                                        color_counts[card] = color_counts.get(card, 0) + 1
                                if color_counts:
                                    needed_colors.add(max(color_counts.items(), key=lambda x: x[1])[0])

        return needed_colors

    def _find_best_path(self, city1: str, city2: str) -> List[str]:
        """Find the best path between two cities using Dijkstra's algorithm."""
        distances = {city: float('infinity') for city in self.game_map.cities}
        distances[city1] = 0
        previous = {city: None for city in self.game_map.cities}
        unvisited = set(self.game_map.cities)

        while unvisited:
            # Fix: Use city parameter instead of current in the lambda
            current = min(unvisited, key=lambda city: distances[city])
            if current == city2:
                break

            if distances[current] == float('infinity'):
                break

            unvisited.remove(current)

            for route in self.game_map.routes:
                if route.claimed_by is not None and route.claimed_by != self.player_state["player_id"]:
                    continue

                next_city = None
                if route.city1 == current and route.city2 in unvisited:
                    next_city = route.city2
                elif route.city2 == current and route.city1 in unvisited:
                    next_city = route.city1

                if next_city:
                    new_dist = distances[current] + route.length
                    if new_dist < distances[next_city]:
                        distances[next_city] = new_dist
                        previous[next_city] = current

        if distances[city2] == float('infinity'):
            return []

        # Reconstruct path
        path = []
        current = city2
        while current is not None:
            path.append(current)
            current = previous[current]
        return list(reversed(path))

    def _find_unclaimed_route(self, city1: str, city2: str):
        """Find an unclaimed route between two cities."""
        for route in self.game_map.routes:
            if route.claimed_by is None:
                if (route.city1 == city1 and route.city2 == city2) or \
                   (route.city1 == city2 and route.city2 == city1):
                    return route
        return None

    def _score_route(self, route, is_path_route: bool) -> float:
        """Score a route based on its strategic value."""
        score = self.game_map.calculate_route_points(route) * 2

        # Higher bonus for routes that complete destination tickets
        if is_path_route:
            score += 40  # Increased from 30

        # Smaller penalty for longer routes
        if self.player_state["remaining_trains"] < 10:
            score -= route.length

        # Bonus for shorter routes in late game
        if self.player_state["remaining_trains"] <= 20 and route.length <= 3:
            score += 15

        # Bonus for using up cards when hand is large
        if len(self.player_state["hand"]) > 8:
            score += route.length * 3

        return score
