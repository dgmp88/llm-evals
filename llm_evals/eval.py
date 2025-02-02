import numpy as np

from llm_evals.db import EvalResult
from llm_evals.llm import batch_completion
from llm_evals.system_prompt import SYSTEM_PROMPT
from llm_evals.types import Message, Model

SEED = 0


def math(model: Model, low=100, high=1000, num_problems: int = 50, batch_size: int = 5):
    """random numbers under 10, addition, subtraction, multiplication, division"""
    np.random.seed(SEED)

    results = []
    for i in range(0, num_problems, batch_size):
        history_batch = []
        gt_batch = []

        for b in range(batch_size):
            x, y = np.random.randint(low=low, high=high, size=2)
            operation = np.random.choice(["+", "-", "*", "/"])

            problem = f"{x} {operation} {y}"

            correct_answer: float = eval(problem)
            correct_answer = round(correct_answer, 2)
            gt_batch.append(correct_answer)

            history: list[Message] = [
                Message(
                    role="system",
                    content=SYSTEM_PROMPT,
                ),
                Message(
                    role="user",
                    content=problem,
                ),
            ]
            history_batch.append(history)

        pred_batch = batch_completion(model, history_batch)

        for pred, gt in zip(pred_batch, gt_batch):
            correct = False
            try:
                pred = float(pred)
                correct = pred == gt
            except ValueError:
                pass

            if not correct:
                print(f" - Wrong with: {pred} (gt: {gt})")

            results.append(correct)

    percent_correct = sum(results) / num_problems

    result = EvalResult(model_name=model, eval_name="math_easy", result=percent_correct)
    result.save()


if __name__ == "__main__":
    import fire

    fire.Fire({"math": math})
