# QA Agent Action (日本語)

あなたのGitHubリポジトリのためのAI駆動型QAエージェントです。
LLMのオーケストレーションに **Strands** を、自律的なコードベース探索に **Serena** を使用しています。

[English README](README.md)

## 特徴

- **自律的探索**: ファイル検索、読み取り、gitログなどのツールを駆使して、リポジトリの内容を能動的に調査し回答します。
- **マルチプロバイダー対応**: OpenAI, Anthropic, Gemini をサポートしています。
- **簡単な導入**: GitHub Composite Action として動作するため、既存のワークフローに簡単に追加できます。

## 使い方

ワークフローファイル (例: `.github/workflows/qa.yml`) を作成します：

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
          # 使用するプロバイダーのAPIキーを設定してください
          OPENAI_API_KEY: ${{ secrets.OPENAI_API_KEY }}
          # ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}
          # GEMINI_API_KEY: ${{ secrets.GEMINI_API_KEY }}
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
        with:
          query: ${{ github.event.comment.body }}
          # provider: openai  # 任意 (デフォルト: openai)
          # model: gpt-4o     # 任意
```

## 入力パラメータ (Inputs)

| パラメータ | 説明                                                 | 必須     | デフォルト               |
| ---------- | ---------------------------------------------------- | -------- | ------------------------ |
| `query`    | エージェントへの質問または指示。                     | **はい** | -                        |
| `provider` | LLMプロバイダー (`openai`, `anthropic`, `gemini`)。  | いいえ   | `openai`                 |
| `model`    | 特定のモデル名 (例: `gpt-4o`, `claude-3-5-sonnet`)。 | いいえ   | プロバイダーのデフォルト |

## 開発用

ローカルで動作確認を行う場合：

```bash
# セットアップ
python3.11 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# 実行
export OPENAI_API_KEY="..."
python qa_agent.py --query "このリポジトリについて説明して"
```
