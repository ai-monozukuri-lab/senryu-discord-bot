---
title: ローカル Bot 開発手順
description: Discord Gateway に接続した Bot をローカルで起動し、実際の投稿で確認しながら安全に開発する手順。
updated: 2026-08-23
read_when:
  - ローカルで Discord Bot を起動して実投稿を確認するとき。
  - プロンプト、返信、画像合成、Gateway 接続を手元で開発するとき。
  - Railway の本番 Bot とローカル Bot の二重起動を避けるとき。
---

# ローカル Bot 開発手順

## 先に決める実行環境

ローカルで実際の Discord 投稿を処理すると、OpenAI API と Discord の本番状態を使う。次のどちらかを選ぶ。

- **推奨:** 開発用 Discord Application / Bot Token と、招待先の非公開テストサーバーを用意する。
- **一時確認:** Railway の production Service を停止またはスケールダウンしてから、production Token をローカルで使う。

同じ Token で Railway とローカルを同時に起動しない。重複防止キャッシュは各プロセス内だけにあるため、同じ投稿へ二重返信する可能性がある。Discord Application、Token、Message Content Intent、権限の準備は [Discord Bot セットアップ手順](../operations/discord-bot-setup.md) を参照する。

## 1. 依存関係を準備する

リポジトリのルートで Python 3.12 系を確認し、仮想環境を作る。

```bash
python3.12 --version
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

以降のコマンドは `.venv` を有効にした同じターミナルで実行する。別のターミナルで作業する場合は `source .venv/bin/activate` を繰り返す。

## 2. 環境変数を現在のシェルへ設定する

このアプリは `.env` ファイルを自動読み込みしない。秘密値をファイルへ保存せず、開発用 Token と OpenAI API キーを現在のシェルへ一時設定する。

```bash
export DISCORD_TOKEN='開発用Discord Bot Token'
export OPENAI_API_KEY='OpenAI API key'
```

必要に応じてモデルや TTL だけ上書きする。

```bash
export OPENAI_CLASSIFICATION_MODEL='gpt-5.6'
export OPENAI_REVIEW_MODEL='gpt-5.6'
export DEDUP_TTL_SECONDS='900'
export DEDUP_MAX_ENTRIES='10000'
```

Token や API キーをシェル履歴、スクリーンショット、Git 管理ファイルへ残さない。値を変更したら、起動中のプロセスを停止して再起動する。

## 3. Bot を起動する

```bash
python -m bot.main
```

`bot.main` は次の処理を行う。

1. `DISCORD_TOKEN` と `OPENAI_API_KEY` を検証する。
2. Discord Gateway 用の `message_content` intent を有効にする。
3. OpenAI アダプタ、固定画像テンプレート、TTL 重複防止を組み立てる。
4. `discord.py` の常時接続を開始する。

ログに Bot のユーザー名が表示され、開発用サーバーのメンバー一覧でオンラインになれば起動成功である。プロセスはフォアグラウンドで動くため、終了は `Ctrl-C`、コードや環境変数を変えた後は同じコマンドで再起動する。ファイル変更の自動 reload は実装していない。

## 4. 開発中の確認方法

Bot を起動したターミナルはそのままにし、別ターミナルでテストと lint を実行する。

```bash
source .venv/bin/activate
python -m pytest tests/test_models.py tests/test_dedupe.py tests/test_formatting.py \
  tests/test_image.py tests/test_service.py tests/test_openai_analyzer.py \
  tests/test_discord_bot.py tests/test_config.py -q
ruff check bot tests
```

これらのテストは Discord Gateway や OpenAI へ接続せず、fake の AI クライアント・メッセージを使う。プロンプトや Responses API の引数を変更した場合は `tests/test_openai_analyzer.py`、返信の見た目を変更した場合は `tests/test_formatting.py` と `tests/test_discord_bot.py`、画像を変更した場合は `tests/test_image.py` を先に実行する。

## 5. Discord でスモークテストする

開発用サーバーの専用チャンネルで、少量の投稿だけを使って確認する。

1. `春の雨\n傘のとなりに\n猫の影` のような短詩を投稿する。
2. 元投稿への reply として、俳句/川柳の種別、元本文、画像、講評、5 項目評価、総合評価が返ることを確認する。
3. `今日はいい天気ですね` のような通常文を投稿し、返信しないことを確認する。
4. 同じメッセージを Gateway が再送しても、短時間に二重返信されないことを確認する。

通常文でも一次判定の OpenAI 呼び出しが 1 回発生し、対象作品では判定＋講評の最大 2 回が発生する。API コストとレート制限に配慮し、テスト用チャンネル以外で大量投稿しない。画像背景は API 生成せず、`assets/senryu_template.png` に Pillow で本文を合成する。

## 6. Docker で本番に近い確認をする（任意）

Docker の日本語フォントと固定テンプレートを含む起動経路を確認したい場合は、次を実行する。

```bash
docker build -t senryu-discord-bot:local .
docker run --rm \
  --env DISCORD_TOKEN \
  --env OPENAI_API_KEY \
  senryu-discord-bot:local
```

ホスト側で先に `export` した値だけをコンテナへ渡す。Docker 実行中も `Ctrl-C` で停止できる。ローカル Python 実行と Docker 実行を同時に行わない。

## 7. 停止・再起動・後片付け

- Bot を止める: 起動ターミナルで `Ctrl-C`。
- 仮想環境を抜ける: `deactivate`。
- 開発用 Token を無効化する: Developer Portal の `Bot` ページで `Reset Token` を実行し、必要なら Railway の Variables も更新する。
- Railway を停止していた場合: production Service を 1 インスタンスへ戻し、Railway のログでオンライン状態を確認する。

## 8. ローカル起動時のトラブルシュート

### `DISCORD_TOKEN is required` または `OPENAI_API_KEY is required`

環境変数が現在のシェルに存在しない。`export` を実行した同じターミナルから `python -m bot.main` を起動する。.env ファイルへ書いただけでは読み込まれない。

### Bot がオンラインだが反応しない

Developer Portal の Message Content Intent と、対象チャンネルの `View Channel`、`Send Messages`、`Read Message History`、`Attach Files` を確認する。Bot 自身の投稿、空本文、画像だけの投稿、通常会話は仕様上返信しない。

### `LoginFailure` や Gateway 接続エラー

Token の取り違え、Reset 後の古い値、別 Application の Bot を招待している可能性がある。開発用 Bot の Token を再発行し、環境変数を設定し直して再起動する。

### OpenAI エラーまたは画像付き返信が届かない

API キー、利用可能なモデル、API の利用上限を確認する。画像合成エラー時は部分返信を行わず、ログに `font` または `template` の原因を残す。固定テンプレートを更新する場合は [作品画像テンプレート生成仕様](../design/senryu-template.md) と `tests/test_image.py` を同時に確認する。
