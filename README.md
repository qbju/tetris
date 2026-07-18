# TETRIS OS

LPythonでゲームロジックを書き、CPython + llvmliteでi386向けハードウェア境界を生成する、起動可能な32bit自作OSです。GRUB Multiboot2からベアメタルで起動し、QEMU上でテトリスを遊べます。

PythonインタプリタをOS上で動かしているわけではありません。LPythonのコードをネイティブコードへ変換し、仮想マシンやホストOSなしで実行しています。

## 特徴

- 10×20のテトリス盤面と4行の非表示スポーン領域
- 7種類のテトリミノ、回転、ライン消去、スコア
- NEXT／HOLD表示と色付きミノ
- PITによる500msの自然落下、200msのロックディレイ
- PS/2キーボード入力
- 一時停止、ゲームオーバー演出、再スタート
- テトリミノ風`TETRIS OS`起動画面
- VGAテキストモードのカラーUI
- ATA PIOディスクドライバ
- 独自TinyFSと永続ハイスコア
- Shiftで切り替え可能なデバッグ表示

## 構成

```text
boot/boot.S
  Multiboot2ヘッダ、スタック初期化、main呼び出し

kernel/main.py
  LPython製カーネル
  ゲーム、描画制御、PS/2、PIT、ATA PIO、TinyFS

tools/gen_hw_object.py
  CPython + llvmlite製ビルドツール
  VGAプリミティブ、作業バッファ、inb/outb/inw/outwをELF32へ生成

storage/pythonos-data.img
  QEMU用の4MiB永続ディスク（自動生成、Git管理外）
```

手書きアセンブリは起動に必要な[boot/boot.S](boot/boot.S)だけです。`in`／`out`命令を含むハードウェア関数は、llvmliteのインラインASMから生成されます。Cソースは手書きせず、LPythonがビルド時に中間生成するものだけを使用します。

## 必要なもの

- Docker Desktop
- Docker Compose
- VNCクライアント

LPython、llvmlite、Clang、LLD、GRUB、QEMUなどはDockerイメージ内に導入されます。

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

`storage/pythonos-data.img`は最初のビルド時だけ作られ、`make clean`では削除されません。

## QEMUをVNCで起動

```powershell
docker rm -f pythonos-vnc
docker compose run -d --service-ports --name pythonos-vnc osdev sh -c "qemu-system-i386 -boot d -cdrom build/pythonos.iso -drive file=storage/pythonos-data.img,format=raw,if=ide,index=0 -display none -vnc 0.0.0.0:0 -no-reboot -no-shutdown"
```

VNCクライアントから次へ接続します。

```text
127.0.0.1:5900
```

停止：

```powershell
docker rm -f pythonos-vnc
```

## 操作

| キー | 動作 |
|---|---|
| Enter | PLAY／ゲームオーバー画面からホームへ |
| ← / → | 左右移動 |
| ↓ | ソフトドロップ |
| ↑ | 回転 |
| C | HOLD |
| Esc | 一時停止してホームへ |
| Shift | デバッグ表示のオン／オフ |

## TinyFS

QEMUへ接続したprimary-master IDEディスクを、LPython製ATA PIOドライバで読み書きします。未初期化ディスクは起動時にOS自身がTinyFSとしてフォーマットします。

現在のTinyFSには以下があります。

- `PYFS`スーパーブロック
- ルートディレクトリ
- `HIGHSCORE`ファイル
- チェックサム付きレコード
- 書き込み中断に備えた二重スロット

ゲームオーバー時にハイスコアを保存し、次回起動時に読み戻します。

保存ディスクを初期化する場合は、QEMUを停止してから`storage/pythonos-data.img`を削除し、再度`make`を実行してください。保存済みハイスコアは失われます。

## ビルドの流れ

```text
kernel/main.py
   │ LPython --show-c
   ▼
build/kernel.c
   │ clang -target i386-elf
   ▼
build/kernel.o

 tools/gen_hw_object.py
   │ CPython + llvmlite
   ▼
 build/hw.o

 boot/boot.S ── clang ── build/boot.o

 build/boot.o + build/kernel.o + build/hw.o
   │ ld.lld + linker.ld
   ▼
build/kernel.elf
   │ grub-mkrescue
   ▼
build/pythonos.iso
```

## 現在の制約

- VGAテキストモード専用
- PS/2キーボードはポーリング方式
- ATAはPIO方式
- TinyFSは現在ハイスコア保存に必要な最小構成
- テトリミノ生成は簡易的で、公式の7-bag方式ではありません

## ライセンス

このプロジェクトは[MIT License](LICENSE)で公開されています。
