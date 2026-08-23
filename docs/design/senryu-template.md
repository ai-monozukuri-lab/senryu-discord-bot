---
title: 作品画像テンプレート生成仕様
description: 画像生成ツールで作成した俳句・川柳作品画像の背景テンプレートと、再生成時に守るプロンプト・不変条件。
updated: 2026-08-23
read_when:
  - "`assets/senryu_template.png` を更新するとき。"
  - 作品画像の和風デザイン、余白、色、背景表現を変更するとき。
---

# 作品画像テンプレート生成仕様

## 現在のアセット

- パス: `assets/senryu_template.png`
- 用途: Discord に添付する作品画像の背景。
- 生成サイズ: 1254×1254 の RGBA PNG。Bot は Pillow で 1024×1024 に整形して本文を合成する。
- 生成方式: Codex の組み込み画像生成ツールで生成し、生成画像をリポジトリへコピー。
- 日本語本文: 画像生成には含めず、`bot/image.py` が元の Discord 本文を正確に描画する。

## 再生成プロンプト

```text
Create a quiet, refined Japanese poetry display background designed like a poem mounted in a traditional frame. Use warm ivory handmade washi paper with delicate visible paper fibers, a generous clear negative-space center for overlaid Japanese text, and a very subtle atmospheric ink-wash landscape around the perimeter. Include a restrained dark walnut wooden frame, muted watercolor and sumi-e scenery, and one small abstract vermilion red seal near the lower right; the seal must contain no character. Use a square composition, soft diffuse daylight, calm literary mood, warm ivory/parchment, muted charcoal, sage, blue-gray, walnut brown, and a tiny vermilion accent. The center must remain uncluttered and readable.

No readable text, Japanese characters, kanji, kana, Latin letters, numbers, calligraphy, logos, watermark, signature, people, animals, bright saturated colors, hard geometric mountains, large dark blobs, excessive noise, clutter, or border text.
```

再生成後は、中央の文字安全領域、木製額縁、和紙の繊維、水墨画の淡い周辺表現、赤い抽象落款、文字・透かしがないことを目視確認する。生成した PNG を `assets/senryu_template.png` に置き換え、`python -m pytest tests/test_image.py` を実行する。
