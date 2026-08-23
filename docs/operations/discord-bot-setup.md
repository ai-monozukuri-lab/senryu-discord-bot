---
title: Discord Bot セットアップ手順
description: Discord Developer Portal で Bot を作成・招待し、Message Content Intent、権限、ローカル起動、Railway 本番確認まで行う手順。
updated: 2026-08-23
read_when:
  - Discord Bot を新規作成、招待、再設定するとき。
  - Bot がオンラインなのに投稿へ反応しないとき。
  - DISCORD_TOKEN、権限、Message Content Intent を確認するとき。
---

# Discord Bot セットアップ手順

この Bot は Discord Gateway で新規メッセージを受け取り、本文を OpenAI へ送って俳句・川柳を判定する。Discord Developer Portal で Message Content Intent を有効にし、Bot に対象チャンネルの閲覧・投稿・添付権限を付与する必要がある。

公式の導入概要は [Discord Bots & Companion Apps](https://docs.discord.com/developers/bots/overview)、Gateway の Intent 仕様は [Gateway](https://docs.discord.com/developers/events/gateway) を参照する。

## 1. Developer Portal でアプリケーションを作る

1. [Discord Developer Portal](https://discord.com/developers/applications) を開き、Discord アカウントでログインする。
2. `New Application` からアプリケーション名を入力して作成する。
3. `General Information` に表示される **Application ID** を控える。Bot の招待 URL を手作業で作る場合に使う。
4. 左メニューの `Bot` を開き、Bot ユーザーを追加する。既存 Bot の場合はこの手順を飛ばす。

## 2. Bot Token を安全に発行する

1. `Bot` ページの `Reset Token` を実行し、表示された Token を一度だけ安全な場所へコピーする。
2. Token は `DISCORD_TOKEN` 環境変数へ設定する。Git にコミットしない、ログへ出力しない、チャットへ貼り付けない。
3. Token が漏れた場合は、直ちに `Reset Token` で再発行し、Railway の環境変数とローカルの値を更新する。

Token はパスワードと同じ扱いにする。Bot の表示名やアイコンは同じページから変更できるが、動作には影響しない。

## 3. Message Content Intent を有効にする

`Bot` ページの `Privileged Gateway Intents` で **Message Content Intent** を ON にして `Save Changes` を押す。

このリポジトリのコードも `discord.Intents.default()` に `message_content = True` を設定しているため、Portal 側とコード側の両方が有効である必要がある。Presence Intent と Server Members Intent はこの Bot には不要である。

## 4. Bot をサーバーへ招待する

`OAuth2` → `URL Generator` を開き、次を選択する。

- Scopes: `bot`
- Bot Permissions: `View Channel`、`Send Messages`、`Read Message History`、`Attach Files`

`Administrator` は選択しない。生成された URL をサーバー管理者へ渡して認可し、対象サーバーを選択する。Bot の招待後、対象チャンネルの権限上書きでも同じ 4 権限が許可されていることを確認する。

この Bot はスラッシュコマンドを使わないため `applications.commands` scope は不要である。将来スラッシュコマンドを追加する場合だけ scope を追加する。

## 5. ローカルで起動する

リポジトリのルートで Python 3.12 系の仮想環境を作り、依存関係をインストールする。

```bash
python3.12 -m venv .venv
.venv/bin/pip install -r requirements.txt
```

Token と OpenAI API キーを現在のシェルにだけ設定して起動する。

```bash
export DISCORD_TOKEN='ここにDiscord Bot Token'
export OPENAI_API_KEY='ここにOpenAI API key'
.venv/bin/python -m bot.main
```

起動ログに Bot のユーザー名が表示され、Discord のサーバー一覧で Bot がオンラインになれば Gateway 接続は成功している。OpenAI API キーは [API Keys](https://platform.openai.com/api-keys) で発行する。

コード変更を続けながらローカル Gateway を起動する場合は [ローカル Bot 開発手順](../development/local-bot.md) を参照する。

## 6. Railway へ本番デプロイする

1. Railway で GitHub リポジトリを接続した Service を 1 つ作る。
2. リポジトリの `Dockerfile` が自動検出されることを確認する。Start Command は `python -m bot.main` である。
3. Railway の Variables に次を登録する。

   - `DISCORD_TOKEN`
   - `OPENAI_API_KEY`

4. 必要なら [Railway 運用手順](railway.md) の任意変数を追加する。CLI で Project、Service、Variables を作成・設定する場合は [Railway CLI セットアップ手順](railway-cli.md) を参照する。
5. Deploy 後のログで Bot がオンラインになったことを確認する。

production は 1 インスタンスにする。重複防止用の `message.id` TTL キャッシュはプロセス内メモリだけに存在するため、複数インスタンスでは同じ投稿を二重処理する可能性がある。

## 7. GitHub Actions からデプロイする

`.github/workflows/deploy.yml` は `main` への push をトリガーに、テスト、lint、Railway CLI デプロイを実行する。GitHub リポジトリの `Settings` → `Secrets and variables` → `Actions` に次を登録する。

- `RAILWAY_TOKEN`
- `RAILWAY_PROJECT_ID`
- `RAILWAY_ENVIRONMENT_ID`（省略時は `production`）
- `RAILWAY_SERVICE_ID`（Service が 1 つだけなら省略可能）

Secrets に `DISCORD_TOKEN` や `OPENAI_API_KEY` を置く必要はない。これらは Railway Service の Variables にだけ登録する。

## 8. 動作確認（スモークテスト）

対象チャンネルへ次の順で投稿する。

1. `春の雨\n傘のとなりに\n猫の影` のような短詩を投稿する。
2. Bot が元投稿への reply として、作品種別、元本文、画像、講評、5 項目の星評価、総合評価を返すことを確認する。
3. 通常の質問や説明文を投稿し、Bot が返信しないことを確認する。
4. 同じメッセージイベントが再送されても、短時間に二重返信されないことを確認する。

画像内の日本語本文は AI 画像ではなく Pillow で合成される。背景テンプレートを変更する場合は [作品画像テンプレート生成仕様](../design/senryu-template.md) を参照する。

## 9. トラブルシューティング

### Bot がオフラインのまま

- Railway の `DISCORD_TOKEN` が未設定、空、または古い Token でないか確認する。
- Token を Reset した場合、Railway Variables を更新して再デプロイする。
- Railway のログに Gateway 接続エラーがないか確認する。

### Bot はオンラインだが返信しない

- Portal の Message Content Intent が ON か確認する。
- 対象チャンネルで `View Channel`、`Send Messages`、`Read Message History`、`Attach Files` が許可されているか確認する。
- Bot 自身の投稿、空本文、画像だけの投稿は仕様上無視される。
- 通常会話や質問は一次判定で対象外となり、返信しない。

### 返信が画像付きで届かない

- Pillow 合成またはフォント・テンプレート読み込みに失敗した対象投稿は、部分返信を行わない。
- Docker には Noto CJK フォントが含まれている。ログに `font` または `template` が出ていれば [Railway 運用手順](railway.md) の障害確認を行う。

### 同じ投稿が複数回返信される

- Railway の Service が複数インスタンスになっていないか確認する。
- プロセス再起動後は TTL キャッシュが消えるため、再送されたイベントが再処理される可能性がある。
