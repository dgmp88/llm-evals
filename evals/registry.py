"""
Evaluation registry for centralized eval management.
"""
from typing import Any, Callable, Dict

from evals.core import Eval

# Registry to store all available evaluations
EVALS: Dict[str, Dict[str, Any]] = {}


def register_eval(
    name: str,
    factory: Callable[..., Eval],
    description: str = "",
    default_runs: int = 10,
    **default_params,
):
    """
    Register an evaluation in the global registry.

    Args:
        name: Unique name for the evaluation
        factory: Function that creates Eval instances
        description: Human-readable description
        default_runs: Default number of runs for batch evaluation
        **default_params: Default parameters for the evaluation
    """
    EVALS[name] = {
        "factory": factory,
        "description": description,
        "default_runs": default_runs,
        "default_params": default_params,
    }


def get_eval_names() -> list[str]:
    """Get list of all registered evaluation names."""
    return list(EVALS.keys())


def get_eval_config(name: str) -> Dict[str, Any]:
    """Get configuration for a specific evaluation."""
    if name not in EVALS:
        raise ValueError(f"Unknown evaluation: {name}. Available: {get_eval_names()}")
    return EVALS[name]


def create_eval_factory(name: str, model: str, **kwargs) -> Callable[[int], Eval]:
    """
    Create an evaluation factory function for the given eval name and parameters.

    Args:
        name: Name of the evaluation
        model: Model name to use
        **kwargs: Additional parameters to pass to the evaluation

    Returns:
        Factory function that takes a seed and returns an Eval instance
    """
    config = get_eval_config(name)
    factory = config["factory"]

    # Merge default params with provided kwargs
    params = {**config["default_params"], **kwargs}

    def eval_factory(seed: int) -> Eval:
        return factory(model=model, rng_seed=seed, **params)

    return eval_factory
