import time
from abc import ABC, abstractmethod
from typing import Callable

import numpy as np
from tqdm import tqdm

from evals.types import Message, Role
from evals.util.db import EvalResult
from evals.util.llm import completion


class Agent(ABC):
    role: Role

    @abstractmethod
    def respond(self, chat_history: list[Message]) -> str:
        pass

    @abstractmethod
    def is_done(self) -> bool:
        pass


TIMES = []


class Assistant(Agent):
    role = "assistant"

    def __init__(self, model: str, messages: list[Message]):
        super().__init__()
        self.model: str = model
        self.messages = messages

    def pre_respond(self, chat_history: list[Message]):
        # Overloadable hook
        pass

    def post_respond(self, chat_history: list[Message], response: str):
        # Overloadable hook
        pass

    def respond(self, chat_history: list[Message]):
        self.pre_respond(chat_history)
        ch: list[Message] = self.messages + chat_history
        t1 = time.time()
        response = completion(self.model, ch)
        print(f"Time taken: {time.time() - t1:.2f}s")
        TIMES.append(time.time() - t1)
        print(f"avg time: {np.mean(TIMES)}, max time: {np.max(TIMES)}")
        self.post_respond(chat_history, response)
        return response


class User(Agent):
    role = "user"


class Eval(ABC):
    name: str
    assistant: Assistant
    user: User
    max_turns: int = 10

    def __init__(
        self,
        rng_seed: int,
    ):
        self.rng = np.random.default_rng(seed=rng_seed)
        self.chat_history: list[Message] = []

    def run(self):
        # User always goes first for compatibility with Gemini, Claude etc.
        current = self.user

        response: None | str = None

        for i in range(self.max_turns):
            response = current.respond(self.chat_history)
            self.chat_history.append(Message(role=current.role, content=response))
            if current.is_done():
                break
            current = self.assistant if current == self.user else self.user

        score = self.evaluate()
        self.print_chat()
        return score

    @abstractmethod
    def evaluate(self) -> float:
        pass

    def print_chat(self):
        for message in self.chat_history:
            print(f"{message['role']}: {message['content']}")


