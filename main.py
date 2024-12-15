import os
from game.map import TicketToRideMap
from game.state import GameState
from game.agent import TicketToRideAI


def print_game_status(game: GameState):
    print("\nCurrent Game Status:")
    print("=" * 40)
    for player_id, player_data in game.players.items():
        print(f"\nPlayer {player_id}:")
        print(f"  Cards in hand: {len(player_data['hand'])}")
        print(f"  Trains remaining: {player_data['remaining_trains']}")
        print(f"  Current score: {player_data['points']}")

        if player_data['claimed_routes']:
            print("  Claimed routes:")
            for route in player_data['claimed_routes']:
                points = game.map.calculate_route_points(route)
                print(f"    {route.city1} → {route.city2} ({route.length} trains, {points} points)")
        else:
            print("  No routes claimed yet")

        if player_data['destination_tickets']:
            print("  Destination tickets:")
            for ticket in player_data['destination_tickets']:
                completed = game.map.are_cities_connected(player_id, ticket.city1, ticket.city2)
                status = "✓" if completed else "✗"
                print(f"    {status} {ticket.city1} → {ticket.city2} ({ticket.points} points)")
        else:
            print("  No destination tickets")

    print("=" * 40)


def play_game(num_players: int = 2, max_turns: int = 80):
    frames_dir = "frames"
    if os.path.exists(frames_dir):
        for file in os.listdir(frames_dir):
            file_path = os.path.join(frames_dir, file)
            if os.path.isfile(file_path):
                os.unlink(file_path)
            elif os.path.isdir(file_path):
                os.rmdir(file_path)
    else:
        os.makedirs(frames_dir, exist_ok=True)

    game_map = TicketToRideMap()
    game = GameState(game_map, num_players)
    svg_files = []

    # Initialize AI agents for each player by passing player's state and game map
    ai_agents = {i: TicketToRideAI(game.players[i], game_map) for i in range(num_players)}
    for i in range(num_players):
        game.players[i]['ai_agent'] = ai_agents[i]

    # Initial setup - each player draws some cards and destination tickets
    for player in range(num_players):
        for _ in range(4):
            card = game.draw_train_card(player)
            if card:
                print(f"Player {player} drew a {card.value} card")
        # Initial destination ticket selection
        game.initial_ticket_selection(player)

    # Game loop
    current_player = 0
    while True:
        print(f"\nTurn {game.turn_number + 1}")
        print(f"Player {current_player}'s turn")
        print("-" * 20)

        # Check for max turns limit or empty deck condition
        if game.turn_number >= max_turns or (len(game.train_deck) == 0 and len(game.face_up_cards) == 0):
            print(f"Game over - {'maximum turns reached' if game.turn_number >= max_turns else 'deck exhausted'}!")
            break

        ai = ai_agents[current_player]
        ai.set_face_up_cards(game.face_up_cards)  # Update AI with current face-up cards
        action = ai.choose_action()

        if action == 'draw_cards':
            # Draw two cards
            for _ in range(2):
                card = game.draw_train_card(current_player)
                if card:
                    print(f"Player {current_player} drew a {card.value} card")

        elif action == 'claim_route':
            # Try to claim a route
            claimed = False
            for route in game.map.routes:
                if route.claimed_by is None and game.map.has_enough_cards(ai.player_state["hand"], route):
                    if game.map.claim_route(route, current_player, ai.player_state["hand"]):
                        game.players[current_player]["points"] += game.map.calculate_route_points(route)
                        game.players[current_player]["claimed_routes"].append(route)
                        game.players[current_player]["remaining_trains"] -= route.length
                        print(f"Player {current_player} claimed route: {route.city1} to {route.city2}")
                        claimed = True
                        break
            if not claimed:
                # If couldn't claim any route, draw cards instead
                card = game.draw_train_card(current_player)
                if card:
                    print(f"Player {current_player} drew a {card.value} card")

        elif action == 'draw_tickets':
            # Player draws 3 destination tickets and keeps at least 1
            game.draw_destination_tickets(current_player)
            print(f"Player {current_player} drew new destination tickets")

        # Check for endgame condition after the player's turn
        game.check_end_game_condition(current_player)

        print_game_status(game)

        # Save the current state as SVG
        svg_filename = os.path.join(frames_dir, f"game_state_turn_{game.turn_number + 1}.svg")
        game.map.render_svg_to_file(
            svg_filename,
            turn_number=game.turn_number + 1,
            player_hands={i: {
                'cards': data['hand'],
                'points': data['points'],
                'destination_tickets': data['destination_tickets']
            } for i, data in game.players.items()},
            current_player=current_player,
            face_up_cards=game.face_up_cards
        )
        svg_files.append(svg_filename)

        # Move to next player and increment turn number
        game.turn_number += 1
        current_player = (current_player + 1) % num_players

        # Check if the final round has been triggered and completed
        if game.final_round and current_player == game.last_turn_player:
            print("Final round completed. Game over!")
            break

    print("\nGame finished! Generating replay GIF...")
    game.map.create_game_gif(svg_files)


if __name__ == "__main__":
    play_game(num_players=2)
