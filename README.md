# QA Agent

Strands Agents を使用したGitHub Actions QAエージェントです。
`strands-agents` フレームワークと `serena-agent` ツールセットを組み合わせ、リポジトリに関する質問に自律的に回答します。


## セットアップ手順

### 1. シークレットの設定
GitHubリポジトリの `Settings` -> `Secrets and variables` -> `Actions` に以下のシークレットを追加してください。使用したいプロバイダーのキーだけで構いません。

- `OPENAI_API_KEY`: OpenAI APIキー
- `ANTHROPIC_API_KEY`: Anthropic (Claude) APIキー
- `GEMINI_API_KEY`: Google Gemini APIキー (または `GOOGLE_API_KEY`)

Note: `qa_agent.py` 内のロジックにより、ワークフローで使用するプロバイダーに対応したキーが必要です。

### 2. ワークフローの確認
`.github/workflows/qa_agent.yml` がリポジトリのデフォルトブランチに含まれていることを確認してください。

## 使い方

### エージェントへの質問
Issueのコメントで `/ask` から始まる文章を投稿してください。

例:
```
/ask READMEには何が書いてありますか？
```

```
/ask 最新のコミットで変更された点は何ですか？
```

### プロバイダーの切り替え
`.github/workflows/qa_agent.yml` は GitHub Actions の `Settings` -> `Secrets and variables` -> `Variables` で設定された以下の変数を参照します。

- `QA_AGENT_PROVIDER`: プロバイダー名 (`openai`, `anthropic`, `gemini`)。デフォルトは `openai`。
- `QA_AGENT_MODEL`: モデル名 (例: `gpt-5.2`)。指定しない場合はプロバイダーのデフォルトが使われます。

これらの変数を設定することで、コードを変更せずにプロバイダーやモデルを切り替え可能です。

## ローカル実行
ローカルで動作確認する場合は以下のように実行します。
**注意**: `serena-agent` は Python 3.12以上では動作保証されていません (3.11推奨)。

```bash
# 仮想環境の作成 (Python 3.11)
python3.11 -m venv .venv
source .venv/bin/activate
pip install "strands-agents[openai,anthropic,gemini]" serena-agent

# 実行
export OPENAI_API_KEY="sk-..."
python qa_agent.py --query "READMEの内容は？"
```
