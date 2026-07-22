# TETRIS OS

LPythonでゲームロジックを書き、CPython + llvmliteでi386向けのハードウェア境界と描画プリミティブを生成する、起動可能な32-bit自作OSです。

GRUB Multiboot2からベアメタルで起動します。Pythonインタプリタや既存OSの上でゲームを動かしているわけではありません。LPythonがPythonコードをCへ変換し、Clang/LLDでカーネルへコンパイル・リンクします。

<p align="center">
  <img src="play.gif" alt="TETRIS OS gameplay" width="640">
</p>

## 特徴

- VGA Mode 13h（320×200、256色）によるピクセル描画
- 10×20の可視盤面と4行の非表示スポーン領域
- 7種類のテトリミノ、回転、ソフトドロップ、HOLD、NEXT、Ghost piece表示
- Fisher–Yatesシャッフルを使った7-bag方式
- bag境界で同じミノが連続しない補正
- ENDLESS、MARATHON 150、SPRINT 40の3ゲームモード
- ライン消去時の約200msフラッシュ演出
- 基本四隅判定によるT-spin検出とスコアボーナス
- PITを使った実時間ベースの落下・ロックディレイ・入力クールダウン
- スコア、コンボ、最長コンボ、ハイスコア
- PCスピーカーによる非同期SEと「コロブチカ」BGM
- SE再生中はSEを優先し、終了後にBGMを再開
- 複数のカラーテーマ
- 矢印キー操作とWASD操作の切り替え
- 落下速度、BGM音量、SE音量、デバッグ表示、Ghostの設定
- FPS、キーコード、盤面状態などのデバッグ表示
- 起動画面、ホームメニュー、一時停止、ゲームオーバー演出
- 統計、実績、実績解除通知、実績詳細モーダル
- ATA PIOドライバと独自TinyFSによる永続化

## 技術構成

```text
boot/boot.S
  Multiboot2ヘッダ、スタック初期化、kernel_main呼び出しだけの最小ASM

kernel/main.py
  分割カーネルを説明するソースマニフェスト

kernel/parts/
  00_platform.inc.py     I/O宣言、PIT、RTC、PCスピーカー、BGM/SE
  10_storage.inc.py      ATA PIO、TinyFS、永続レコード
  20_state_menu.inc.py   状態、ホーム、設定、統計、実績UI
  30_game_render.inc.py  Tetrisロジック、7-bag、ゲーム描画
  40_entry.inc.py        kernel_main、入力、状態遷移

tools/gen_kernel_source.py
  kernel/partsをbuild/kernel.pyへ結合

tools/gen_hw_object.py
  CPython + llvmliteでi386 ELFオブジェクトを生成
  VGA、フォント描画、in/out、盤面・bag・I/Oバッファを担当

storage/pythonos-data.img
  QEMUへ接続する4 MiBの永続データディスク
```

ブート処理以外に手書きASMソースはありません。`in` / `out`命令を含むハードウェアアクセスは、llvmliteのLLVMインラインASMから生成されます。

## ビルドの流れ

```text
kernel/parts/*.inc.py
        │ 結合
        ▼
build/kernel.py
        │ LPython --show-c
        ▼
build/kernel.c
        │ Clang -target i386-elf
        ▼
build/kernel.o ─────────────┐
                            │
tools/gen_hw_object.py      │
        │ CPython+llvmlite  │
        ▼                   │
build/hw.o ─────────────────┤
                            ├─ LLD → kernel.elf → GRUB → pythonos.iso
boot/boot.S → build/boot.o ─┘
```

`build/kernel.c`は中間生成物です。編集対象は`kernel/parts/*.inc.py`です。

## 必要なもの

- Docker Desktop
- Docker Compose
- QEMUまたはVNCクライアント

LPython、llvmlite、Clang、LLD、GRUB、xorriso、QEMUなどのビルド環境はDockerイメージに含まれます。

## ビルド

```powershell
docker compose build
docker compose run --rm osdev make
```

生成物：

```text
build/pythonos.iso
build/kernel.elf
storage/pythonos-data.img
```

`storage/pythonos-data.img`が既に存在する場合、通常の再ビルドでは上書きされません。

## 実行

### Docker + VNC

```powershell
docker rm -f pythonos-vnc
docker compose run -d --service-ports --name pythonos-vnc osdev sh -c "qemu-system-i386 -boot d -cdrom build/pythonos.iso -drive file=storage/pythonos-data.img,format=raw,if=ide,index=0 -display none -vnc 0.0.0.0:0 -no-reboot -no-shutdown"
```

VNCクライアントから`127.0.0.1:5900`へ接続してください。VNC接続ではPCスピーカー音声は転送されません。

停止：

