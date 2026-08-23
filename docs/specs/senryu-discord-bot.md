---
title: 俳句・川柳講評 Discord Bot 実装仕様
description: Discord の短詩を AI で判定し、対象作品へ講評・評価・作品画像を返信する Bot の実装契約。
updated: 2026-08-23
read_when:
  - Bot の判定、講評、画像生成、Discord 投稿の挙動を変更するとき。
  - OpenAI API のモデル、構造化出力、環境変数、デプロイ設定を変更するとき。
  - 永続化または重複処理防止の実装を変更するとき。
---

# 俳句・川柳講評 Discord Bot 実装仕様

## 1. 目的と適用範囲

Discord の新規投稿を受け取り、俳句・川柳・それに近い短詩だけを AI で検出する。対象作品には、具体的な表現に触れた親しみやすい講評、3 項目の 5 段階評価、総合評価、和風の作品画像を返信する。

本仕様では、Bot のアプリケーションコード、OpenAI 呼び出し契約、画像合成、重複処理防止、Docker/Railway/GitHub Actions の最小構成を定義する。Discord や OpenAI の実アカウント設定そのものは対象外とする。

## 2. 処理不変条件

- 一次判定に 5・7・5、文字数、改行数などのローカル判定を使わない。判定は AI の構造化出力だけで決める。
- 通常投稿は一次判定の OpenAI 呼び出し 1 回で終了する。
- 対象投稿は一次判定と二次生成を合わせて OpenAI API 呼び出しを最大 2 回とする。
- 二次生成の 1 回の Responses API リクエストで、構造化された講評と評価を取得する。背景画像は固定テンプレートを使うため、画像生成 API は呼び出さない。
- 背景テンプレートに日本語本文は含めず、Bot が Pillow で元の作品本文を合成する。
- Bot 自身の投稿は無視する。同じ Discord `message.id` は短時間に一度だけ処理する。
- 対象外投稿には Discord への返信を行わない。
- OpenAI または画像合成に失敗した対象投稿は、部分的な講評を投稿せずログに記録する。

## 3. 公開データ型と JSON 契約

### 3.1 一次判定

```json
{
  "is_poem": true,
  "type": "senryu",
  "confidence": 0.91,
  "normalized_lines": ["第一句", "第二句", "第三句"]
}
```

- `type` は `haiku`、`senryu`、`other` のいずれか。
- `confidence` は 0 以上 1 以下。
- `normalized_lines` は AI が鑑賞用に整理した行であり、画像に描く本文の正本ではない。
- 対象作品は `is_poem == true` かつ `type in {haiku, senryu}` とする。

### 3.2 二次生成

```json
{
  "comment": "5文程度の講評",
  "ratings": {
    "情景": 4,
    "余韻": 5,
    "独創性": 4
  },
  "overall": 4
}
```

- `comment` は作品中の具体的な語句に触れる日本語の 5 文程度の文章。
- `ratings` の 3 項目と `overall` は 1 から 5 の整数。
- アプリケーション内部では Python の型安全なモデルを使い、Discord へは `★` と `☆` へ変換して表示する。

## 4. OpenAI API シーケンス

1. 一次判定は Responses API の構造化出力（Pydantic モデル）で実行する。
2. `is_poem` と `type` から対象性を決定する。ローカルの詩形判定や閾値判定は追加しない。
3. 対象なら、二次生成を Responses API の構造化出力だけで実行する。
4. 画像はリポジトリの固定テンプレートから読み込み、Pillow で元の作品本文を合成する。画像生成 API は使用しない。

SDK は `AsyncOpenAI` を使い、モデルは `gpt-5.6-luna`、推論 effort は `max` にコード固定する。実装時点では Responses API の `responses.parse(..., text_format=..., reasoning={"effort": "max"})` を前提とする。

## 5. Discord 投稿契約

対象投稿への返信本文は、1 行目の `俳句を検出しました！` または `川柳を検出しました！`、続く総合評価、`情景`・`余韻`・`独創性` の星評価、最後のラベルなし講評本文で構成する。元作品本文は返信本文へ含めず、添付画像へだけ合成する。

画像は `senryu-{message_id}.png` の一時バイト列として添付し、元メッセージへの reply として投稿する。メンションは付けない。Discord の本文上限を超える場合は講評を失わず、必要な分割を行う。

## 6. 画像合成

- 固定テンプレートを RGBA へ変換し、正方形へフィットさせる。
- 元作品本文を行単位で保持し、幅に合わせて折り返す。文字列の省略や AI による正規化は行わない。
- 画像生成で作成したテンプレートは、生成り色の和紙、紙繊維、控えめな木製額縁、水墨画風の淡い背景、余白、抽象的な赤い落款を含む。
- 生成り色の紙面を損なわない濃色で本文を中央寄せし、可読性のために控えめな影または半透明の下地を使う。
- 日本語フォントは同梱の Yuji Syuku（SIL Open Font License 1.1）を優先し、句ごとの列を上から下、列を右から左へ描く。フォントパスは環境変数で変更しない。
- Pillow の合成結果は PNG バイト列として返す。ローカルディスクへ永続化しない。

## 7. 重複処理防止

インメモリの TTL キャッシュを使う。

- キーは Discord `message.id`。
- `check_and_mark` は未登録キーだけを登録して `true` を返し、登録済みなら `false` を返す。
- デフォルト TTL は 15 分、最大件数を設けて古いキーから削除する。
- キャッシュはプロセス再起動で消える。Railway の production サービスは原則 1 インスタンスとする。

## 8. 環境変数と実行

必須:

- `DISCORD_TOKEN`
- `OPENAI_API_KEY`

任意のアプリケーション設定は環境変数に置かず、`bot/config.py` と `bot/usage.py` にコード化する。

起動コマンドは `python -m bot.main`。Dockerfile は Python 3.12 系を使い、`discord.py`、`openai`、`Pillow`、`pydantic` をインストールする。GitHub Actions は `workflow_dispatch` の手動実行時に対象テストを実行してから、Project・Environment・任意の Service を明示した Railway CLI の `railway up --ci` を実行する。`RAILWAY_ENVIRONMENT_ID` は未設定時に `production`、`RAILWAY_SERVICE_ID` は Service が 1 つなら省略可能とする。

## 9. テスト境界

- 型モデル: enum、範囲、必須キー、星表示。
- 重複防止: TTL、最大件数、同時呼び出し時の一意性。
- 画像合成: 正方形 PNG、元本文の描画、フォント未発見時の明示的エラー。
- AI サービス: 一次判定が対象外なら二次呼び出しを行わない、対象なら二次を一度だけ呼ぶ。
- Discord ハンドラ: Bot 投稿・重複投稿の無視、対象外の無返信、対象作品の reply。
- usage ログ: 各 OpenAI 応答の token 内訳と推定 USD、未知モデルの金額不明継続、本文非記録。

## 10. 確定した実装判断

- OpenAI のモデルは API 識別子 `gpt-5.6-luna`、Responses API の `reasoning.effort` は `max` に固定する。一次判定・二次生成とも環境変数で上書きしない。
- 背景画像は固定テンプレートを使用し、画像生成 API は呼び出さない。
- 画像合成に失敗した場合は全体を返信せず、ログだけを残す。
- 空本文・画像だけの投稿は AI に送らず無視する。
