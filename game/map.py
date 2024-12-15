import math
import random
import os
from typing import List, Dict, Tuple
import cairosvg
from PIL import Image
from game.utils import Route, DestinationTicket, City, CardColor


class TicketToRideMap:
    # Update color mapping - GREY routes should be solid gray, only WILD should be striped
    COLOR_MAP = {
        CardColor.RED: "#F44336",
        CardColor.BLUE: "#2196F3",
        CardColor.GREEN: "#4CAF50",
        CardColor.YELLOW: "#FFC107",
        CardColor.BLACK: "#212121",
        CardColor.WHITE: "#FAFAFA",
        CardColor.ORANGE: "#FF9800",
        CardColor.PINK: "#E91E63",
        CardColor.WILD: "url(#wildPattern)",  # Striped pattern for wild only
        CardColor.GREY: "#757575"  # Solid gray for grey routes
    }

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
            "Kansas City": City("Kansas City", 75, 70),  # New city
            "Dallas": City("Dallas", 70, 95),  # New city
            "Atlanta": City("Atlanta", 100, 85),  # New city
            "Chicago": City("Chicago", 100, 50),
            "Saint Louis": City("Saint Louis", 90, 70),
            "New Orleans": City("New Orleans", 90, 100),
            "Miami": City("Miami", 120, 110),
            "New York": City("New York", 130, 40),
            "Boston": City("Boston", 135, 30)
        }

        self.routes: List[Route] = self._initialize_routes()
        self.destination_tickets: List[DestinationTicket] = self._initialize_destination_tickets()
        self.drawn_tickets = []  # Keep track of drawn destination tickets

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
            Route("Phoenix", "Denver", 3, CardColor.WHITE),  # Add Phoenix-Denver route

            Route("Salt Lake City", "Denver", 3, CardColor.RED),
            Route("Salt Lake City", "Helena", 3, CardColor.PINK),

            Route("Denver", "Omaha", 4, CardColor.PINK),
            Route("Denver", "Kansas City", 2, CardColor.BLACK),  # New route
            Route("Denver", "Dallas", 4, CardColor.RED),  # New route
            Route("Denver", "Helena", 4, CardColor.GREEN),
            Route("Helena", "Chicago", 6, CardColor.BLACK),  # Add Helena-Chicago route

            Route("Kansas City", "Omaha", 1, CardColor.GREY),  # New route
            Route("Kansas City", "Saint Louis", 2, CardColor.BLUE),  # New route
            Route("Kansas City", "Dallas", 3, CardColor.GREY),  # New route

            Route("Dallas", "New Orleans", 3, CardColor.RED),  # New route

            Route("Atlanta", "Miami", 5, CardColor.BLUE),  # New route
            Route("Atlanta", "New Orleans", 4, CardColor.YELLOW),  # New route
            Route("Atlanta", "New York", 6, CardColor.GREEN),  # New route

            Route("Omaha", "Chicago", 4, CardColor.BLUE),

            Route("Chicago", "Saint Louis", 3, CardColor.GREEN),
            Route("Chicago", "New York", 5, CardColor.WHITE),
            Route("Chicago", "New York", 4, CardColor.PINK),  # Added second Chicago-New York route

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
            # Shorter routes with balanced point values
            DestinationTicket("Seattle", "Helena", 8),
            DestinationTicket("Portland", "Salt Lake City", 8),
            DestinationTicket("San Francisco", "Las Vegas", 7),
            DestinationTicket("Los Angeles", "Phoenix", 6),
            DestinationTicket("Salt Lake City", "Denver", 7),
            DestinationTicket("Phoenix", "Denver", 8),
            DestinationTicket("Helena", "Omaha", 8),
            DestinationTicket("Denver", "Kansas City", 7),
            DestinationTicket("Omaha", "Chicago", 8),
            DestinationTicket("Kansas City", "Saint Louis", 6),
            DestinationTicket("Dallas", "New Orleans", 8),
            DestinationTicket("Atlanta", "Miami", 9),
            # A few medium-length routes
            DestinationTicket("Chicago", "New York", 12),
            DestinationTicket("Saint Louis", "New Orleans", 10),
            DestinationTicket("Atlanta", "New Orleans", 10),
            # Only a couple of long routes for ambitious players
            DestinationTicket("Los Angeles", "Chicago", 16),
            DestinationTicket("Seattle", "New York", 20),
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
        if route.color == CardColor.GREY:
            # Grey routes can be claimed with any set of same-colored cards
            # Check each color (excluding wild) to see if we have enough
            for color, count in color_count.items():
                if color != CardColor.WILD:
                    if count + wild_count >= route.length:
                        return True
            return False
        elif route.color != CardColor.WILD:
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

        if route.color == CardColor.GREY:
            # Find the color we have the most of
            color_counts = {}
            for card in hand:
                if card != CardColor.WILD:
                    color_counts[card] = color_counts.get(card, 0) + 1

            if not color_counts:  # Only wild cards
                chosen_color = CardColor.WILD
            else:
                chosen_color = max(color_counts.items(), key=lambda x: x[1])[0]

            # Use chosen color cards first
            matching_cards = [c for c in hand if c == chosen_color]
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

            return spent_cards

        # For colored or wild routes, use existing logic
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

    def return_destination_ticket(self, ticket: DestinationTicket):
        """Return an unkept destination ticket to the pool."""
        if ticket in self.drawn_tickets:
            self.drawn_tickets.remove(ticket)

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

    def _get_svg_dimensions(self, width: int, height: int) -> Tuple[int, int, int]:
        """Calculate dimensions for SVG rendering."""
        player_section_height = 250
        header_height = 100  # Increased from 50 to 100
        map_height = height - header_height
        total_height = height + player_section_height
        return height, map_height, total_height

    def _get_coordinate_transformer(self, width: int, map_height: int) -> callable:
        """Create coordinate transformation function with current scaling."""
        x_values = [city.x for city in self.cities.values()]
        y_values = [city.y for city in self.cities.values()]
        min_x, max_x = min(x_values), max(x_values)
        min_y, max_y = min(y_values), max(y_values)

        # Scale to 90% of width/height to leave margin
        viewport_width = width * 0.9
        viewport_height = map_height * 0.9

        scale_x = viewport_width / (max_x - min_x)
        scale_y = viewport_height / (max_y - min_y)
        scale = min(scale_x, scale_y)

        def transform_coordinate(x: float, y: float) -> tuple[float, float]:
            """Transform coordinates to fit map exactly in viewport"""
            scaled_width = (max_x - min_x) * scale
            scaled_height = (max_y - min_y) * scale
            # Center the map horizontally and add more vertical offset
            x_offset = (width - scaled_width) / 2
            y_offset = 100  # Match the new header_height value
            return (
                (x - min_x) * scale + x_offset,
                (y - min_y) * scale + y_offset
            )

        return transform_coordinate

    def _draw_route(self, route: Route, transform_coord: callable, svg_elements: list):
        """Draw a single route on the map."""
        city1, city2 = self.cities[route.city1], self.cities[route.city2]
        x1, y1 = transform_coord(city1.x, city1.y)
        x2, y2 = transform_coord(city2.x, city2.y)

        dx, dy = x2 - x1, y2 - y1
        length = (dx * dx + dy * dy) ** 0.5
        angle = math.atan2(dy, dx) * 180 / math.pi

        # Use slightly darker gray for GREY routes to make them more visible
        color = "#757575" if route.color == CardColor.GREY else self.COLOR_MAP.get(route.color, "#9E9E9E")
        segment_length = length / route.length
        car_width = segment_length * 0.8
        car_height = 12

        # Draw route group
        svg_elements.append(f'<g transform="translate({x1},{y1}) rotate({angle})">')
        svg_elements.append(
            f'<line x1="0" y1="0" x2="{length}" y2="0" '
            f'stroke="{color}" stroke-width="{car_height}" stroke-opacity="0.2"/>'
        )

        if route.claimed_by is not None:
            player_color = self.COLOR_MAP[CardColor(list(CardColor)[route.claimed_by].value)]
            for i in range(route.length):
                x_offset = i * segment_length
                # Draw train car
                svg_elements.append(
                    f'<rect x="{x_offset}" y="{-car_height / 2}" '
                    f'width="{car_width}" height="{car_height}" '
                    f'fill="{player_color}" rx="2"/>'
                )
                # Draw wheels
                for wheel_pos in [0.25, 0.75]:
                    svg_elements.append(
                        f'<circle cx="{x_offset + car_width * wheel_pos}" '
                        f'cy="{car_height / 2 - 1}" r="{car_height / 4}" fill="black"/>'
                    )

        svg_elements.append('</g>')

        # Add route length
        text_offset = 15
        mid_x = (x1 + x2) / 2
        mid_y = (y1 + y2) / 2
        text_x = mid_x + text_offset * math.sin(math.radians(angle))
        text_y = mid_y - text_offset * math.cos(math.radians(angle))

        # Draw route length with outline
        for stroke in [True, False]:
            attrs = 'stroke="white" stroke-width="2" stroke-linejoin="round"' if stroke else 'fill="black"'
            svg_elements.append(
                f'<text x="{text_x}" y="{text_y}" '
                f'font-size="14" font-weight="bold" text-anchor="middle" '
                f'{attrs}>{route.length}</text>'
            )

    def render_svg(self, width: int = 800, height: int = 600, turn_number: int = None,
                   player_hands=None, current_player: int = None, face_up_cards=None) -> str:
        base_height, map_height, total_height = self._get_svg_dimensions(width, height)
        transform_coord = self._get_coordinate_transformer(width, map_height)

        # Initialize SVG
        svg_elements = [
            '<?xml version="1.0" encoding="UTF-8"?>',
            f'<svg viewBox="0 0 {width} {total_height}" xmlns="http://www.w3.org/2000/svg">',
            self._get_svg_defs(),
            f'<rect width="{width}" height="{total_height}" fill="#f0f0f0"/>'
        ]

        # Draw map elements
        self._draw_face_up_cards(svg_elements, face_up_cards, width)
        self._draw_turn_number(svg_elements, turn_number, width)

        # Draw routes and cities
        for route in self.routes:
            self._draw_route(route, transform_coord, svg_elements)

        for name, city in self.cities.items():
            self._draw_city(city, name, transform_coord, svg_elements)

        # Draw player sections
        if player_hands:
            self._draw_player_sections(svg_elements, player_hands, current_player,
                                       width, base_height)

        svg_elements.append('</svg>')
        return '\n'.join(svg_elements)

    def _get_svg_defs(self) -> str:
        """Get SVG definitions including patterns."""
        return '''<defs>
            <pattern id="wildPattern" patternUnits="userSpaceOnUse" width="10" height="10">
                <rect width="10" height="10" fill="white"/>
                <path d="M-1,1 l2,-2 M0,10 l10,-10 M9,11 l2,-2" stroke="black" stroke-width="2"/>
            </pattern>
        </defs>'''

    def render_svg_to_file(self, filename: str, width: int = 800, height: int = 600,
                           turn_number: int = None, player_hands=None, current_player: int = None,
                           face_up_cards=None):
        """Render the map to an SVG file."""
        with open(filename, 'w') as f:
            f.write(self.render_svg(width, height, turn_number, player_hands, current_player, face_up_cards))

    def create_game_gif(self, svg_files: List[str], output_file: str = "game_replay.gif", duration: int = 200):
        """
        Create a GIF from a series of SVG files, with each frame lasting for the specified duration.

        Args:
            svg_files: List of SVG filenames
            output_file: Output GIF filename
            duration: Duration for each frame in milliseconds
        """
        print("\nGenerating game replay GIF...")
        print("[", end="", flush=True)

        # Create temporary directory for PNG files
        temp_dir = "temp"
        if not os.path.exists(temp_dir):
            os.makedirs(temp_dir)

        # Convert SVGs to PNGs with progress indicator
        png_files = []
        for i, svg_file in enumerate(svg_files):
            png_file = os.path.join(temp_dir, f"frame_{i}.png")
            cairosvg.svg2png(url=svg_file, write_to=png_file)
            png_files.append(png_file)

            # Print progress bar
            progress = (i + 1) / len(svg_files)
            bar_width = 40
            position = int(progress * bar_width)
            print("\r[" + "=" * position + ">" + " " * (bar_width - position - 1) + "]" +
                  f" {int(progress * 100)}%", end="", flush=True)

        print("\nCombining frames into GIF...")

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

        print(f"Game replay saved as {output_file}")

    def _draw_face_up_cards(self, svg_elements: list, face_up_cards: list, width: int):
        """Draw the face-up cards at the top of the display."""
        if not face_up_cards:
            return

        card_width = 30
        card_height = 45
        card_gap = 5
        start_x = width - 20 - (5 * (card_width + card_gap))
        cards_y = 20

        for i, card in enumerate(face_up_cards):
            x = start_x + i * (card_width + card_gap)
            card_color = self.COLOR_MAP.get(card, "#9E9E9E")
            svg_elements.append(
                f'<rect x="{x}" y="{cards_y}" width="{card_width}" height="{card_height}" '
                f'fill="{card_color}" stroke="black" stroke-width="1" rx="2"/>'
            )

    def _draw_turn_number(self, svg_elements: list, turn_number: int, width: int):
        """Draw the turn number indicator."""
        if turn_number is None:
            return

        # Position the turn number at the top left
        svg_elements.extend([
            f'<text x="20" y="40" font-size="24" font-weight="bold" '
            f'stroke="white" stroke-width="3" stroke-linejoin="round" text-anchor="start">Turn {turn_number}</text>',
            f'<text x="20" y="40" font-size="24" font-weight="bold" '
            f'fill="black" text-anchor="start">Turn {turn_number}</text>'
        ])

    def _draw_city(self, city: City, name: str, transform_coord: callable, svg_elements: list):
        """Draw a city and its name."""
        x, y = transform_coord(city.x, city.y)
        svg_elements.append(
            f'<circle cx="{x}" cy="{y}" r="8" '
            f'fill="white" stroke="black" stroke-width="2"/>'
        )
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

    def _draw_player_sections(self, svg_elements: list, player_hands: dict, current_player: int, width: int, base_height: int):
        """Draw the player sections at the bottom."""
        section_width = width / len(player_hands)
        card_width = 20
        card_height = 30
        cards_y = base_height + 30
        cards_per_row = int((section_width - 40) / (card_width + 5))

        for player_id, hand in player_hands.items():
            section_x = player_id * section_width

            # Draw player header
            font_weight = "900" if player_id == current_player else "normal"
            player_color = self.COLOR_MAP[list(CardColor)[player_id]]
            svg_elements.append(
                f'<text x="{section_x + section_width / 2}" y="{base_height + 20}" '
                f'font-size="16" font-weight="{font_weight}" text-anchor="middle" '
                f'fill="{player_color}">Player {player_id} ({hand.get("points", 0)}pts)</text>'
            )

            # Draw cards
            cards = hand.get('cards', [])
            for i, card in enumerate(cards):
                row = i // cards_per_row
                col = i % cards_per_row
                x = section_x + 10 + (col * (card_width + 5))
                y = cards_y + (row * (card_height + 5))
                svg_elements.append(
                    f'<rect x="{x}" y="{y}" width="{card_width}" height="{card_height}" '
                    f'fill="{self.COLOR_MAP.get(card, "#9E9E9E")}" stroke="black" stroke-width="1" rx="2"/>'
                )

            # Calculate vertical position for destination tickets
            tickets_y = cards_y + ((len(hand.get('cards', [])) - 1) // cards_per_row + 2) * (card_height + 5)

            # Draw destination tickets
            if 'destination_tickets' in hand and hand['destination_tickets']:
                svg_elements.append(
                    f'<text x="{section_x + 10}" y="{tickets_y}" '
                    f'font-size="12" font-weight="bold" fill="black">Destination Tickets:</text>'
                )
                for i, ticket in enumerate(hand['destination_tickets']):
                    is_completed = self.are_cities_connected(player_id, ticket.city1, ticket.city2)
                    text_color = "#006400" if is_completed else "#8B0000"  # Dark green if completed, dark red if not
                    svg_elements.append(
                        f'<text x="{section_x + 20}" y="{tickets_y + (i + 1) * 20}" '
                        f'font-size="12" fill="{text_color}">'
                        f'{ticket.city1} -> {ticket.city2} ({ticket.points} points)</text>'
                    )
            else:
                svg_elements.append(
                    f'<text x="{section_x + 10}" y="{tickets_y}" '
                    f'font-size="12" fill="gray">No destination tickets</text>'
                )
