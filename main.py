import os
from game.map import TicketToRideMap
from game.state import GameState


def print_game_status(game: GameState):
    print("\nCurrent Game Status:")
    print("=" * 40)
    for player_id, player_data in game.players.items():
        print(f"\nPlayer {player_id}:")
        print(f"  Cards in hand: {len(player_data['hand'])}")
        print(f"  Trains remaining: {player_data['remaining_trains']}")
        print(f"  Current score: {player_data['points']}")
        print(f"  Routes claimed: {len(player_data['claimed_routes'])}")
    print("=" * 40)


def play_game(num_players: int = 3, num_turns: int = 10):
    frames_dir = "frames"
    if not os.path.exists(frames_dir):
        os.makedirs(frames_dir)

    game_map = TicketToRideMap()
    game = GameState(game_map, num_players)
    svg_files = []

    # Initial setup - each player draws some cards
    for player in range(num_players):
        for _ in range(4):
            game.draw_train_card(player)

    # Game loop - now with just one player action per turn
    current_player = 0
    for turn in range(num_turns * num_players):  # Adjust total turns to give each player equal turns
        print(f"\nTurn {turn + 1}")
        print(f"Player {current_player}'s turn")
        print("-" * 20)

        # Simple AI: alternate between drawing cards and claiming routes
        if turn % 2 == 0:
            # Draw cards
            card = game.draw_train_card(current_player)
            if card:
                print(f"Player {current_player} drew a {card.value} card")
        else:
            # Try to claim a route
            for city in ["Seattle", "Portland", "San Francisco"]:
                available_routes = game.map.get_available_routes(city)
                for route in available_routes:
                    player_hand = game.players[current_player]["hand"]
                    if game.map.claim_route(route, current_player, player_hand):
                        game.players[current_player]["points"] += game.map.calculate_route_points(route)
                        game.players[current_player]["claimed_routes"].append(route)
                        print(f"Player {current_player} claimed route: {route.city1} to {route.city2}")
                        break
                else:
                    continue
                break

        print_game_status(game)

        # Save the current state as SVG
        svg_filename = os.path.join(frames_dir, f"game_state_turn_{turn + 1}.svg")
        game.map.render_svg_to_file(
            svg_filename,
            turn_number=turn + 1,
            player_hands={i: data['hand'] for i, data in game.players.items()}
        )
        svg_files.append(svg_filename)

        # Move to next player
        current_player = (current_player + 1) % num_players

    # Create GIF from all turns
    game.map.create_game_gif(svg_files)

    # Remove cleanup code to keep the SVG files


if __name__ == "__main__":
    play_game(num_players=3, num_turns=10)