```powershell
docker rm -f pythonos-vnc
```

### Windows版QEMU（音声あり）

```powershell
qemu-system-i386 -boot d -cdrom build/pythonos.iso `
  -drive file=storage/pythonos-data.img,format=raw,if=ide,index=0 `
  -audiodev dsound,id=snd0 -machine pcspk-audiodev=snd0 `
  -no-reboot -no-shutdown
```

## 操作

| キー | ホーム・設定 | ゲーム |
|---|---|---|
| `↑` / `↓` | 項目選択 | 回転 / ソフトドロップ |
| `←` / `→` | 値変更、ページ移動 | 左右移動 |
| `Enter` | 決定、次項目、モーダルを開く | ゲームオーバー後にホームへ戻る |
| `C` | — | HOLD |
| `Esc` | 戻る | 一時停止してホームへ戻る |
| `Shift` | 許可時にデバッグ表示を切り替え | 許可時にデバッグ表示を切り替え |

CONTROLを`WASD`へ変更すると、ゲーム中は`W`で回転、`A` / `D`で左右移動、`S`でソフトドロップします。

## ゲームモード

ホームのPLAYへカーソルを合わせ、左右キーでモードを選択します。

- `ENDLESS` — 従来の終了条件なしの通常ゲーム
- `MARATHON` — 150ライン消去で完走
- `SPRINT 40` — 40ライン消去までのタイムアタック

MARATHONとSPRINTでは、ゲーム画面に進行ライン数と経過時間を表示します。目標達成時は通常のGAME OVERとは異なる`MODE COMPLETE`画面を表示します。

Ghost pieceは現在のミノが着地する位置を薄いブロックで表示します。設定からON/OFFを切り替えられます。
## メニュー

ホームにはPLAY、SETTINGS、RESET DATA、STATISTICS、ACHIEVEMENTSがあります。ホーム項目は3件ずつ表示され、上下移動に合わせてスクロールします。RESET DATAでは確認ダイアログを表示します。

## 設定

設定は3ページ構成です。

- Page 1: COLOR、GRAVITY、CONTROL
- Page 2: BGM VOL、SE VOL、DEBUG
- Page 3: MUSIC、追加表示、GHOST

左右キーで値を変更します。Enterで次の行へ進み、`NEXT PAGE`または`SAVE BACK`でEnterを押すとページ移動・保存を実行します。設定はTinyFSへ保存されます。

## 実績

通常実績：

- FIRST BLOCK — 初めてミノを置く
- LINE ONE — 初めて1ライン消す
- FOUR WIDE — 4ラインを同時に消す
- GETTING STARTED — 累計100個のミノを置く
- FIVE DIGITS — 10000点に到達する
- CENTURY — 累計100ライン消す
- MARATHON — 累計1時間プレイする
- COMBO STARTER — 3コンボを達成する
- CHAIN REACTION — 8コンボを達成する

モード・チャレンジ実績：

- FIRST ENDLESS — ENDLESSを初めて開始する
- FIRST MARATHON — MARATHONを初めて開始する
- FIRST SPRINT — SPRINT 40を初めて開始する
- NOHOLD MARATHON — HOLDを使わずMARATHONを完走する
- NOHOLD SPRINT — HOLDを使わずSPRINTを完走する
- PERFECT STACK — ライン消去後に盤面を完全に空にする
- GHOSTLESS — GHOSTをOFFにして1000点を超える
- SURVIVOR — 300ms以下の落下速度で5分間生存する
- T-SPINER — T-spinを1回達成する
- T-SPIN MASTER — 1ゲーム中にT-spinを5回達成する
実績一覧では上下キーで選択、左右キーでページを移動します。実績にカーソルを合わせてEnterを押すと、解除状態と達成条件をモーダル表示します。

解除通知はゲーム画面右下へ表示され、約3秒後に消えます。

## TinyFS

プライマリマスターIDEディスクを、Pythonで実装したATA PIOドライバから読み書きします。保存対象は次のとおりです。

- ハイスコア
- 最長コンボ
- プレイ時間、消去ライン数、配置ミノ数
- カラーテーマ、落下速度、操作方式
- BGM/SE音量、デバッグ、GHOST設定
- 実績解除状態

重要なレコードは世代番号とチェックサムを持つ2スロットへ交互に保存し、書き込み途中の中断に耐える構造です。RESET DATAですべて初期化できます。

## 現在の制約

- 32-bit x86とVGA Mode 13h専用
- PS/2キーボードはポーリング方式
- ATAはPIO方式
- PCスピーカーは単音のみ
- VNCでは音声を利用できない
- TinyFSはこのOSの固定用途に特化した最小構成

## ライセンス

[MIT License](LICENSE)