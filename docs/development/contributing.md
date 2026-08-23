---
title: Bot 開発ガイド
description: 俳句・川柳講評 Bot のローカル検証、コード境界、テンプレート更新方法をまとめた contributor 向けガイド。
updated: 2026-08-23
read_when:
  - Bot の機能、プロンプト、画像合成、Discord ハンドラを変更するとき。
  - テストや lint の実行方法を確認するとき。
  - 固定画像テンプレートを更新するとき。
---

# Bot 開発ガイド

## ローカル検証

Python 3.12 系で依存関係をインストールする。

```bash
python -m venv .venv
.venv/bin/pip install -r requirements.txt
```

コード変更時は、次の 2 つを実行する。

```bash
.venv/bin/python -m pytest
.venv/bin/ruff check bot tests scripts
```

テストは OpenAI、Discord Gateway、Railway へ接続せず、AI アダプタと Discord メッセージを fake に差し替える。対象テストが検証する範囲は、型契約、星表示、TTL 重複防止、固定テンプレート合成、一次判定後の呼び出し回数、返信本文・添付ファイルである。

## コード境界

- `bot/models.py`: OpenAI の構造化出力とアプリケーション結果の公開型。JSON キーの日本語 alias と 1〜5 の範囲を変更するときは `tests/test_models.py` を同時に更新する。
- `bot/ai.py`: Responses API の一次判定・二次講評アダプタ。本文は XML 風の区切りでデータとして渡し、本文内の命令をプロンプト命令として扱わない。
- `bot/service.py`: 「一次判定 → 対象時だけ二次講評 → Pillow 合成」の唯一のオーケストレーション境界。ここへ文字数や五・七・五のローカル判定を追加しない。
- `bot/image.py`: 固定テンプレートへ元本文を正確に描く Pillow 層。`normalized_lines` は使わず、Discord 本文を正本とする。
- `bot/discord_bot.py`: Bot 投稿・空本文・TTL 重複を除外し、対象結果だけを reply する。AI/合成エラー時は部分投稿を行わない。
- `bot/config.py` と `bot/main.py`: 環境変数の検証と Railway 起動配線。秘密値をログやドキュメントへ出さない。

## 固定テンプレートの更新

背景は OpenAI の画像 API ではなく、`assets/senryu_template.png` を使う。デザインを変更するときは、手作業で PNG だけを上書きせず、`scripts/create_template.py` を修正して次を実行する。

```bash
python scripts/create_template.py
python -m pytest tests/test_image.py
```

画像は 1024×1024 の正方形 PNG とし、本文の安全領域を空け、日本語の可読文字をテンプレートへ埋め込まない。日本語フォントは macOS のヒラギノまたは Docker の Noto CJK を探索するため、フォント探索候補を変更するときは Dockerfile と `bot/image.py` を一緒に確認する。

## 変更時に守る不変条件

- 通常投稿は OpenAI 呼び出し 1 回、対象投稿は最大 2 回。一次判定が対象外なら二次呼び出しをしない。
- 背景画像の生成 API は使わない。画像は固定テンプレート＋Pillow 合成で作る。
- 同じ `message.id` は TTL 中に一度だけ処理する。キャッシュはプロセス内だけなので production は 1 インスタンスにする。
- 作品本文は AI の正規化結果ではなく、Discord の元本文を画像と返信本文へ使う。
- API/画像処理に失敗した対象投稿は Discord へ部分結果を投稿しない。
