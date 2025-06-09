import pytest

pytest.importorskip("numpy")
pytest.importorskip("openai")
pytest.importorskip("easyAI")

from evals.core import batch_eval
from evals.tictactoe import TicTacToeEval
from evals.math import MathEval

MODEL = "openai/gpt-4.1-nano"


def run_single_eval(eval_cls, **kwargs):
    factory = lambda seed: eval_cls(model=MODEL, rng_seed=seed, **kwargs)
    return batch_eval(num_runs=1, eval_factory=factory, save_results=False, verbose=False)


def test_tictactoe_one_run():
    result = run_single_eval(TicTacToeEval, opponent="random")
    assert result["statistics"]["successful_runs"] == 1


def test_math_one_run():
    result = run_single_eval(MathEval)
    assert result["statistics"]["successful_runs"] == 1
