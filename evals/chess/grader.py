from pathlib import Path

import chess
import chess.engine
import chess.pgn

from evals.types import Message

# Add import for LLM functionality
from evals.util.llm import completion


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

    grader = MoveGrader()
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


def test_llm(model: str, max_positions: int = 50):
    """Test LLM chess moves - ask LLM for moves on positions and grade them

    Args:
        model: The LLM model to test (e.g. "openai/gpt-4")
        max_positions: Maximum number of positions to test per game (default 50)
    """
    GAMES_FOLDER = Path(__file__).parent / "games"

    grader = MoveGrader()
    print(f"Testing LLM ({model}) chess moves...\n")

    all_losses = []
    illegal_moves = 0
    total_positions = 0

    # Process each PGN file
    for pgn_file in sorted(GAMES_FOLDER.glob("*.pgn")):
        print(f"=== {pgn_file.name} ===")

        with open(pgn_file, "r") as f:
            game = chess.pgn.read_game(f)

        if not game:
            print(f"Could not read game from {pgn_file.name}")
            continue

        # Extract positions from the game
        board = chess.Board()
        positions = []

        for i, move in enumerate(game.mainline_moves()):
            if i >= max_positions:
                break

            fen_before = board.fen()
            positions.append(
                {
                    "fen": fen_before,
                    "move_number": i + 1,
                    "to_move": "White" if board.turn else "Black",
                }
            )
            board.push(move)

        if len(positions) < 5:
            print(f"Game too short ({len(positions)} positions), skipping")
            continue

        print(f"Testing {len(positions)} positions...")

        game_losses = []
        game_illegal = 0

        for i, pos in enumerate(positions):
            # Show progress for longer games
            if len(positions) > 20 and i % 10 == 0:
                print(f"  Progress: {i + 1}/{len(positions)} positions tested...")

            # Get PGN representation up to current position
            if i == 0:
                moves_text = "Starting position"
            else:
                # Get the moves up to position i
                moves_list = list(game.mainline_moves())[:i]
                temp_board = chess.Board()
                moves_text = temp_board.variation_san(moves_list)
                if not moves_text:
                    moves_text = "Starting position"

            # Create prompt for the LLM
            prompt = f"""You are playing chess. Here is the current game:

{moves_text}

It is {pos["to_move"]}'s turn to move. Please provide your move in standard algebraic notation (e.g., "e4", "Nf3", "O-O" for castling, "Qh5+", "Rxe8#").
Respond with ONLY the move in standard algebraic notation, nothing else."""
            breakpoint()

            try:
                # Get LLM's move
                response = completion(model, [Message(content=prompt, role="user")])
                llm_move_san = response.strip()

                # Check if move is legal and convert to UCI
                board = chess.Board(pos["fen"])

                try:
                    # Parse the move from standard algebraic notation
                    move = board.parse_san(llm_move_san)
                    llm_move_uci = move.uci()

                    # Legal move - grade it
                    centipawn_loss = grader.grade_move(
                        pos["fen"], llm_move_uci, debug=False
                    )
                    game_losses.append(centipawn_loss)
                    all_losses.append(centipawn_loss)

                except (ValueError, chess.InvalidMoveError, chess.IllegalMoveError):
                    # Invalid or illegal move
                    print(
                        f"  Invalid/illegal move: '{llm_move_san}' in position {pos['move_number']}"
                    )
                    game_losses.append(1000)
                    all_losses.append(1000)
                    game_illegal += 1
                    illegal_moves += 1

            except Exception as e:
                print(
                    f"  Error getting LLM response for position {pos['move_number']}: {e}"
                )
                game_losses.append(1000)
                all_losses.append(1000)
                game_illegal += 1
                illegal_moves += 1

            total_positions += 1

        # Calculate game statistics
        if game_losses:
            game_avg = sum(game_losses) / len(game_losses)
            legal_moves = len(game_losses) - game_illegal
            legal_rate = (legal_moves / len(game_losses)) * 100 if game_losses else 0

            print(f"  {len(game_losses)} positions tested")
            print(
                f"  Legal moves: {legal_moves}/{len(game_losses)} ({legal_rate:.1f}%)"
            )
            print(f"  Average cp loss: {game_avg:.1f}")
            if legal_moves > 0:
                legal_only_avg = (
                    sum([loss for loss in game_losses if loss < 1000]) / legal_moves
                )
                print(f"  Average cp loss (legal moves only): {legal_only_avg:.1f}")
            print()

    # Overall statistics
    if all_losses:
        overall_avg = sum(all_losses) / len(all_losses)
        legal_moves_total = len([loss for loss in all_losses if loss < 1000])
        legal_rate_total = (legal_moves_total / len(all_losses)) * 100

        print("=== OVERALL RESULTS ===")
        print(f"Model: {model}")
        print(f"Total positions tested: {total_positions}")
        print(
            f"Legal moves: {legal_moves_total}/{total_positions} ({legal_rate_total:.1f}%)"
        )
        print(f"Illegal moves: {illegal_moves}")
        print(f"Average cp loss (all): {overall_avg:.1f}")

        if legal_moves_total > 0:
            legal_only_avg = (
                sum([loss for loss in all_losses if loss < 1000]) / legal_moves_total
            )
            print(f"Average cp loss (legal only): {legal_only_avg:.1f}")

        # Grade distribution for legal moves
        legal_losses = [loss for loss in all_losses if loss < 1000]
        if legal_losses:
            excellent = len([loss for loss in legal_losses if loss <= 10])
            good = len([loss for loss in legal_losses if 10 < loss <= 30])
            inaccuracy = len([loss for loss in legal_losses if 30 < loss <= 60])
            mistake = len([loss for loss in legal_losses if 60 < loss <= 100])
            blunder = len([loss for loss in legal_losses if loss > 100])

            print("\nMove quality distribution (legal moves):")
            print(
                f"  Excellent (≤10 cp): {excellent} ({excellent / len(legal_losses) * 100:.1f}%)"
            )
            print(f"  Good (11-30 cp): {good} ({good / len(legal_losses) * 100:.1f}%)")
            print(
                f"  Inaccuracy (31-60 cp): {inaccuracy} ({inaccuracy / len(legal_losses) * 100:.1f}%)"
            )
            print(
                f"  Mistake (61-100 cp): {mistake} ({mistake / len(legal_losses) * 100:.1f}%)"
            )
            print(
                f"  Blunder (>100 cp): {blunder} ({blunder / len(legal_losses) * 100:.1f}%)"
            )
    else:
        print("No positions were successfully tested!")

    print("\nLLM chess move test completed!")


if __name__ == "__main__":
    import fire

    fire.Fire()
