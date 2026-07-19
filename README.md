# TETRIS OS

LPythonでゲームロジックを書き、CPython + llvmliteでi386向けハードウェア境界と描画コードを生成する、起動可能な32bit自作OSです。GRUB Multiboot2からベアメタルで起動し、Pythonインタプリタや既存OSを使わずにテトリスを実行します。

## 主な機能

- VGA Mode 13h（320×200、256色）のピクセルUI
- 10×20の可視盤面と4行の非表示スポーン領域
- 7種類のテトリミノ、回転、ライン消去、ロックディレイ
- 7-bag方式（バッグ境界で同じミノが連続しない拡張）
- 色付きのNEXT／HOLD表示
- HOLDは何度でも交換可能
- PITによる実時間ベースの落下・入力クールダウン
- PCスピーカーによる効果音とコロブチカのループ再生
- スコア、コンボ、歴代ハイスコア、最長コンボ
- スクロール式PLAY／SETTINGS／RESET DATA／STATISTICSメニュー
- 2ページ構成の設定画面
- 通常色、グレースケール、反転パレット
- 100ms単位の落下速度設定
- 矢印キー／WASD操作の切り替え
- BGM／SE音量（0〜10）
- Shiftデバッグ機能の有効・無効
- デバッグ欄の描画FPS表示
- ゲームオーバー演出、一時停止、デバッグ表示
- ATA PIOドライバと独自TinyFSによるデータ永続化

## 構成

```text
boot/boot.S
  Multiboot2ヘッダ、スタック初期化、kernel_main呼び出しだけの最小ASM

kernel/main.py
  分割カーネルのビルドマニフェスト

kernel/parts/
  00_platform.inc.py    I/O、PIT、PCスピーカー、音楽
  10_storage.inc.py     ATA PIO、TinyFS、永続レコード
  20_state_menu.inc.py  状態、ホーム、設定、統計UI
  30_game_render.inc.py 7-bag、盤面、ゲーム描画
  40_entry.inc.py       メインループ、入力、状態遷移

tools/gen_kernel_source.py
  上記断片をbuild/kernel.pyへ結合

tools/gen_hw_object.py
  CPython + llvmlite製ビルドツール
  Mode 13h描画、バッファ、in/out関数をELF32オブジェクトとして生成

storage/pythonos-data.img
  QEMU用4MiB永続ディスク
```

ブート以外の手書きASMやCソースはありません。LPythonが生成したCと、llvmliteが生成したLLVMオブジェクトをリンクします。

## 必要なもの

- Docker Desktop
- Docker Compose
- VNCクライアント（コンテナ版QEMUを使う場合）

LPython、llvmlite、Clang、LLD、GRUB、QEMUなどのビルド環境はDockerイメージに含まれます。

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

`storage/pythonos-data.img`は存在しない場合だけ作成されます。`make -B`や`make clean`でも保存データを上書きしません。

## QEMU + VNCで起動

```powershell
docker rm -f pythonos-vnc
docker compose run -d --service-ports --name pythonos-vnc osdev sh -c "qemu-system-i386 -boot d -cdrom build/pythonos.iso -drive file=storage/pythonos-data.img,format=raw,if=ide,index=0 -display none -vnc 0.0.0.0:0 -no-reboot -no-shutdown"
```

VNCクライアントから `127.0.0.1:5900` へ接続します。VNCは音声を転送しません。

停止：

```powershell
docker rm -f pythonos-vnc
```

## Windowsで音声付き起動

Windows版QEMUではDirectSoundへPCスピーカーを接続できます。

```powershell
qemu-system-i386 -boot d -cdrom build/pythonos.iso `
  -drive file=storage/pythonos-data.img,format=raw,if=ide,index=0 `
  -audiodev dsound,id=snd0 -machine pcspk-audiodev=snd0 `
  -no-reboot -no-shutdown
```

## 操作

| キー | 動作 |
|---|---|
| Enter | メニュー決定／ゲームオーバー画面からホームへ戻る |
| ↑ / ↓ | メニュー選択／ゲーム中は回転・ソフトドロップ |
| ← / → | 左右移動／設定値変更／確認ダイアログ選択 |
| C | HOLD |
| Esc | 一時停止してホームへ戻る |
| Shift | 設定で許可されている場合、デバッグ表示を切り替える |

## 統計画面

ホームのRESET DATAで↓を押すとメニューがスクロールし、PLAYの代わりにSTATISTICSが表示されます。STATISTICSからさらに↓を押すとPLAYへ戻ります。

STATISTICSでは、累計プレイ時間、累計消去ライン数、累計固定ミノ数を表示します。統計はTinyFSへ保存され、RESET DATAで初期化されます。
## 設定画面

設定は各ページ3項目とページ操作ボタンで構成されます。

- 1ページ目：COLOR、GRAVITY、CONTROL、NEXT PAGE
- 2ページ目：BGM VOL、SE VOL、DEBUG、SAVE BACK

左右キーで値を変更します。通常の設定項目でEnterを押すと次の行へ進み、NEXT PAGEまたはSAVE BACK上でEnterを押すとページ移動／保存を実行します。
## 7-bag

0〜6の7種類をFisher–Yates法でシャッフルし、すべて取り出してから次のバッグを生成します。さらに、新しいバッグの先頭が直前のバッグの末尾と同じ場合は、新バッグ内の別要素と交換します。

したがって各バッグに7種類が1個ずつ含まれる保証を維持しながら、`...7 | 7...` のような境界での同種連続を防ぎます。

## TinyFS

プライマリマスターIDEディスクをLPython製ATA PIOドライバで読み書きします。

保存対象：

- ハイスコア
- 最長コンボ
- カラーモード
- 落下速度
- 操作方式
- BGM音量
- SE音量
- デバッグ機能の有効・無効

ハイスコア、設定、最長コンボはそれぞれ世代番号とチェックサムを持つ二重スロットへ書き込み、書き込み途中の中断に耐える設計です。RESET DATAではこれらをすべて初期化します。

## ビルドの流れ

```text
kernel/parts/*.inc.py ── 結合 ──> build/kernel.py ── LPython ──> build/kernel.c ── Clang ──> build/kernel.o
tools/gen_hw_object.py ── CPython + llvmlite ──────────> build/hw.o
boot/boot.S ── Clang ───────────────────────────────────> build/boot.o

boot.o + kernel.o + hw.o ── LLD ──> kernel.elf ── GRUB ──> pythonos.iso
```

## 現在の制約

- VGA Mode 13h専用
- PS/2キーボードはポーリング方式
- ATAはPIO方式
- PCスピーカーは1音のみで、VNCでは音声を聞けない
- TinyFSはこのOSに必要な固定用途へ絞った最小構成

## ライセンス

[MIT License](LICENSE)