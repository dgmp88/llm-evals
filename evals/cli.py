"""
Unified CLI for running all evaluations.
"""
from typing import Optional

import typer
from typing_extensions import Annotated

# Import all evaluation modules to trigger registration
import evals.math  # noqa: F401
import evals.tictactoe  # noqa: F401
from evals.core import batch_eval, debug_eval
from evals.registry import create_eval_factory, get_eval_config, get_eval_names

app = typer.Typer(help="Unified command-line interface for all evaluations.")


@app.command()
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


@app.command()
def run(
    eval_name: Annotated[str, typer.Argument(help="Name of the evaluation to run")],
    model: Annotated[
        str, typer.Argument(help="Model name (e.g., 'gpt-4', 'claude-3-sonnet')")
    ],
    runs: Annotated[
        Optional[int],
        typer.Option(help="Number of evaluation runs (uses default if not specified)"),
    ] = None,
    save_results: Annotated[
        bool, typer.Option(help="Whether to save results to database")
    ] = True,
    verbose: Annotated[
        bool, typer.Option(help="Whether to print detailed output")
    ] = True,
    max_workers: Annotated[
        Optional[int], typer.Option(help="Maximum number of concurrent workers")
    ] = None,
):
    """Run a batch evaluation."""
    if eval_name not in get_eval_names():
        print(f"Error: Unknown evaluation '{eval_name}'")
        print(f"Available evaluations: {', '.join(get_eval_names())}")
        raise typer.Exit(1)

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


@app.command()
def debug(
    eval_name: Annotated[str, typer.Argument(help="Name of the evaluation to debug")],
    model: Annotated[
        str, typer.Argument(help="Model name (e.g., 'gpt-4', 'claude-3-sonnet')")
    ],
    seed: Annotated[
        int, typer.Option(help="Random seed for reproducible debugging")
    ] = 0,
):
    """Debug a single evaluation run."""
    if eval_name not in get_eval_names():
        print(f"Error: Unknown evaluation '{eval_name}'")
        print(f"Available evaluations: {', '.join(get_eval_names())}")
        raise typer.Exit(1)

    print(f"Debugging {eval_name} with model {model}")

    # Create evaluation factory
    eval_factory = create_eval_factory(eval_name, model)

    # Run debug evaluation
    result = debug_eval(eval_factory, seed=seed)

    return result


@app.command()
def info(
    eval_name: Annotated[str, typer.Argument(help="Name of the evaluation")],
):
    """Show detailed information about a specific evaluation."""
    if eval_name not in get_eval_names():
        print(f"Error: Unknown evaluation '{eval_name}'")
        print(f"Available evaluations: {', '.join(get_eval_names())}")
        raise typer.Exit(1)

    config = get_eval_config(eval_name)

    print(f"Evaluation: {eval_name}")
    print("-" * 50)
    print(f"Description: {config.get('description', 'No description available')}")
    print(f"Default runs: {config.get('default_runs', 10)}")

    default_params = config.get("default_params", {})
    if default_params:
        print("Default parameters:")
        for key, value in default_params.items():
            print(f"  {key}: {value}")
    else:
        print("No configurable parameters")


def main():
    """Main entry point for the CLI."""
    app()


if __name__ == "__main__":
    main()
