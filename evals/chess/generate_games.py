import datetime
from pathlib import Path

import chess
import chess.engine
import chess.pgn

GAMES_FOLDER = Path(__file__).parent / "games"


def generate_and_store_game(skill_level):
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

    # Save PGN file using GAMES_FOLDER
    GAMES_FOLDER.mkdir(parents=True, exist_ok=True)
    pgn_path = GAMES_FOLDER / f"skill_{skill_level}.pgn"

    with open(pgn_path, "w") as f:
        print(game, file=f)

    return pgn_path


def generate_games():
    """Generate games for all skill levels"""
    skill_levels = [5, 10, 15, 18, 20]

    for skill in skill_levels:
        print(f"Generating Skill Level {skill}...")
        pgn_path = generate_and_store_game(skill)
        print(f"Saved: {pgn_path}")

    print(f"Generated {len(skill_levels)} games in {GAMES_FOLDER}")


if __name__ == "__main__":
    generate_games()
