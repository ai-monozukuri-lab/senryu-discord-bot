---
title: Railway 運用手順
description: 俳句・川柳講評 Discord Bot を Railway 常駐サービスとして動かすための環境変数とデプロイ手順。
updated: 2026-08-23
read_when:
  - Railway、Docker、GitHub Actions のデプロイ設定を変更するとき。
  - 本番の環境変数、Discord Intent、OpenAI モデルを設定するとき。
---

# Railway 運用手順

CLI での初回プロジェクト作成、既存プロジェクトへの接続、変数設定、デプロイ確認は [Railway CLI セットアップ手順](railway-cli.md) を参照する。

## Railway サービス

リポジトリの `Dockerfile` を使う常時実行サービスを 1 つだけ作成する。Start Command は Dockerfile の `python -m bot.main` を使う。Discord Gateway の WebSocket 接続を維持するため、スリープする Web サービスとして構成しない。

production のインスタンスは原則 1 つにする。重複処理キャッシュはプロセス内メモリだけに保持するため、複数インスタンスを起動すると同じ投稿を二重処理する可能性がある。

## リソース構成

production Service は Free/Trial 枠を優先し、次の上限で設定している。

- レプリカ: 1
- CPU 上限: 1 vCPU
- メモリ上限: 0.5 GB（約 512 MB）

Railway は実使用量で課金し、Replica Limits は急な使用量の上限を設定するもの。上限を下げても常時稼働の実使用量やプラン料金が自動的に 0 になるわけではなく、低すぎる上限では Bot がクラッシュする可能性がある。CPU/RAM の実測値は `railway metrics --cpu --memory --since 1h --json` または Dashboard の Metrics で確認する。

公式の費用・上限の説明は [Cost Control](https://docs.railway.com/pricing/cost-control) と [Pricing Plans](https://docs.railway.com/pricing/plans) を参照する。

## Railway 環境変数

必須:

- `DISCORD_TOKEN`
- `OPENAI_API_KEY`

任意:

- `OPENAI_CLASSIFICATION_MODEL`（既定 `gpt-5.6`）
- `OPENAI_REVIEW_MODEL`（既定 `gpt-5.6`）
- `IMAGE_TEMPLATE_PATH`（Docker 既定 `/app/assets/senryu_template.png`）
- `FONT_PATH`（未指定時は macOS ヒラギノ / Linux Noto CJK を探索）
- `DEDUP_TTL_SECONDS`（既定 900）
- `DEDUP_MAX_ENTRIES`（既定 10000）

Discord Developer Portal では Message Content Intent を有効にし、Bot の招待時にもメッセージ閲覧権限を与える。

初回のアプリ作成、Token 発行、招待 URL、チャンネル権限は [Discord Bot セットアップ手順](discord-bot-setup.md) を参照する。

## GitHub Actions Secrets

`.github/workflows/deploy.yml` は `workflow_dispatch` による手動実行で、テスト、lint、Railway デプロイを順に実行する。リポジトリ Secrets に次を登録する。

- `RAILWAY_TOKEN`
- `RAILWAY_PROJECT_ID`
- `RAILWAY_ENVIRONMENT_ID`（未登録時は workflow が `production` を使用）
- `RAILWAY_SERVICE_ID`（Service が 1 つだけなら省略可能）

GitHub Actions の画面で `Deploy` workflow の `Run workflow` を押すか、次の CLI で明示的に実行する。

```bash
gh workflow run Deploy --repo ai-monozukuri-lab/senryu-discord-bot --ref main
```

workflow は Railway CLI に `RAILWAY_TOKEN` を渡し、`RAILWAY_PROJECT_ID`、`RAILWAY_ENVIRONMENT_ID`、任意の `RAILWAY_SERVICE_ID` を明示して `railway up --ci` を実行する。`RAILWAY_TOKEN` は対象 Project の Project Token を使う。

## 障害時の確認

- `DISCORD_TOKEN` または `OPENAI_API_KEY` が未設定なら起動時に終了する。
- フォントが見つからない場合、対象投稿は返信せずログに `font` エラーを出す。Docker イメージでは `fonts-noto-cjk` を導入済み。
- 画像テンプレートが見つからない場合、対象投稿は返信せずログに `template` エラーを出す。
