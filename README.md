# QA Agent Action

AI-powered QA Agent for your GitHub repository.
It uses **Strands** for LLM orchestration and **Serena** for autonomous codebase exploration.

## Features

- **Autonomous Exploration**: actively explores your codebase (file search, read, git log) to answer questions.
- **Provider Agnostic**: Supports OpenAI, Anthropic, and Gemini.
- **Easy Integration**: runs as a GitHub Composite Action.

## Usage

Create a workflow file (e.g., `.github/workflows/qa.yml`):

```yaml
name: QA Agent
on:
  issue_comment:
    types: [created]

jobs:
  qa:
    if: contains(github.event.comment.body, '/ask')
    runs-on: ubuntu-latest
    permissions:
      contents: read
      issues: write
    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Run QA Agent
        uses: HawkClaws/QAAgent@main
        env:
          # Set the API key for your chosen provider
          OPENAI_API_KEY: ${{ secrets.OPENAI_API_KEY }}
          # ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}
          # GEMINI_API_KEY: ${{ secrets.GEMINI_API_KEY }}
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
        with:
          query: ${{ github.event.comment.body }}
          # provider: openai  # optional (default: openai)
          # model: gpt-4o     # optional
```

## Inputs

| Input      | Description                                                | Required | Default          |
| ---------- | ---------------------------------------------------------- | -------- | ---------------- |
| `query`    | The question or instruction for the agent.                 | **Yes**  | -                |
| `provider` | LLM Provider (`openai`, `anthropic`, `gemini`).            | No       | `openai`         |
| `model`    | Specific model name (e.g., `gpt-4o`, `claude-3-5-sonnet`). | No       | Provider default |

## Development

To run locally for contribution:

```bash
# Setup
python3.11 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Run
export OPENAI_API_KEY="..."
python qa_agent.py --query "Explain this repo"
```