def batch_eval(
    num_runs: int,
    eval_factory: Callable[[int], Eval],
    max_workers: int | None = 5,
    save_results: bool = True,
    verbose: bool = True,
) -> dict:
    """
    Run evaluations in parallel and return aggregated results.

    Args:
        num_runs: Number of evaluation runs
        eval_factory: Factory function that creates Eval instances
        max_workers: Maximum number of concurrent workers (None for auto)
        save_results: Whether to save results to database
        verbose: Whether to print progress information

    Returns:
        Dictionary containing results, statistics, and metadata
    """
    import logging
    from concurrent.futures import ThreadPoolExecutor, as_completed

    def run_single_eval(i: int) -> tuple[float, str, str, bool]:
        """Run a single evaluation and return (score, model_name, eval_name, success)"""
        try:
            eval_instance = eval_factory(i)
            if verbose:
                print(f"Starting eval {i}: {eval_instance.name}")
            score = eval_instance.run()
            return score, eval_instance.assistant.model, eval_instance.name, True
        except Exception as e:
            if verbose:
                print(f"Eval {i} failed: {str(e)}")
            logging.error(f"Evaluation {i} failed: {str(e)}")
            return 0.0, "", "", False

    # Use ThreadPoolExecutor for I/O-bound LLM tasks
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        # Submit all tasks
        future_to_index = {
            executor.submit(run_single_eval, i): i for i in range(num_runs)
        }

        # Collect results as they complete
        results: list[float] = []
        failed_runs: list[int] = []
        model_name: str | None = None
        eval_name: str | None = None

        progress_bar = (
            tqdm(total=num_runs, desc="Running evaluations") if verbose else None
        )

        for future in as_completed(future_to_index):
            run_index = future_to_index[future]
            try:
                score, m_name, e_name, success = future.result()
                if success:
                    results.append(score)
                    if model_name is None:
                        model_name = m_name
                        eval_name = e_name
                else:
                    failed_runs.append(run_index)
            except Exception as e:
                if verbose:
                    print(f"Future for run {run_index} raised exception: {e}")
                failed_runs.append(run_index)

            if progress_bar:
                progress_bar.update(1)

        if progress_bar:
            progress_bar.close()

    # Check if we have enough successful results
    success_rate = len(results) / num_runs if num_runs > 0 else 0

    if not results:
        # Provide more detailed error information
        error_msg = f"No evaluations completed successfully out of {num_runs} runs."
        if failed_runs:
            error_msg += f" Failed runs: {failed_runs}"
        if len(failed_runs) == num_runs:
            error_msg += " All evaluations failed."
        raise ValueError(error_msg)
    elif success_rate < 0.1 and num_runs > 1:
        # If success rate is very low (< 10%) and we ran multiple evaluations, warn but continue
        print(
            f"⚠️  WARNING: Very low success rate ({success_rate:.1%}). Only {len(results)}/{num_runs} evaluations succeeded."
        )
        print(f"   Failed runs: {failed_runs}")
        print("   Continuing with available results...")
    elif failed_runs and len(failed_runs) > 0:
        # Just log the failures if some succeeded
        print(
            f"ℹ️  Some evaluations failed: {len(failed_runs)}/{num_runs} failed ({len(failed_runs) / num_runs:.1%})"
        )

    # Calculate statistics
    results_array = np.array(results, dtype=np.float64)
    stats = {
        "mean": float(np.mean(results_array)),  # type: ignore
        "std": float(np.std(results_array)),  # type: ignore
        "min": float(np.min(results_array)),
        "max": float(np.max(results_array)),
        "median": float(np.median(results_array)),  # type: ignore
        "successful_runs": len(results),
        "failed_runs": len(failed_runs),
        "total_runs": num_runs,
        "success_rate": len(results) / num_runs,
    }

    if verbose:
        print(f"\nEvaluation Results:")
        print(f"  Mean Score: {stats['mean']:.4f} ± {stats['std']:.4f}")
        print(f"  Range: [{stats['min']:.4f}, {stats['max']:.4f}]")
        print(
            f"  Success Rate: {stats['successful_runs']}/{num_runs} ({stats['success_rate']:.1%})"
        )
        if failed_runs:
            print(f"  Failed runs: {failed_runs}")

    # Save to database if requested
    if save_results and model_name and eval_name:
        # Split the model name into provider and model parts
        # Expected format: "provider/model" (e.g., "anthropic/claude-sonnet-4")
        if "/" in model_name:
            provider, model = model_name.split("/", 1)
        else:
            # Fallback if no provider specified
            provider = "unknown"
            model = model_name

        eval_result = EvalResult(
            provider=provider,
            model=model,
            eval_name=eval_name,
            result=stats["mean"],
            runs=stats["successful_runs"],
        )
        eval_result.save()
        if verbose:
            print(f"  Saved results to database")

    return {
        "scores": results,
        "statistics": stats,
        "model_name": model_name,
        "eval_name": eval_name,
        "failed_runs": failed_runs,
    }


def debug_eval(eval_factory: Callable[[int], Eval], seed: int = 0) -> dict:
    """
    Run a single evaluation for debugging purposes.

    Args:
        eval_factory: Factory function that creates Eval instances
        seed: Random seed for reproducible debugging

    Returns:
        Dictionary containing debug information and results
    """
    print(f"=== DEBUG MODE (seed={seed}) ===")

    try:
        eval_instance = eval_factory(seed)
        print(f"Eval: {eval_instance.name}")
        print(f"Model: {eval_instance.assistant.model}")
        print(f"Max turns: {eval_instance.max_turns}")
        print("\n" + "=" * 50)

        score = eval_instance.run()

        print("\n" + "=" * 50)
        print(f"Final Score: {score}")
        print("=" * 50)

        return {
            "score": score,
            "model_name": eval_instance.assistant.model,
            "eval_name": eval_instance.name,
            "chat_history": eval_instance.chat_history,
            "seed": seed,
        }

    except Exception as e:
        print(f"DEBUG EVAL FAILED: {str(e)}")
        import traceback

        traceback.print_exc()
        return {"score": 0.0, "error": str(e), "seed": seed}
