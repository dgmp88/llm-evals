from easyAI import AI_Player, Negamax
from easyAI.games.TicTacToe import TicTacToe as EAITicTacToe

from evals.core import Assistant, Eval, User, batch_eval
from evals.types import Model

SYSTEM_PROMPT = """You are an expert TicTacToe player, and always make the perfect move. Respond with a number between 1 and 9, where 1 is the top-left corner and 9 is the bottom-right corner. The game board is numbered as follows:

1 2 3
4 5 6
7 8 9

## Examples:
User: -
. . .
. . .
. . .
Assistant: 1
----
User: 1
O . .
. . .
. . .
Assistant: 5
----
User: 2
O X O
. X .
. . O
Assistant: 8"""


class TicTacToe(EAITicTacToe):
    def __str__(self):
        string = "\n" + "\n".join(
            [
                " ".join([[".", "O", "X"][self.board[3 * j + i]] for i in range(3)])
                for j in range(3)
            ]
        )
        return string

    def winner(self):
        if self.lose():
            idx = self.opponent_index
        else:
            idx = self.current_player
        return self.players[idx - 1]


class TicTacToeAssistant(Assistant):
    def __init__(self, model: Model, game: TicTacToe):
        super().__init__(model=model, system_prompt=SYSTEM_PROMPT)
        self.game = game

    def is_done(self):
        return self.game.is_over()

    def post_respond(self, chat_history, response):
        # Update the game board
        move = int(response)
        self.game.play_move(move)


class TicTacToeUser(User):
    def __init__(self, game: TicTacToe):
        super().__init__()
        self.game = game

    def respond(self, chat_history):
        move = self.game.get_move()
        self.game.play_move(move)

        response = str(move) + "\n" + str(self.game)
        return response

    def is_done(self):
        return self.game.is_over()


class TicTacToeEval(Eval):
    name = "tictactoe"

    def __init__(self, assistant: Assistant, user: User, game: TicTacToe):
        super().__init__(assistant=assistant, user=user)
        self.game = game

    def evaluate(self):
        winner = self.game.winner()
        res = 1 if winner is None else 0  # LLM player is 'None'
        return res


def tic_tac_toe(model: Model, runs: int = 10):
    """Tic Tac Toe eval using easyAI as the opponent"""

    def eval_factory():
        game = TicTacToe([AI_Player(Negamax(6)), None])
        return TicTacToeEval(
            assistant=TicTacToeAssistant(model=model, game=game),
            user=TicTacToeUser(game=game),
            game=game,
        )

    batch_eval(10, eval_factory)


TODO = """
1. User always goes first, which isn't fair. Fix this.
2. Implement win/lose/draw detection.
"""

if __name__ == "__main__":
    # from easyAI import AI_Player, Negamax

    # ai_algo = Negamax(6)
    # TicTacToe([Human_Player(), AI_Player(ai_algo)]).play()

    import fire

    raise ValueError(TODO)

    fire.Fire(tic_tac_toe)
