---
title: Railway 運用手順
description: 俳句・川柳講評 Discord Bot を Railway 常駐サービスとして動かすための環境変数とデプロイ手順。
updated: 2026-08-23
read_when:
  - Railway、Docker、GitHub Actions のデプロイ設定を変更するとき。
  - 本番の環境変数、Discord Intent、OpenAI モデルを設定するとき。
---

# Railway 運用手順

## Railway サービス

リポジトリの `Dockerfile` を使う常時実行サービスを 1 つだけ作成する。Start Command は Dockerfile の `python -m bot.main` を使う。Discord Gateway の WebSocket 接続を維持するため、スリープする Web サービスとして構成しない。

production のインスタンスは原則 1 つにする。重複処理キャッシュはプロセス内メモリだけに保持するため、複数インスタンスを起動すると同じ投稿を二重処理する可能性がある。

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

## GitHub Actions Secrets

`main` ブランチへの push で `.github/workflows/deploy.yml` がテスト、lint、Railway デプロイを順に実行する。リポジトリ Secrets に次を登録する。

- `RAILWAY_TOKEN`
- `RAILWAY_PROJECT_ID`

GitHub Actions は Railway CLI に `RAILWAY_TOKEN` を渡し、`RAILWAY_PROJECT_ID` の production サービスへ `railway up --ci` を実行する。

## 障害時の確認

- `DISCORD_TOKEN` または `OPENAI_API_KEY` が未設定なら起動時に終了する。
- フォントが見つからない場合、対象投稿は返信せずログに `font` エラーを出す。Docker イメージでは `fonts-noto-cjk` を導入済み。
- 画像テンプレートが見つからない場合、対象投稿は返信せずログに `template` エラーを出す。
