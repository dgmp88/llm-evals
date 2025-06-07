import datetime
import json
from pathlib import Path

import chess
import chess.engine
import chess.pgn


def generate_and_store_game(skill_level, game_number, output_dir="chess_data"):
    """Generate a game and store as PGN file"""
    engine = chess.engine.SimpleEngine.popen_uci("stockfish")
    engine.configure({"Skill Level": skill_level})

    board = chess.Board()
    game = chess.pgn.Game()

    # Set metadata
    game.headers["White"] = f"Stockfish_Skill_{skill_level}"
    game.headers["Black"] = f"Stockfish_Skill_{skill_level}"
    game.headers["Date"] = datetime.datetime.now().strftime("%Y.%m.%d")
    game.headers["SkillLevel"] = str(skill_level)
    game.headers["TimeControl"] = "1s"

    node = game
    moves = []

    while not board.is_game_over():
        result = engine.play(board, chess.engine.Limit(time=1.0))
        board.push(result.move)
        moves.append(result.move)
        node = node.add_variation(result.move)

    game.headers["Result"] = board.result()
    engine.quit()

    # Save PGN file
    Path(f"{output_dir}/games").mkdir(parents=True, exist_ok=True)
    pgn_path = f"{output_dir}/games/skill_{skill_level}_game_{game_number}.pgn"

    with open(pgn_path, "w") as f:
        print(game, file=f)

    return moves, board.result(), pgn_path


def extract_test_positions(pgn_path, skill_level, game_number):
    """Extract test positions from a PGN file"""
    with open(pgn_path) as f:
        game = chess.pgn.read_game(f)

    board = chess.Board()
    positions = []
    moves = list(game.mainline_moves())

    for i, move in enumerate(moves):
        # Extract early (moves 3-5) and late (last 6 moves) positions
        if i in [3, 4, 5] or i >= len(moves) - 6:
            positions.append(
                {
                    "id": f"{skill_level}_g{game_number}_move{i + 1}",
                    "source_skill_level": skill_level,
                    "game_id": f"skill_{skill_level}_game_{game_number}",
                    "move_number": i + 1,
                    "phase": "early" if i <= 5 else "late",
                    "fen": board.fen(),
                    "best_move": move.uci(),
                    "move_san": board.san(move),  # Standard algebraic notation
                    "context": {
                        "total_moves": len(moves),
                        "game_result": game.headers.get("Result", "*"),
                    },
                }
            )
        board.push(move)

    return positions


def create_complete_test_suite(output_dir="chess_data"):
    """Generate all games and create test suite"""
    skill_levels = [5, 10, 15, 18, 20]
    all_positions = []

    for skill in skill_levels:
        for game_num in range(1, 3):  # 2 games per skill level
            print(f"Generating Skill Level {skill}, Game {game_num}...")

            # Generate and store game
            moves, result, pgn_path = generate_and_store_game(
                skill, game_num, output_dir
            )

            # Extract positions
            positions = extract_test_positions(pgn_path, skill, game_num)
            all_positions.extend(positions)

    # Save test suite as JSON
    test_suite = {
        "metadata": {
            "version": "1.0",
            "generated_date": datetime.datetime.now().isoformat(),
            "total_positions": len(all_positions),
            "skill_levels": skill_levels,
            "games_per_skill_level": 2,
        },
        "positions": all_positions,
    }

    Path(output_dir).mkdir(parents=True, exist_ok=True)
    with open(f"{output_dir}/test_suite.json", "w") as f:
        json.dump(test_suite, f, indent=2)

    print(f"Generated {len(all_positions)} test positions")
    return f"{output_dir}/test_suite.json"


if __name__ == "__main__":
    create_complete_test_suite()
