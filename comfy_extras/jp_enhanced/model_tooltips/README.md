# 導入モデルの説明とツールチップ

2026-10-10時点の導入済み39ファイルを整理しています。作者が確認できないものは未確認とし、原作者と変換・配布者を分けています。ファイル名・埋め込みメタデータ・配布資料による照合であり、ハッシュによる同一性確認や生成品質の実測ではありません。

## 使い方

ComfyUIを再起動し、ブラウザーを再読み込みしてください。モデル読み込みノードの選択済みファイル欄にカーソルを置くと、標準ツールチップに説明を表示します。選択を変えると説明も切り替わります。プルダウン一覧内の各候補への表示ではありません。標準設定のツールチップ表示を有効にしてください。

## 説明の編集

モデル説明は最大520px幅で表示し、画面の端に12pxの余白を確保します。長文は説明内でスクロールできます。カーソルを説明へ移しても表示を保持し、外へ移すかEscキーで閉じます。

`web/catalog/index.json` が読み込む説明ファイルの一覧です。カテゴリ／モデル系列別のJSONにまとめています。各JSONの `category` はComfyUIのモデルカテゴリ、`file` はそのカテゴリのフォルダからの相対パス（区切りは `/`）です。新しい説明ファイルを追加するときは一覧にも登録してください。説明の編集はブラウザー再読み込みで反映します。外部サイトへの通信や自動取得は行いません。

各項目: `name` 名称、`author` 原作者、`publisher` 変換・配布者、`baseModel` 対応系統、`description` 特徴、`notes` 注意点、`verification` 確認範囲、`sources` 出典URL。未登録ファイルは未登録と表示し、別フォルダの同名ファイルとは取り違えません。

## 導入一覧

以下は整理時点の一覧です。説明の正本はリンク先JSONです。

