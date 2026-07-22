"""Build the ordered LPython kernel translation unit, including extensions."""
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
PARTS = ROOT / "kernel" / "parts"
EXTENSIONS = ROOT / "extension"
ORDER = (
    "00_platform.inc.py",
    "10_storage.inc.py",
    "20_state_menu.inc.py",
    "30_game_render.inc.py",
    "40_entry.inc.py",
)


def extension_symbol(path: Path) -> str:
    return "ext_" + re.sub(r"[^a-zA-Z0-9_]", "_", path.stem).lower()


def build_extension_registry(paths: list[Path]) -> str:
    lines = [f"extension_count_value: i32 = {len(paths)}", "", "def extension_count() -> i32:", "    return extension_count_value", ""]
    lines += ["def extension_name_length(identifier: i32) -> i32:"]
    if paths:
        for index, path in enumerate(paths):
            keyword = "if" if index == 0 else "elif"
            lines.append(f"    {keyword} identifier == {index}: return {len(path.name)}")
    lines += ["    return 0", "", "def extension_name_char(identifier: i32, position: i32) -> i32:"]
    if paths:
        for index, path in enumerate(paths):
            keyword = "if" if index == 0 else "elif"
            lines.append(f"    {keyword} identifier == {index}:")
            for position, character in enumerate(path.name.upper().encode("ascii", "replace")):
                lines.append(f"        if position == {position}: return {character}")
    lines += ["    return 0", "", "def extension_window_host_id() -> i32:"]
    window_id = next((index for index, path in enumerate(paths) if path.stem.lower() == "windowcursor"), -1)
    lines += [f"    return {window_id}", "", "def extension_draw(identifier: i32) -> None:"]
    if paths:
        for index, path in enumerate(paths):
            keyword = "if" if index == 0 else "elif"
            lines.append(f"    {keyword} identifier == {index}: {extension_symbol(path)}_draw()")
    else:
        lines.append("    pass")
    lines += ["", "def extension_enter(identifier: i32) -> None:"]
    if paths:
        for index, path in enumerate(paths):
            keyword = "if" if index == 0 else "elif"
            lines.append(f"    {keyword} identifier == {index}: {extension_symbol(path)}_enter()")
    else:
        lines.append("    pass")
    lines += ["", "def extension_update(identifier: i32) -> None:"]
    if paths:
        for index, path in enumerate(paths):
            keyword = "if" if index == 0 else "elif"
            lines.append(f"    {keyword} identifier == {index}: {extension_symbol(path)}_update()")
    else:
        lines.append("    pass")
    lines += ["", "def extension_exit(identifier: i32) -> None:"]
    if paths:
        for index, path in enumerate(paths):
            keyword = "if" if index == 0 else "elif"
            lines.append(f"    {keyword} identifier == {index}: {extension_symbol(path)}_exit()")
    else:
        lines.append("    pass")
    lines += ["", "def extension_key(identifier: i32, key: i32) -> i32:"]
    if paths:
        for index, path in enumerate(paths):
            keyword = "if" if index == 0 else "elif"
            lines.append(f"    {keyword} identifier == {index}: return {extension_symbol(path)}_key(key)")
    lines += ["    return 0", ""]
    transition = None
    for path in paths:
        symbol = extension_symbol(path)
        source = path.read_text(encoding="utf-8")
        if f"def {symbol}_transition_enabled(" in source and f"def {symbol}_transition_begin(" in source and f"def {symbol}_transition_step(" in source:
            transition = symbol
            break
    lines += ["def extension_transition_enabled() -> i32:"]
    lines.append(f"    return {transition}_transition_enabled()" if transition else "    return 0")
    lines += ["", "def extension_transition_begin() -> None:"]
    lines.append(f"    {transition}_transition_begin()" if transition else "    ui_set_render_target(0)")
    lines += ["", "def extension_transition_step() -> i32:"]
    lines.append(f"    return {transition}_transition_step()" if transition else "    return 320")
    lines += [""]
    return "\n".join(lines)


def main() -> None:
    if len(sys.argv) != 2:
        raise SystemExit("usage: gen_kernel_source.py OUTPUT")
    output = Path(sys.argv[1])
    chunks = ["# Generated from kernel/parts and extension; do not edit.\n"]
    for name in ORDER[:-1]:
        chunks += [f"\n# --- {name} ---\n", (PARTS / name).read_text(encoding="utf-8")]
    extensions = sorted((path for path in EXTENSIONS.iterdir() if path.is_file() and path.suffix.lower() == ".py"), key=lambda path: path.name.lower()) if EXTENSIONS.is_dir() else []
    for path in extensions:
        chunks += [f"\n# --- extension/{path.name} ---\n", path.read_text(encoding="utf-8")]
    chunks += ["\n# --- generated extension registry ---\n", build_extension_registry(extensions)]
    name = ORDER[-1]
    chunks += [f"\n# --- {name} ---\n", (PARTS / name).read_text(encoding="utf-8")]
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text("".join(chunks), encoding="utf-8", newline="\n")


if __name__ == "__main__":
    main()