# Unified Evaluation CLI

The evaluation framework now includes a unified CLI that makes it easy to run and debug any evaluation without needing separate scripts.

## Quick Start

```bash
# List all available evaluations
python -m evals list

# Run a batch evaluation
python -m evals run math gpt-4 --runs 100

# Debug a single evaluation
python -m evals debug tictactoe_random gpt-4 --seed 42

# Get info about a specific evaluation
python -m evals info math
```

## Commands

### `list`
Shows all available evaluations with descriptions and default parameters.

```bash
python -m evals list
```

### `run`
Runs a batch evaluation with the specified parameters.

```bash
python -m evals run <eval_name> <model> [options]

# Examples:
python -m evals run math gpt-4 --runs 50
python -m evals run tictactoe_perfect claude-3-sonnet --runs 20
python -m evals run math gpt-4 --low 1 --high 100  # Custom parameters
```

**Options:**
- `--runs`: Number of evaluation runs (uses default if not specified)
- `--save_results`: Whether to save to database (default: True)
- `--verbose`: Whether to show detailed output (default: True)
- `--max_workers`: Maximum concurrent workers (default: 5)
- Additional eval-specific parameters (e.g., `--low`, `--high` for math)

### `debug`
Runs a single evaluation with detailed debugging output.

```bash
python -m evals debug <eval_name> <model> [options]

# Examples:
python -m evals debug math gpt-4
python -m evals debug tictactoe_random gpt-4 --seed 42
python -m evals debug math gpt-4 --low 1 --high 10  # Easier problems
```

**Options:**
- `--seed`: Random seed for reproducible debugging (default: 0)
- Additional eval-specific parameters

### `info`
Shows detailed information about a specific evaluation.

```bash
python -m evals info <eval_name>

# Example:
python -m evals info math
```

## Available Evaluations

### `math`
Basic arithmetic problems with random integers.
- **Default runs:** 50
- **Parameters:**
  - `low`: Minimum number (default: 100)
  - `high`: Maximum number (default: 1000)

### `tictactoe_random`
Tic-tac-toe against a random opponent.
- **Default runs:** 10
- **Score:** +1 for win, 0 for draw, -1 for loss

### `tictactoe_perfect`
Tic-tac-toe against a perfect AI opponent.
- **Default runs:** 10
- **Score:** +1 for win, 0 for draw, -1 for loss

## Adding New Evaluations

To add a new evaluation to the unified CLI:

1. Create your evaluation class inheriting from `Eval`
2. Register it using the `register_eval` function:

```python
from evals.registry import register_eval

register_eval(
    name="my_eval",
    factory=MyEval,
    description="Description of what this eval does",
    default_runs=20,
    # Default parameters
    param1="default_value",
    param2=42
)
```

3. Import your module in `evals/cli.py` to trigger registration

## Migration from Individual CLIs

The individual evaluation CLIs (`python math.py`, `python tictactoe.py`) still work for backward compatibility, but the unified CLI is recommended for new usage.

**Old way:**
```bash
python evals/math.py math gpt-4 50
python evals/tictactoe.py tic_tac_toe gpt-4 random 10
```

**New way:**
```bash
python -m evals run math gpt-4 --runs 50
python -m evals run tictactoe_random gpt-4 --runs 10
``` 