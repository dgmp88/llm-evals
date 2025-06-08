"""
Unified CLI for running all evaluations.
"""

from typing import Optional

from cyclopts import App

# Import all evaluation modules to trigger registration
import evals.math  # noqa: F401
import evals.tictactoe  # noqa: F401
from evals.core import batch_eval
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
    eval_names: str,
    models: str,
    *,
    runs: Optional[int] = None,
    save_results: bool = True,
    verbose: bool = True,
    max_workers: Optional[int] = None,
):
    """Run batch evaluations on multiple models and evaluations.

    Parameters
    ----------
    eval_names
        Comma-separated list of evaluation names to run (e.g., 'math,tictactoe')
    models
        Comma-separated list of model names (e.g., 'gpt-4,claude-3-sonnet')
    runs
        Number of evaluation runs (uses default if not specified)
    save_results
        Whether to save results to database
    verbose
        Whether to print detailed output
    max_workers
        Maximum number of concurrent workers
    """
    # Parse comma-separated strings
    eval_list = [name.strip() for name in eval_names.split(",")]
    model_list = [name.strip() for name in models.split(",")]

    # Validate all eval names
    available_evals = get_eval_names()
    invalid_evals = [name for name in eval_list if name not in available_evals]
    if invalid_evals:
        print(f"Error: Unknown evaluation(s): {', '.join(invalid_evals)}")
        print(f"Available evaluations: {', '.join(available_evals)}")
        exit(1)

    print(f"Running {len(eval_list)} evaluation(s) on {len(model_list)} model(s)")
    print(f"Evaluations: {', '.join(eval_list)}")
    print(f"Models: {', '.join(model_list)}")
    print("-" * 50)

    all_results = {}
    failed_combinations = []

    for eval_name in eval_list:
        config = get_eval_config(eval_name)

        # Use default runs if not specified
        eval_runs = runs if runs is not None else config["default_runs"]

        for model in model_list:
            print(f"\n🔄 Running {eval_name} with model {model} ({eval_runs} runs)")

            # Create evaluation factory
            eval_factory = create_eval_factory(eval_name, model)

            try:
                # Run batch evaluation
                results = batch_eval(
                    num_runs=eval_runs,
                    eval_factory=eval_factory,
                    max_workers=max_workers,
                    save_results=save_results,
                    verbose=verbose,
                )

                # Store results
                if eval_name not in all_results:
                    all_results[eval_name] = {}
                all_results[eval_name][model] = results

                print(f"✅ Completed {eval_name} with {model}")

            except ValueError as e:
                # Handle case where all evaluations failed for this model/eval combination
                if "No evaluations completed successfully" in str(e):
                    print(f"❌ All evaluations failed for {eval_name} with {model}")
                    print(f"   Error: {str(e)}")
                    failed_combinations.append((eval_name, model))

                    # Store failure information
                    if eval_name not in all_results:
                        all_results[eval_name] = {}
                    all_results[eval_name][model] = {"error": str(e), "failed": True}
                else:
                    # Re-raise other ValueError types
                    raise
            except Exception as e:
                # Handle other unexpected errors
                print(f"❌ Unexpected error for {eval_name} with {model}: {str(e)}")
                failed_combinations.append((eval_name, model))

                # Store failure information
                if eval_name not in all_results:
                    all_results[eval_name] = {}
                all_results[eval_name][model] = {"error": str(e), "failed": True}

    print("\n" + "=" * 50)
    print("📊 SUMMARY OF ALL RESULTS")
    print("=" * 50)

    for eval_name in eval_list:
        print(f"\n{eval_name}:")
        for model in model_list:
            if eval_name in all_results and model in all_results[eval_name]:
                results = all_results[eval_name][model]
                if isinstance(results, dict) and results.get("failed", False):
                    print(
                        f"  {model}: FAILED - {results.get('error', 'Unknown error')}"
                    )
                else:
                    print(f"  {model}: {results}")
            else:
                print(f"  {model}: No results (skipped)")

    # Report failed combinations at the end
    if failed_combinations:
        print("\n" + "⚠️" * 20)
        print("❌ FAILED EVALUATIONS SUMMARY")
        print("⚠️" * 20)
        print(f"\n{len(failed_combinations)} evaluation(s) completely failed:")
        for eval_name, model in failed_combinations:
            print(f"  • {eval_name} with {model}")
        print("\nConsider checking:")
        print("  - Model availability and configuration")
        print("  - Network connectivity")
        print("  - API keys and authentication")
        print("  - Evaluation parameters and requirements")
    else:
        print("\n✅ All evaluations completed successfully!")

    return all_results


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

    eval_instance = eval_factory(seed)
    score = eval_instance.run()

    print(f"Final Score: {score}")


def main():
    """Main entry point for the CLI."""
    app()


if __name__ == "__main__":
    main()
