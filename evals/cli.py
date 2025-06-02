"""
Unified CLI for running all evaluations.
"""

from typing import Optional

from cyclopts import App

# Import all evaluation modules to trigger registration
import evals.math  # noqa: F401
import evals.tictactoe  # noqa: F401
from evals.core import batch_eval, debug_eval
from evals.registry import create_eval_factory, get_eval_config, get_eval_names

app = App()


@app.command
def list():
    """List all available evaluations with descriptions."""
    print("Available evaluations:")
    print("-" * 50)

    for name in sorted(get_eval_names()):
        config = get_eval_config(name)
        description = config.get("description", "No description available")
        default_runs = config.get("default_runs", 10)

        print(f"{name:20} | {description}")
        print(f"{'':20} | Default runs: {default_runs}")

        # Show default parameters if any
        default_params = config.get("default_params", {})
        if default_params:
            params_str = ", ".join(f"{k}={v}" for k, v in default_params.items())
            print(f"{'':20} | Default params: {params_str}")

        print()


@app.command
def run(
    eval_name: str,
    model: str,
    *,
    runs: Optional[int] = None,
    save_results: bool = True,
    verbose: bool = True,
    max_workers: Optional[int] = None,
):
    """Run a batch evaluation.

    Parameters
    ----------
    eval_name
        Name of the evaluation to run
    model
        Model name (e.g., 'gpt-4', 'claude-3-sonnet')
    runs
        Number of evaluation runs (uses default if not specified)
    save_results
        Whether to save results to database
    verbose
        Whether to print detailed output
    max_workers
        Maximum number of concurrent workers
    """
    if eval_name not in get_eval_names():
        print(f"Error: Unknown evaluation '{eval_name}'")
        print(f"Available evaluations: {', '.join(get_eval_names())}")
        exit(1)

    config = get_eval_config(eval_name)

    # Use default runs if not specified
    if runs is None:
        runs = config["default_runs"]

    print(f"Running {eval_name} with model {model}")
    print(f"Runs: {runs}")
    print("-" * 50)

    # Create evaluation factory
    eval_factory = create_eval_factory(eval_name, model)

    # Run batch evaluation
    results = batch_eval(
        num_runs=runs,
        eval_factory=eval_factory,
        max_workers=max_workers,
        save_results=save_results,
        verbose=verbose,
    )

    return results


@app.command
def debug(
    eval_name: str,
    model: str,
    *,
    seed: int = 0,
):
    """Debug a single evaluation run.

    Parameters
    ----------
    eval_name
        Name of the evaluation to debug
    model
        Model name (e.g., 'gpt-4', 'claude-3-sonnet')
    seed
        Random seed for reproducible debugging
    """
    if eval_name not in get_eval_names():
        print(f"Error: Unknown evaluation '{eval_name}'")
        print(f"Available evaluations: {', '.join(get_eval_names())}")
        exit(1)

    print(f"Debugging {eval_name} with model {model}")

    # Create evaluation factory
    eval_factory = create_eval_factory(eval_name, model)

    # Run debug evaluation
    result = debug_eval(eval_factory, seed=seed)

    return result


def main():
    """Main entry point for the CLI."""
    app()


if __name__ == "__main__":
    main()
