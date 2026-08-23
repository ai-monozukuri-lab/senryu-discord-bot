# 俳句・川柳講評 Discord Bot

Discord の投稿を OpenAI で判定し、俳句・川柳として鑑賞できる短詩に画像付きの講評を返信する Bot です。

## 主な仕様

- 一次判定が対象外なら返信しない
- 対象作品には判定・講評の最大 2 回の OpenAI 呼び出しを行う
- モデルは `gpt-5.6-luna`、推論 effort は `max` に固定
- 評価は `情景`、`余韻`、`独創性` の 3 項目と総合評価
- 作品本文は Yuji Syuku の縦書きで画像へ合成
- Discord の返信本文は次の形式

  ```text
  川柳を検出しました！
  総合評価: ★★★★☆
  情景: ★★★★☆
  余韻: ★★★★★
  独創性: ★★★★☆
  （講評本文）
  ```

- OpenAI 呼び出しごとに token 内訳と推定 USD を `openai_usage` JSON ログへ記録
- 同じ Discord `message.id` の短時間重複処理を抑止

## ローカル起動

Python 3.12 系を使います。

```bash
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
cp .env.local.example .env.local
```

`.env.local` に次の秘密値だけを設定します。

```dotenv
DISCORD_TOKEN=Discord Bot Token
OPENAI_API_KEY=OpenAI API key
```

起動:

```bash
python -m bot.main
```

モデル、推論設定、TTL、テンプレート、料金表などの非秘密設定はコードに固定しており、環境変数では変更しません。

## テストと lint

```bash
python -m pytest
ruff check bot tests
```

テストは実際の Discord Gateway や OpenAI APIへ接続せず、fake クライアントを使います。

## Railway デプロイ

Railway は Dockerfile で Bot を常時実行します。production は 1 replica、1 vCPU、0.5 GB RAM に設定済みです。

Deploy は自動 push ではなく手動実行です。

```bash
gh workflow run Deploy \
  --repo ai-monozukuri-lab/senryu-discord-bot \
  --ref main
```

Railway Service Variables には `DISCORD_TOKEN` と `OPENAI_API_KEY` だけを設定します。GitHub Actions には Railway の Project Token と Project / Environment / Service ID を設定します。

## ドキュメント

- [Discord Bot セットアップ](docs/operations/discord-bot-setup.md)
- [ローカル Bot 開発手順](docs/development/local-bot.md)
- [Railway 運用手順](docs/operations/railway.md)
- [Railway CLI セットアップ](docs/operations/railway-cli.md)
- [実装仕様](docs/specs/senryu-discord-bot.md)
- [作品画像・フォント仕様](docs/design/senryu-template.md)

## フォントライセンス

同梱の `assets/fonts/YujiSyuku-Regular.ttf` は Yuji Project の SIL Open Font License 1.1 で提供されています。ライセンス本文は `assets/fonts/OFL-Yuji.txt` にあります。
