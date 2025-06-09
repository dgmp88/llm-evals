from dataclasses import dataclass
from typing import Literal

import numpy as np
from easyAI import AI_Player, Negamax
from easyAI.games.TicTacToe import TicTacToe as EAITicTacToe

from evals.core import (
    Eval,
    InvalidResponseException,
    LLMPlayer,
    OpponentPlayer,
    batch_eval,
)
from evals.registry import register_eval
from evals.types import Message

SYSTEM_PROMPT = """You are an expert TicTacToe player, and always make the perfect move. Either 'X' or 'O' may go first.

Respond only with a number between 1 and 9, where 1 is the top-left corner and 9 is the bottom-right corner. The game board positions are numbered as follows:

1 2 3
4 5 6
7 8 9

Respond ONLY with a number between 1 and 9. Do not respond with any new lines or other text."""


MESSAGES: list[Message] = [
    {"role": "system", "content": SYSTEM_PROMPT},
    {
        "role": "user",
        "content": """Game Board:
. . .
. . .
. . .
'X' to play""",
    },
    {"role": "assistant", "content": "1"},
    {
        "role": "user",
        "content": """Game Board:
X . .
. . .
. . .
'O' to play""",
    },
    {"role": "assistant", "content": "5"},
    {
        "role": "user",
        "content": """Game Board:
O X O
. X .
. . O
'X' to play""",
    },
    {"role": "assistant", "content": "8"},
]


class TicTacToe(EAITicTacToe):
    def __str__(self):
        board_str = "\n".join(
            [
                " ".join([[".", "O", "X"][self.board[3 * j + i]] for i in range(3)])
                for j in range(3)
            ]
        )

        # Determine whose turn it is (player 1 = O, player 2 = X)
        current_player = "O" if self.current_player == 1 else "X"

        return f"Game Board:\n{board_str}\n'{current_player}' to play:"


@dataclass
class RandomPlayer:
    rng: np.random.Generator

    def ask_move(self, game):
        return self.rng.choice(game.possible_moves())


class TicTacToeLLMPlayer(LLMPlayer):
    def __init__(self, model: str, game: TicTacToe):
        super().__init__(model=model, messages=MESSAGES)
        self.game = game

    def is_done(self):
        return self.game.is_over()

    def process_completion(self, chat_history, response):
        # Update the game board
        try:
            move = int(
                response.strip()
            )  # Let a value error raise if the move is invalid

            if move not in self.game.possible_moves():
                raise InvalidResponseException(f"Invalid move: {move}")
        except ValueError:
            raise InvalidResponseException(f"Invalid move: {response}")

        self.game.play_move(move)


class TicTacToeOpponentPlayer(OpponentPlayer):
    def __init__(self, rng: np.random.Generator, game: TicTacToe, llm_goes_first: bool):
        super().__init__()
        self.rng = rng
        self.game = game
        self.llm_goes_first = llm_goes_first

    def make_move(self, chat_history):
        # On the very first turn, check who should go first
        if len(chat_history) == 0:
            if self.llm_goes_first:
                # LLM goes first, just return the empty board
                return str(self.game)
            else:
                # LLM goes second, make a move then return board
                move = self.game.get_move()
                self.game.play_move(move)
                return str(self.game)
        else:
            # Normal turn: opponent makes move, then return board state
            move = self.game.get_move()
            self.game.play_move(move)
            return str(self.game)

    def is_done(self):
        return self.game.is_over()


OpponentType = Literal["random", "perfect"]


class TicTacToeEval(Eval):
    name = "tictactoe"

    def __init__(
        self,
        model: str,
        rng_seed: int,
        opponent: OpponentType,
    ):
        super().__init__(rng_seed=rng_seed)
        self.name = f"tictactoe_{opponent}"
        match opponent:
            case "random":
                opp = RandomPlayer(self.rng)
            case "perfect":
                opp = AI_Player(Negamax(6))
            case _:
                raise ValueError("Invalid opponent")

        # Decide who goes first at initialization
        llm_goes_first = self.rng.choice([True, False])
        if llm_goes_first:
            # LLM is player 1 (X), opponent is player 2 (O)
            game = TicTacToe([None, opp])
            self.llm_goes_first = True
        else:
            # Opponent is player 1 (X), LLM is player 2 (O)
            game = TicTacToe([opp, None])
            self.llm_goes_first = False

        self.game = game

        self.assistant = TicTacToeLLMPlayer(model=model, game=game)
        self.user = TicTacToeOpponentPlayer(
            self.rng, game=game, llm_goes_first=self.llm_goes_first
        )

    def evaluate(self):
        winner: int | None = None
        if self.game.lose():
            winner = self.game.opponent_index
        else:
            self.game.switch_player()
            if self.game.lose():
                winner = self.game.opponent_index

        if not winner:
            # It was a draw
            return 0.5

        winning_player = self.game.players[winner - 1]
        # If winning_player is None, that means the LLM won (1.0)
        # If winning_player is not None, that means the opponent won, so LLM lost (0.0)
        return 1.0 if winning_player is None else 0.0


def tic_tac_toe(model: str, opponent: OpponentType, runs: int = 10):
    """Tic Tac Toe eval using easyAI as the opponent"""

    def eval_factory(seed: int):
        return TicTacToeEval(model=model, opponent=opponent, rng_seed=seed)

    batch_eval(runs, eval_factory)


# Register the evaluations
register_eval(
    name="tictactoe_random",
    factory=lambda model, rng_seed, **kwargs: TicTacToeEval(model, rng_seed, "random"),
    description="Tic-tac-toe against a random opponent",
    default_runs=10,
)

register_eval(
    name="tictactoe_perfect",
    factory=lambda model, rng_seed, **kwargs: TicTacToeEval(model, rng_seed, "perfect"),
    description="Tic-tac-toe against a perfect AI opponent",
    default_runs=10,
)


if __name__ == "__main__":
    import fire

    fire.Fire(tic_tac_toe)
