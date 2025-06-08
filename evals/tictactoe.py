from dataclasses import dataclass
from typing import Literal

import numpy as np
from easyAI import AI_Player, Negamax
from easyAI.games.TicTacToe import TicTacToe as EAITicTacToe

from evals.core import Assistant, Eval, User, batch_eval
from evals.registry import register_eval
from evals.types import Message

SYSTEM_PROMPT = """You are an expert TicTacToe player, and always make the perfect move. Respond only with a number between 1 and 9, where 1 is the top-left corner and 9 is the bottom-right corner. The game board is numbered as follows:

1 2 3
4 5 6
7 8 9
"""


MESSAGES: list[Message] = [
    {"role": "system", "content": SYSTEM_PROMPT},
    {
        "role": "user",
        "content": """. . .
. . .
. . .""",
    },
    {"role": "assistant", "content": "1"},
    {
        "role": "user",
        "content": """O . .
. . .
. . .""",
    },
    {"role": "assistant", "content": "5"},
    {
        "role": "user",
        "content": """O X O
. X .
. . O""",
    },
    {"role": "assistant", "content": "8"},
]


class TicTacToe(EAITicTacToe):
    def __str__(self):
        string = "\n" + "\n".join(
            [
                " ".join([[".", "O", "X"][self.board[3 * j + i]] for i in range(3)])
                for j in range(3)
            ]
        )
        return string


@dataclass
class RandomPlayer:
    rng: np.random.Generator

    def ask_move(self, game):
        return self.rng.choice(game.possible_moves())


class TicTacToeAssistant(Assistant):
    def __init__(self, model: str, game: TicTacToe):
        super().__init__(model=model, messages=MESSAGES)
        self.game = game

    def is_done(self):
        return self.game.is_over()

    def post_respond(self, chat_history, response):
        # Update the game board
        move = int(response.strip())
        self.game.play_move(move)


class TicTacToeUser(User):
    def __init__(self, rng: np.random.Generator, game: TicTacToe):
        super().__init__()
        self.rng = rng
        self.game = game

    def respond(self, chat_history):
        is_empty_first_move = len(chat_history) == 0 and self.rng.choice([True, False])
        if is_empty_first_move:
            print("LLM going first")
            response = str(self.game)
            self.game.switch_player()
        else:
            move = self.game.get_move()
            self.game.play_move(move)
            response = str(move) + "\n" + str(self.game)
        return response

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

        game = TicTacToe([opp, None])
        self.game = game
        self.assistant = TicTacToeAssistant(model=model, game=game)
        self.user = TicTacToeUser(self.rng, game=game)

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
            return 0

        winning_player = self.game.players[winner - 1]
        res = 1 if winning_player is None else -1
        return res


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
