import math
import random
import os
from typing import List, Dict
import cairosvg
from PIL import Image

from game.utils import Route, DestinationTicket, City, CardColor


class TicketToRideMap:
    def __init__(self):
        # Initialize basic US map
        self.cities: Dict[str, City] = {
            "Seattle": City("Seattle", 10, 10),
            "Portland": City("Portland", 10, 30),
            "San Francisco": City("San Francisco", 10, 80),
            "Los Angeles": City("Los Angeles", 20, 100),
            "Salt Lake City": City("Salt Lake City", 40, 60),
            "Las Vegas": City("Las Vegas", 30, 90),
            "Phoenix": City("Phoenix", 40, 100),
            "Denver": City("Denver", 60, 70),
            "Helena": City("Helena", 50, 30),
            "Omaha": City("Omaha", 80, 60),
            "Chicago": City("Chicago", 100, 50),
            "Saint Louis": City("Saint Louis", 90, 70),
            "New Orleans": City("New Orleans", 90, 100),
            "Miami": City("Miami", 120, 110),
            "New York": City("New York", 130, 40),
            "Boston": City("Boston", 135, 30)
        }

        self.routes: List[Route] = self._initialize_routes()
        self.destination_tickets: List[DestinationTicket] = self._initialize_destination_tickets()

    def _initialize_routes(self) -> List[Route]:
        """Initialize the basic routes on the map."""
        routes = [
            Route("Seattle", "Portland", 2, CardColor.GREY),
            Route("Seattle", "Helena", 6, CardColor.YELLOW),

            Route("Portland", "Helena", 5, CardColor.BLUE),
            Route("Portland", "San Francisco", 5, CardColor.GREEN),
            Route("Portland", "Salt Lake City", 6, CardColor.RED),

            Route("San Francisco", "Los Angeles", 3, CardColor.YELLOW),
            Route("San Francisco", "Salt Lake City", 5, CardColor.WHITE),

            Route("Los Angeles", "Las Vegas", 2, CardColor.RED),
            Route("Los Angeles", "Phoenix", 3, CardColor.BLACK),

            Route("Las Vegas", "Salt Lake City", 3, CardColor.ORANGE),
            Route("Las Vegas", "Phoenix", 2, CardColor.WILD),

            Route("Salt Lake City", "Denver", 3, CardColor.RED),
            Route("Salt Lake City", "Helena", 3, CardColor.PINK),

            Route("Denver", "Omaha", 4, CardColor.PINK),
            Route("Denver", "Helena", 4, CardColor.GREEN),
            Route("Denver", "New Orleans", 5, CardColor.ORANGE),

            Route("Omaha", "Chicago", 4, CardColor.BLUE),

            Route("Chicago", "Saint Louis", 3, CardColor.GREEN),
            Route("Chicago", "New York", 5, CardColor.WHITE),

            Route("Saint Louis", "New Orleans", 4, CardColor.GREEN),

            Route("New Orleans", "Miami", 5, CardColor.RED),

            Route("Miami", "New York", 8, CardColor.BLUE),

            Route("New York", "Boston", 2, CardColor.YELLOW),
            Route("New York", "Boston", 2, CardColor.RED),

            Route("Helena", "Omaha", 5, CardColor.RED),
            Route("Helena", "New York", 8, CardColor.ORANGE),

            Route("Phoenix", "New Orleans", 7, CardColor.YELLOW),
        ]
        return routes

    def _initialize_destination_tickets(self) -> List[DestinationTicket]:
        """Initialize the destination tickets."""
        return [
            DestinationTicket("Seattle", "New York", 22),
            DestinationTicket("Los Angeles", "Chicago", 16),
            DestinationTicket("Denver", "Miami", 20),
            DestinationTicket("Portland", "Phoenix", 11),
            DestinationTicket("San Francisco", "Boston", 25),
            DestinationTicket("Salt Lake City", "New Orleans", 15),
            DestinationTicket("Helena", "Miami", 20),
            DestinationTicket("Chicago", "New Orleans", 7),
            DestinationTicket("New York", "Los Angeles", 21)
        ]

    def get_available_routes(self, city: str) -> List[Route]:
        """Get all available (unclaimed) routes from a city."""
        for route in self.routes:
            if route.city1 == city or route.city2 == city:
                print(route)
        return [
            route for route in self.routes
            if (route.city1 == city or route.city2 == city) and route.claimed_by is None
        ]

    def has_enough_cards(self, hand, route: Route) -> bool:
        """Check if the player has enough cards to claim the route."""
        color_count = {}
        wild_count = 0

        # Count cards by color
        for card in hand:
            if card == CardColor.WILD:
                wild_count += 1
            else:
                color_count[card] = color_count.get(card, 0) + 1

        needed = route.length
        if route.color != CardColor.WILD:
            # For colored routes, first try to use matching cards
            available = color_count.get(route.color, 0)
            needed -= available
            # Then use wilds for the remainder
            needed -= min(wild_count, needed)
        else:
            # For wild routes, can use any combination of cards
            total_cards = sum(color_count.values()) + wild_count
            needed -= total_cards

        return needed <= 0

    def spend_cards(self, hand, route: Route) -> List[CardColor]:
        """Remove and return cards used to claim the route."""
        if not self.has_enough_cards(hand, route):
            return []

        spent_cards = []
        remaining_length = route.length

        # For colored routes, first use matching cards
        if route.color != CardColor.WILD:
            matching_cards = [c for c in hand if c == route.color]
            while matching_cards and remaining_length > 0:
                card = matching_cards.pop()
                hand.remove(card)
                spent_cards.append(card)
                remaining_length -= 1

        # Then use wild cards if needed
        wild_cards = [c for c in hand if c == CardColor.WILD]
        while wild_cards and remaining_length > 0:
            card = wild_cards.pop()
            hand.remove(card)
            spent_cards.append(card)
            remaining_length -= 1

        # For wild routes or remaining needs, use any cards
        if remaining_length > 0:
            other_cards = [c for c in hand if c != CardColor.WILD]
            while other_cards and remaining_length > 0:
                card = other_cards.pop()
                hand.remove(card)
                spent_cards.append(card)
                remaining_length -= 1

        return spent_cards

    def claim_route(self, route: Route, player_id: int, player_hand: List[CardColor]) -> bool:
        """
        Attempt to claim a route for a player.
        Returns True if successful, False if route is already claimed or player lacks cards.
        """
        if route.claimed_by is not None:
            return False

        if not self.has_enough_cards(player_hand, route):
            return False

        spent_cards = self.spend_cards(player_hand, route)
        if not spent_cards:
            return False

        route.claimed_by = player_id
        return True

    def are_cities_connected(self, player_id: int, city1: str, city2: str) -> bool:
        """Check if two cities are connected by a player's routes."""
        # Build graph of player's routes
        graph = {}
        for route in self.routes:
            if route.claimed_by != player_id:
                continue

            if route.city1 not in graph:
                graph[route.city1] = set()
            if route.city2 not in graph:
                graph[route.city2] = set()

            graph[route.city1].add(route.city2)
            graph[route.city2].add(route.city1)

        # Use BFS to check connectivity
        if city1 not in graph or city2 not in graph:
            return False

        visited = set()
        queue = [city1]

        while queue:
            current = queue.pop(0)
            if current == city2:
                return True

            if current in visited:
                continue

            visited.add(current)
            if current in graph:
                queue.extend(graph[current] - visited)

        return False

    def draw_destination_tickets(self, num_tickets: int) -> List[DestinationTicket]:
        """Draw a specified number of destination tickets."""
        available_tickets = [t for t in self.destination_tickets if t not in self.drawn_tickets]
        drawn = random.sample(available_tickets, min(num_tickets, len(available_tickets)))
        self.drawn_tickets.extend(drawn)
        return drawn

    def calculate_route_points(self, route: Route) -> int:
        """Calculate points for a claimed route based on its length."""
        points_table = {
            1: 1,
            2: 2,
            3: 4,
            4: 7,
            5: 10,
            6: 15,
            7: 18,
            8: 21
        }
        return points_table.get(route.length, 0)

    def render_svg(self, width: int = 800, height: int = 600, turn_number: int = None, player_hands=None) -> str:
        # Add extra height for player hands section
        total_height = height + 100  # Extra 100px for hands section

        # Calculate scaling factors to fit the map in the viewport
        x_values = [city.x for city in self.cities.values()]
        y_values = [city.y for city in self.cities.values()]

        min_x, max_x = min(x_values), max(x_values)
        min_y, max_y = min(y_values), max(y_values)

        padding = 20
        viewport_width = width - 2 * padding
        viewport_height = height - 2 * padding

        scale_x = viewport_width / (max_x - min_x)
        scale_y = viewport_height / (max_y - min_y)
        scale = min(scale_x, scale_y)

        def transform_coordinate(x: float, y: float) -> tuple[float, float]:
            """Transform game coordinates to SVG coordinates"""
            return (
                (x - min_x) * scale + padding,
                (y - min_y) * scale + padding
            )

        # Start SVG with new height
        svg_elements = [
            '<?xml version="1.0" encoding="UTF-8"?>',
            f'<svg viewBox="0 0 {width} {total_height}" xmlns="http://www.w3.org/2000/svg">',
            f'<rect width="{width}" height="{total_height}" fill="#f0f0f0"/>'
        ]

        # Add turn number if provided (now in top right)
        if turn_number is not None:
            svg_elements.extend([
                f'<text x="{width - 20}" y="30" font-size="24" font-weight="bold" '
                f'stroke="white" stroke-width="3" stroke-linejoin="round" text-anchor="end">Turn {turn_number}</text>',
                f'<text x="{width - 20}" y="30" font-size="24" font-weight="bold" '
                f'fill="black" text-anchor="end">Turn {turn_number}</text>'
            ])

        # Color mapping for route colors
        color_map = {
            CardColor.RED: "#F44336",
            CardColor.BLUE: "#2196F3",
            CardColor.GREEN: "#4CAF50",
            CardColor.YELLOW: "#FFC107",
            CardColor.BLACK: "#212121",
            CardColor.WHITE: "#FAFAFA",
            CardColor.ORANGE: "#FF9800",
            CardColor.PINK: "#E91E63",
            CardColor.WILD: "#9E9E9E",
            CardColor.GREY: "#9E9E9E"
        }

        # Draw routes
        for route in self.routes:
            city1 = self.cities[route.city1]
            city2 = self.cities[route.city2]
            x1, y1 = transform_coordinate(city1.x, city1.y)
            x2, y2 = transform_coordinate(city2.x, city2.y)

            # Calculate route properties
            dx = x2 - x1
            dy = y2 - y1
            length = (dx * dx + dy * dy) ** 0.5
            angle = math.atan2(dy, dx) * 180 / math.pi

            # Draw route background
            color = color_map.get(route.color, "#9E9E9E")

            # Define segment dimensions
            segment_length = length / route.length
            car_width = segment_length * 0.8  # Leave small gap between cars
            car_height = 12

            # Create a group for the route with rotation transform
            svg_elements.append(f'<g transform="translate({x1},{y1}) rotate({angle})">')

            # Background route (always visible, faint)
            svg_elements.append(
                f'<line x1="0" y1="0" x2="{length}" y2="0" '
                f'stroke="{color}" stroke-width="{car_height}" stroke-opacity="0.2"/>'
            )

            # Draw individual train car segments
            for i in range(route.length):
                x_offset = i * segment_length

                if route.claimed_by is not None:
                    # Draw train car shape for claimed routes
                    player_color = list(CardColor)[route.claimed_by].value
                    # Train car body
                    svg_elements.append(
                        f'<rect x="{x_offset}" y="{-car_height / 2}" '
                        f'width="{car_width}" height="{car_height}" '
                        f'fill="{color_map[CardColor(player_color)]}" rx="2"/>'
                    )
                    # Add train details (optional)
                    wheel_radius = car_height / 4
                    svg_elements.append(
                        f'<circle cx="{x_offset + car_width * 0.25}" cy="{car_height / 2 - 1}" '
                        f'r="{wheel_radius}" fill="black"/>'
                    )
                    svg_elements.append(
                        f'<circle cx="{x_offset + car_width * 0.75}" cy="{car_height / 2 - 1}" '
                        f'r="{wheel_radius}" fill="black"/>'
                    )

            # Close the route group
            svg_elements.append('</g>')

            # Add route length number
            mid_x = (x1 + x2) / 2
            mid_y = (y1 + y2) / 2
            # Offset the text slightly perpendicular to the route
            text_offset = 15
            text_x = mid_x + text_offset * math.sin(math.radians(angle))
            text_y = mid_y - text_offset * math.cos(math.radians(angle))

            svg_elements.append(
                f'<text x="{text_x}" y="{text_y}" '
                f'font-size="14" font-weight="bold" text-anchor="middle" '
                f'fill="black" stroke="white" stroke-width="2" stroke-linejoin="round">'
                f'{route.length}</text>'
            )
            svg_elements.append(
                f'<text x="{text_x}" y="{text_y}" '
                f'font-size="14" font-weight="bold" text-anchor="middle" '
                f'fill="black">{route.length}</text>'
            )

        # Draw cities
        for name, city in self.cities.items():
            x, y = transform_coordinate(city.x, city.y)
            # City circle with white outline for visibility
            svg_elements.append(
                f'<circle cx="{x}" cy="{y}" r="8" '
                f'fill="white" stroke="black" stroke-width="2"/>'
            )
            # City name with white outline for visibility
            svg_elements.append(
                f'<text x="{x}" y="{y - 12}" '
                f'font-size="12" font-weight="bold" text-anchor="middle" '
                f'stroke="white" stroke-width="3" stroke-linejoin="round">{name}</text>'
            )
            svg_elements.append(
                f'<text x="{x}" y="{y - 12}" '
                f'font-size="12" font-weight="bold" text-anchor="middle" '
                f'fill="black">{name}</text>'
            )

        # After drawing the map, add player hands at the bottom
        if player_hands:
            section_width = width / len(player_hands)
            card_width = 20
            card_height = 30
            cards_y = height + 30  # Start 30px below the map

            for player_id, hand in player_hands.items():
                # Calculate section position
                section_x = player_id * section_width

                # Add player label
                svg_elements.append(
                    f'<text x="{section_x + section_width / 2}" y="{height + 20}" '
                    f'font-size="16" font-weight="bold" text-anchor="middle">Player {player_id}</text>'
                )

                # Draw cards in hand
                for i, card in enumerate(hand):
                    x = section_x + 10 + (i * (card_width + 5))  # 5px gap between cards
                    card_color = color_map.get(card, "#9E9E9E")

                    # Card with border
                    svg_elements.append(
                        f'<rect x="{x}" y="{cards_y}" width="{card_width}" height="{card_height}" '
                        f'fill="{card_color}" stroke="black" stroke-width="1" rx="2"/>'
                    )

        # Close SVG
        svg_elements.append('</svg>')

        return '\n'.join(svg_elements)

    def render_svg_to_file(self, filename: str, width: int = 800, height: int = 600, turn_number: int = None, player_hands=None):
        """Render the map to an SVG file."""
        with open(filename, 'w') as f:
            f.write(self.render_svg(width, height, turn_number, player_hands))

    def create_game_gif(self, svg_files: List[str], output_file: str = "game_replay.gif", duration: int = 1000):
        """
        Create a GIF from a series of SVG files, with each frame lasting for the specified duration.

        Args:
            svg_files: List of SVG filenames
            output_file: Output GIF filename
            duration: Duration for each frame in milliseconds
        """
        # Create temporary directory for PNG files
        temp_dir = "temp"
        if not os.path.exists(temp_dir):
            os.makedirs(temp_dir)

        # Convert SVGs to PNGs
        png_files = []
        for i, svg_file in enumerate(svg_files):
            png_file = os.path.join(temp_dir, f"frame_{i}.png")
            cairosvg.svg2png(url=svg_file, write_to=png_file)
            png_files.append(png_file)

        # Create GIF from PNGs
        frames = [Image.open(f) for f in png_files]
        frames[0].save(
            output_file,
            save_all=True,
            append_images=frames[1:],
            duration=duration,
            loop=0
        )

        # Only cleanup temporary PNG files, keep SVGs
        for f in png_files:
            os.remove(f)
        os.rmdir(temp_dir)
