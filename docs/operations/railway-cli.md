---
title: Railway CLI セットアップ手順
description: Railway CLI で俳句・川柳講評 Bot の Project、Environment、Service、Variables を安全に作成・接続・デプロイ・確認する手順。
updated: 2026-08-23
read_when:
  - Railway の Project、Environment、Service を CLI で初期化するとき。
  - Railway Variables、デプロイ、ログ、GitHub Actions の対象を CLI で確認するとき。
  - Railway CLI で外部リソースを作成・変更する前に対象と権限を確認するとき。
---

# Railway CLI セットアップ手順

この手順は、リポジトリの `Dockerfile` を使って Discord Bot を Railway の常時実行 Service として作成・デプロイするためのもの。Railway CLI は Project の作成、既存 Project への接続、Variables の設定、デプロイ、ログ確認を実行できる。公式のコマンド一覧は [Railway CLI](https://docs.railway.com/cli)、デプロイ仕様は [Deploying with the CLI](https://docs.railway.com/cli/deploying) を参照する。

## 重要な前提

- production の Bot Service は 1 インスタンスだけにする。
- Project、Environment、Service の対象を ID または名前で明示する。別 Project へ誤 deploy しないよう、`railway status --json` で確認してから変更する。
- `DISCORD_TOKEN` と `OPENAI_API_KEY` は秘密値。チャット、Git、CI ログ、コマンド出力へ貼り付けない。
- CLI の `RAILWAY_TOKEN` は Project Token、`RAILWAY_API_TOKEN` は Account/Workspace Token で用途が異なる。両方を同時に設定しない。
- `railway link` はカレントディレクトリに `.railway/` を作るため、リポジトリでは `.gitignore` で除外している。

## 1. CLI をインストールする

macOS では Homebrew を推奨する。

```bash
brew install railway
railway --version
```

Homebrew がない場合や別 OS では、公式の [CLI Installation](https://docs.railway.com/cli) にある npm またはインストーラを使う。

## 2. 認証する

手元で初回セットアップする場合はブラウザ認証を行う。

```bash
railway login
railway whoami
```

ブラウザを開けない環境では `railway login --browserless` を使う。既存 Project 内の自動化では、Railway Dashboard で発行した Project Token を現在のシェルへ設定する。

```bash
export RAILWAY_TOKEN='Project Token'
```

Project 自体の作成や Workspace 跨ぎの操作には Account/Workspace Token または対話ログインが必要になる場合がある。

```bash
export RAILWAY_API_TOKEN='Account or Workspace Token'
```

`RAILWAY_TOKEN` と `RAILWAY_API_TOKEN` は同時に設定しない。Token の値はこのチャットへ送らず、ローカルの環境変数または GitHub Secrets だけで管理する。

## 3. 新しい Project と Service を作る

### 対話的に作る（推奨）

リポジトリのルートで、対象 Workspace と Project 名を確認しながら実行する。

```bash
railway init --name senryu-discord-bot
railway up
```

`railway init` は Project を作成してカレントディレクトリへリンクする。初回 `railway up` は Dockerfile を検出し、現在のコードから Service を作成・デプロイする。作成先を誤らないよう、コマンドの確認プロンプトを飛ばす `--yes` は対象を確認した後だけ使う。

### 非対話的に新規作成する

Workspace ID が確定している場合だけ使う。

```bash
railway init --name senryu-discord-bot --workspace "$RAILWAY_WORKSPACE_ID" --json
railway up --ci
```

既存 Project がある場合に `railway up --new` を使うと別 Project を作成するため、使わない。

## 4. 既存 Project / Environment / Service へ接続する

Dashboard または `railway list` で ID を確認し、対象を明示してリンクする。

```bash
export RAILWAY_PROJECT_ID='project-id'
export RAILWAY_ENVIRONMENT_ID='environment-id-or-production'
export RAILWAY_SERVICE_ID='service-id-or-bot-service'

railway link \
  --project "$RAILWAY_PROJECT_ID" \
  --environment "$RAILWAY_ENVIRONMENT_ID" \
  --service "$RAILWAY_SERVICE_ID" \
  --json
railway status --json
```

Service がまだない場合は、対話的に `railway add` で追加するか、対象 Project のルートで `railway up` を実行する。Discord Bot はデータベースを使わないため、追加するのは Dockerfile から起動する Bot Service だけでよい。

## 5. Variables を CLI で登録する

まずローカルのシェルへ秘密値を設定する。値をコマンドライン引数へ直接書かず、`--stdin` で渡す。

```bash
export DISCORD_TOKEN='開発または本番のDiscord Bot Token'
export OPENAI_API_KEY='OpenAI API key'

printf '%s' "$DISCORD_TOKEN" \
  | railway variable set DISCORD_TOKEN --stdin --skip-deploys
printf '%s' "$OPENAI_API_KEY" \
  | railway variable set OPENAI_API_KEY --stdin --skip-deploys
```

`railway variable set` はリンク済みの Project / Environment / Service を対象にする。複数の環境や Service を扱う場合は、先に `railway link` を切り替えてから実行する。設定後はキーだけを確認し、秘密値を出力しない。

```bash
railway variable list --json
```

モデル、推論 effort、TTL、テンプレート、フォント、料金表などの非秘密設定は `bot/config.py` と `bot/usage.py` にコード化しているため、Railway Variables へ追加しない。

Variables を設定しただけでデプロイを待たず、次のデプロイ手順でまとめて反映する。

## 6. Dockerfile からデプロイする

Project、Environment、Service を明示してデプロイする。`--project` を使う場合は `--environment` も指定する。

```bash
railway up \
  --ci \
  --project "$RAILWAY_PROJECT_ID" \
  --environment "$RAILWAY_ENVIRONMENT_ID" \
  --service "$RAILWAY_SERVICE_ID"
```

Railway はリポジトリの `Dockerfile` をビルドし、`python -m bot.main` を起動する。Bot は HTTP ポートを公開しないため、Domain を追加する必要はない。デプロイが成功したら、Gateway 接続ログを確認する。

## 7. 状態・ログ・デプロイを確認する

```bash
railway status --json
railway deployment list --json
railway logs \
  --project "$RAILWAY_PROJECT_ID" \
  --environment "$RAILWAY_ENVIRONMENT_ID" \
  --service "$RAILWAY_SERVICE_ID" \
  -n 100
```

Dashboard を開く場合は `railway open` を使う。デプロイ失敗時は `railway logs --build` と Dockerfile のビルドログを確認する。Token や API キーがログへ出ていないことも確認する。

## リソース上限

`railway scale` はリージョンごとのレプリカ数を変更するコマンドであり、CPU/RAM の上限設定とは別である。CPU/RAM は Dashboard の Service → Settings → Deploy → Replica Limits で設定する。現在の Bot は 1 replica、1 vCPU、0.5 GB RAM に設定している。変更後は `railway metrics --cpu --memory --since 10m --json` と Service status を確認する。

## 8. GitHub Actions へ接続する

`.github/workflows/deploy.yml` は GitHub Actions の `Run workflow` または `gh workflow run` による手動実行で、テスト、lint、Railway CLI デプロイを実行する。次の GitHub Secrets を登録する。

- `RAILWAY_TOKEN`: 対象 Project の Project Token
- `RAILWAY_PROJECT_ID`: 対象 Project ID
- `RAILWAY_ENVIRONMENT_ID`: production Environment ID（省略時は workflow が `production` を使用）
- `RAILWAY_SERVICE_ID`: Bot Service ID（Service が 1 つだけなら省略可能）

GitHub Actions には `DISCORD_TOKEN` と `OPENAI_API_KEY` を渡さない。これらは Railway Service Variables に設定済みであることが前提。Deploy 前に対象 IDs を確認し、Project Token の権限を対象 Project に限定する。

```bash
gh workflow run Deploy --repo ai-monozukuri-lab/senryu-discord-bot --ref main
```

## 9. 私が CLI で実行できる範囲

このワークスペースから Railway CLI を実行する場合、次の条件が必要になる。

1. `railway` CLI がインストールされていること。
2. ユーザーがブラウザで `railway login` を完了するか、現在の環境へ `RAILWAY_TOKEN` / `RAILWAY_API_TOKEN` を設定すること。
3. 対象 `Project ID`、`Environment ID`、`Service ID` と、production へ変更してよいという明示的な確認があること。

条件が整えば、私が `railway status`、`railway logs`、`railway up`、Variables 設定などを CLI で実行できる。ただし、Project 作成、Service 作成、Variables 変更、デプロイ、再起動は外部状態を変更するため、対象と操作内容を確認してから実行する。Token の貼り付けを依頼することはない。

## 10. ロールバックと停止

- 最新デプロイを再適用する: `railway redeploy`
- Service を再起動する: `railway restart`
- production の二重起動を避けるため、ローカル Bot を試す前に Service の稼働数を 1 つへ保つ。
- `railway down` や Project / Environment の削除は破壊的操作なので、この手順では自動実行しない。
