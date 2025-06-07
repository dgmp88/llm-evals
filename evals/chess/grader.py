from pathlib import Path

import chess
import chess.engine
import chess.pgn


class MoveGrader:
    def __init__(self, depth=18, time_limit=2.0):
        """Initialize move grader with Stockfish engine

        Args:
            depth: Analysis depth for Stockfish (default 18 for better accuracy)
            time_limit: Time limit in seconds for analysis (default 2.0)
        """
        self.engine = chess.engine.SimpleEngine.popen_uci("stockfish")
        self.depth = depth
        self.time_limit = time_limit

    def grade_move(self, fen, move_uci, debug=False):
        """Return centipawn loss compared to best move

        Args:
            fen: Position in FEN notation
            move_uci: Move in UCI notation (e.g. "e2e4")
            debug: Print debug information

        Returns:
            int: Centipawn loss (0 = perfect, higher = worse)
        """
        board = chess.Board(fen)

        # Get best move and its resulting evaluation with both depth and time limits
        best_analysis = self.engine.analyse(
            board, chess.engine.Limit(depth=self.depth, time=self.time_limit)
        )
        best_move = best_analysis["pv"][0]

        # Play best move and get resulting evaluation
        board_best = board.copy()
        board_best.push(best_move)
        best_result_analysis = self.engine.analyse(
            board_best, chess.engine.Limit(depth=self.depth, time=self.time_limit)
        )
        best_result_eval = -best_result_analysis["score"].relative.score(
            mate_score=10000
        )

        # Play actual move and get resulting evaluation
        played_move = chess.Move.from_uci(move_uci)
        board_played = board.copy()
        board_played.push(played_move)
        played_result_analysis = self.engine.analyse(
            board_played, chess.engine.Limit(depth=self.depth, time=self.time_limit)
        )
        played_result_eval = -played_result_analysis["score"].relative.score(
            mate_score=10000
        )

        if debug:
            print(f"  Best move: {best_move} → eval: {best_result_eval}")
            print(f"  Played move: {played_move} → eval: {played_result_eval}")
            print(f"  Difference: {best_result_eval - played_result_eval}")

        # Return centipawn loss (0 = perfect, higher = worse)
        return max(0, best_result_eval - played_result_eval)

    def close(self):
        """Close the engine connection"""
        self.engine.quit()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()


def test_grader():
    """Test grader on actual games - grade all moves and show average centipawn loss per player"""
    GAMES_FOLDER = Path(__file__).parent / "games"

    with MoveGrader() as grader:
        print("Testing move grading on generated games...\n")

        # Process each PGN file
        for pgn_file in sorted(GAMES_FOLDER.glob("*.pgn")):
            print(f"=== {pgn_file.name} ===")

            with open(pgn_file, "r") as f:
                game = chess.pgn.read_game(f)

            if not game:
                print(f"Could not read game from {pgn_file.name}")
                continue

            # Extract moves and positions
            board = chess.Board()
            moves_with_fens = []

            for move in game.mainline_moves():
                fen_before = board.fen()
                moves_with_fens.append(
                    {
                        "move": move,
                        "move_uci": move.uci(),
                        "fen_before": fen_before,
                        "move_number": len(moves_with_fens) + 1,
                    }
                )
                board.push(move)

            total_moves = len(moves_with_fens)
            if total_moves < 10:
                print(f"Game too short ({total_moves} moves), skipping")
                continue

            print(f"Analyzing {total_moves} moves...")

            # Grade all moves
            white_losses = []
            black_losses = []

            for i, move_data in enumerate(moves_with_fens):
                # Show progress for longer games
                if total_moves > 100 and i % 20 == 0:
                    print(f"  Progress: {i + 1}/{total_moves} moves analyzed...")

                centipawn_loss = grader.grade_move(
                    move_data["fen_before"], move_data["move_uci"], debug=False
                )

                # White plays on odd move numbers (1, 3, 5, ...), Black on even (2, 4, 6, ...)
                if move_data["move_number"] % 2 == 1:
                    white_losses.append(centipawn_loss)
                else:
                    black_losses.append(centipawn_loss)

            # Calculate averages
            white_avg = sum(white_losses) / len(white_losses) if white_losses else 0
            black_avg = sum(black_losses) / len(black_losses) if black_losses else 0

            print(f"  White: {len(white_losses)} moves, avg {white_avg:.1f} cp loss")
            print(f"  Black: {len(black_losses)} moves, avg {black_avg:.1f} cp loss")
            print(
                f"  Overall: {total_moves} moves, avg {(white_avg + black_avg) / 2:.1f} cp loss"
            )
            print()

        print("Move grading test completed!")


if __name__ == "__main__":
    test_grader()