| 区分・説明ファイル | 名称 | 作者 | 特徴 |
|---|---|---|---|
| [checkpoints](web/catalog/checkpoints/sd15.json) | ChilloutMix Ni Pruned FP32 Fix | 未確認 | ChilloutMixの派生チェックポイント。人物写真向けとして流通する系統。 |
| [checkpoints](web/catalog/checkpoints/sd15.json) | CityEdgeMix v1.25 | 未確認 | CityEdgeMixのチェックポイント。人物向けの詳細な特徴・設定は一次資料未確認。 |
| [checkpoints](web/catalog/checkpoints/sd15.json) | MeinaHentai V5 Final | Meina（シリーズ作者） | 成人向けアニメ表現を中心とするMeinaシリーズ。 |
| [checkpoints](web/catalog/checkpoints/sd15.json) | Stable Diffusion v1.5 Pruned | Runway / CompVis / Stability AI | テキストから画像を生成する基礎チェックポイント。SD1.5用LoRAの接続先。 |
| [checkpoints](web/catalog/checkpoints/sdxl.json) | Animagine XL 4.0 Opt | Cagliostro Research Lab | アニメ向けの追加学習版。Optは追加データで調整された一般用途向けバリアント。 |
| [checkpoints](web/catalog/checkpoints/sdxl.json) | Hassaku XL (Illustrious) 3.4 | Ikena | 明るく特徴的なアニメ画風を目指したチェックポイント。 |
| [checkpoints](web/catalog/checkpoints/sdxl.json) | rinFLanime Illustrious v5.0 | 未確認 | 埋め込みマージ情報ではflaBase_v50とflanime_v50を使用した派生モデル。 |
| [checkpoints](web/catalog/checkpoints/sdxl.json) | WAI-illustrious-SDXL v17.0 | WAI0731（配布カードのクレジット） | アニメ系の派生チェックポイント。配布カードではVAE内蔵と案内。 |
| [checkpoints](web/catalog/checkpoints/sdxl.json) | rinHEros NSFW v3.0 | 未確認 | 埋め込みマージ情報ではIllustrious XL・WAI Illustrious・heros_v30を使用。 |
| [diffusion_models](web/catalog/diffusion_models/anima.json) | Anima Aesthetic v1.1 | 派生版作者は未確認。基礎モデル: CircleStone Labs / Comfy Org | Anima系の生成モデル。基礎モデルはアニメ向けの独立したアーキテクチャ。 |
| [diffusion_models](web/catalog/diffusion_models/flux2.json) | FLUX.2 klein Base 4B FP8 | Black Forest Labs | 画像生成・複数参照画像による編集に対応する4BモデルのFP8版。 |
| [diffusion_models](web/catalog/diffusion_models/krea2.json) | Krea 2 Turbo Q5_0 GGUF | Krea | 蒸留されたKrea 2 TurboのGGUF量子化版。Raw版とは別のチェックポイント。 |
| [diffusion_models](web/catalog/diffusion_models/minimax.json) | MiniMax H3 Ref2VA Pruned INT8 ConvRot | MiniMaxAI | 参照画像から映像・音声を生成するH3系モデル。pruned・INT8 ConvRotの省メモリ版。 |
| [diffusion_models](web/catalog/diffusion_models/qwen_image.json) | Qwen-Image 2.1 INT8 ConvRot | Alibaba / Qwen | テキスト生成・画像編集を統合したQwen-Image 2.1の量子化版。 |
| [diffusion_models](web/catalog/diffusion_models/qwen_image.json) | Qwen-Image 2.1 Turbo AD-Q5_K | Alibaba / Qwen | TurboモデルのAtomic Dynamic量子化版。テンソルごとに量子化精度を調整。 |
| [diffusion_models](web/catalog/diffusion_models/qwen_image.json) | Qwen-Image 2.1 UC Q4_K_M | 派生版作者は未確認。基礎モデル: Alibaba / Qwen | Qwen-Image 2.1系のQ4_K_M量子化ファイル。 |
| [diffusion_models](web/catalog/diffusion_models/qwen_image.json) | Qwen-Image 2.1 UC Q8_0 | 派生版作者は未確認。基礎モデル: Alibaba / Qwen | Qwen-Image 2.1系のQ8_0量子化ファイル。 |
| [loras](web/catalog/loras/minimax.json) | MiniMax H3 FL2V Turbo 4-step v1.2 768p | LightX2V（Turboシリーズ） | 開始・終了フレーム系FL2VA向けの4ステップ高速化LoRA。768p表記。 |
| [loras](web/catalog/loras/minimax.json) | MiniMax H3 FL2V Turbo 8-step v1.0 768p | LightX2V（Turboシリーズ） | 開始・終了フレーム系FL2VA向けの8ステップ高速化LoRA。768p表記。 |
| [loras](web/catalog/loras/minimax.json) | MiniMax H3 FL2V Turbo 8-step v1.0 | LightX2V（Turboシリーズ） | 開始・終了フレーム系FL2VA向けの8ステップ高速化LoRA。解像度の詳細は配布元を確認。 |
| [loras](web/catalog/loras/minimax.json) | MiniMax H3 Ref2V Turbo 8-step v1.0 768p | LightX2V（Turboシリーズ） | ファイル名はRef2V用の8ステップ高速化・768pを示す。 |
| [loras](web/catalog/loras/minimax.json) | MM-H3 Ref2VA Age Slider v2 Experimental | 未確認 | Age Sliderという名称の実験版LoRA。調整効果の方向・推奨強度は未確認。 |
| [loras](web/catalog/loras/qwen_image.json) | NSFW Qwen LoRA | 未確認 | 成人向け用途を示す名称の個人LoRA。具体的な学習内容・効果は未確認。 |
| [loras](web/catalog/loras/qwen_image.json) | Qwen-Image 2.1 Viggle Turbo v0.2.1 r128 | Viggle | 6ステップで生成・画像編集を高速化する蒸留LoRA。rank 128版。 |
| [loras](web/catalog/loras/sd15.json) | Webio-women | 未確認 | SD1.5ベースで学習されたLoRA。具体的な効果・作者は未確認。 |
| [vae](web/catalog/vae/flux2.json) | FLUX.2 VAE | Black Forest Labs | FLUX.2用の潜在表現と画像の変換器。 |
| [vae](web/catalog/vae/minimax.json) | MiniMax H3 Audio VAE FP32 | MiniMaxAI | H3の音声潜在をエンコード・デコードするVAE。ローカルメタデータは32kHz・2チャンネル。 |
| [vae](web/catalog/vae/minimax.json) | MiniMax H3 Video VAE INT8 ConvRot | MiniMaxAI | H3の映像潜在を扱う量子化VAE。 |
| [vae](web/catalog/vae/qwen_image.json) | Qwen-Image 2.1 VAE BF16 | Alibaba / Qwen | Qwen-Image 2.1用の画像・潜在変換器。メタデータのarchitectureも2.1専用を示す。 |
| [vae](web/catalog/vae/sdxl.json) | SDXL Anime Clear VAE | easygoing0114 | SDXLアニメ画像の明瞭さと赤系の色表現を調整したVAE。 |
| [text_encoders](web/catalog/text_encoders/qwen.json) | Qwen3 4B FP8 Mixed | Alibaba / Qwen | 生成モデルへプロンプトを渡すための4Bテキストエンコーダー。 |
| [text_encoders](web/catalog/text_encoders/qwen.json) | Qwen3-VL 32B MiniMax H3 NVFP4 AWQ | Alibaba / Qwen | H3用の大規模テキストエンコーダーの量子化版。 |
| [text_encoders](web/catalog/text_encoders/qwen.json) | Qwen3-VL 8B FP8 Scaled | Alibaba / Qwen | Qwen-Image 2.1の条件付けに用いる8BエンコーダーのFP8 Scaled版。 |
| [text_encoders](web/catalog/text_encoders/qwen.json) | Qwen3-VL 8B INT8 ConvRot | Alibaba / Qwen | Qwen-Image 2.1の条件付けに用いる8BエンコーダーのINT8 ConvRot版。 |
| [controlnet](web/catalog/auxiliary/controlnet.json) | 未特定のControlNet FP16 | 未確認 | 条件画像で生成を制御するモデル。add_embedding入力2816の構造を確認。 |
| [sam3](web/catalog/auxiliary/sam3.json) | SAM 3 | Meta | 画像・動画中の対象を切り分けるセグメンテーションモデル。 |
| [upscale_models](web/catalog/auxiliary/upscale.json) | IllustrationJaNai V1 DAT2 | the-database | 品質重視の4倍拡大。ESRGAN版より処理が重い。 |
| [upscale_models](web/catalog/auxiliary/upscale.json) | IllustrationJaNai V1 ESRGAN | the-database | 速度と品質のバランスを取った4倍拡大。 |
| [loras](web/catalog/loras/qwen_image.json) | Qwen-Image 2.1 Consistency LoRA（step 1500） | ausboss | 画像編集時の位置ずれと、指定していない背景・髪などの描き直しを抑えるLoRA。色・衣装・画風の変更など、構図を保ちたい編集向け。 |
