# LLM Evals

Deployed at: https://llm-evals.streamlit.app/

## Setup

This project uses OpenRouter to access multiple LLM providers through a single API. 

1. Get an API key from [OpenRouter](https://openrouter.ai/)
2. Create a `.env` file in the project root with:
   ```
   OPENROUTER_API_KEY=your_api_key_here
   NEON_POSTGRES=your_postgres_connection_string
   ```

## Instructions

Run an eval using the Fire CLI. e.g.

`python -m evals.math openai/gpt-4o-mini`
`python -m evals.tictactoe anthropic/claude-3.5-haiku random`

## Available Models

The project supports models from multiple providers via OpenRouter:

- **OpenAI**: `openai/gpt-4o`, `openai/gpt-4o-mini`, `openai/o1-mini`, etc.
- **Anthropic**: `anthropic/claude-sonnet-4`, `anthropic/claude-3.5-haiku`, etc.
- **Google**: `google/gemini-flash-1.5`, `google/gemini-pro-1.5`, etc.
- **Meta**: `meta-llama/llama-3.1-70b-instruct`, `meta-llama/llama-3.3-70b-instruct`, etc.
- **DeepSeek**: `deepseek/deepseek-chat`, `deepseek/deepseek-r1`, etc.
- **Free models**: Many models have `:free` variants available

See `evals/types.py` for the complete list of supported models.
