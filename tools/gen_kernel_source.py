"""Build the ordered LPython kernel translation unit, including extensions."""
from pathlib import Path
import re
import sys
import zlib

ROOT = Path(__file__).resolve().parents[1]
PARTS = ROOT / "kernel" / "parts"
EXTENSIONS = ROOT / "extension"
KEYBOARDS = ROOT / "kernel" / "keyboard"
CRYPT = ROOT / "kernel" / "crypt"
IMAGE = ROOT / "kernel" / "image"
ORDER = (
    "00_platform.inc.py",
    "10_storage.inc.py",
    "20_state_menu.inc.py",
    "30_game_render.inc.py",
    "40_entry.inc.py",
)


def extension_symbol(path: Path) -> str:
    return "ext_" + re.sub(r"[^a-zA-Z0-9_]", "_", path.stem).lower()


def extension_permissions(path: Path) -> int:
    source = path.read_text(encoding="utf-8")
    match = re.search(r"(?im)^\s*#\s*permissions\s*:\s*(.+)$", source)
    if not match:
        return 0
    names = {name.strip().lower() for name in re.split(r"[,\s]+", match.group(1)) if name.strip()}
    bits = {"settings.read": 1, "settings.write": 2, "settings.save": 4, "autostart": 8, "background": 16, "events": 32, "notify": 64, "messages": 128, "storage.read": 256, "storage.write": 512, "framebuffer.native": 1024, "settings.admin": 2048, "crypto.hash": 4096, "crypto.encoding": 8192, "crypto.random": 16384, "crypto.symmetric": 32768, "crypto.pqc": 65536, "crypto.legacy": 131072, "image.process": 262144}
    return sum(value for name, value in bits.items() if name in names)


def build_extension_registry(paths: list[Path]) -> str:
    lines = [f"extension_count_value: i32 = {len(paths)}", "", "def extension_count() -> i32:", "    return extension_count_value", ""]
    lines += ["def extension_name_length(identifier: i32) -> i32:"]
    for index, path in enumerate(paths):
        keyword = "if" if index == 0 else "elif"
        lines.append(f"    {keyword} identifier == {index}: return {len(path.name)}")
    lines += ["    return 0", "", "def extension_name_char(identifier: i32, position: i32) -> i32:"]
    for index, path in enumerate(paths):
        keyword = "if" if index == 0 else "elif"
        lines.append(f"    {keyword} identifier == {index}:")
        for position, character in enumerate(path.name.upper().encode("ascii", "replace")):
            lines.append(f"        if position == {position}: return {character}")
    lines += ["    return 0", "", "def extension_permission_mask(identifier: i32) -> i32:"]
    for index, path in enumerate(paths):
        keyword = "if" if index == 0 else "elif"
        lines.append(f"    {keyword} identifier == {index}: return {extension_permissions(path)}")
    lines += ["    return 0", "", "def extension_storage_key(identifier: i32) -> i32:"]
    for index, path in enumerate(paths):
        keyword = "if" if index == 0 else "elif"
        stable_key = zlib.crc32(path.name.upper().encode("ascii", "replace")) & 0x7FFFFFFF
        lines.append(f"    {keyword} identifier == {index}: return {stable_key}")
    lines += ["    return -1", "", "def extension_autostart_match(length: i32) -> i32:"]
    for index, path in enumerate(paths):
        name = path.name.upper().encode("ascii", "replace")
        lines.append(f"    if length == {len(name)}:")
        condition = " and ".join(f"fs_buffer_get({8 + pos}) == {char}" for pos, char in enumerate(name)) or "True"
        lines.append(f"        if {condition}: return {index}")
    lines += ["    return -1", "", "def extension_find_memory(length: i32, offset: i32) -> i32:"]
    for index, path in enumerate(paths):
        name = path.name.upper().encode("ascii", "replace")
        lines.append(f"    if length == {len(name)}:")
        condition = " and ".join(f"(extension_memory_get(offset + {pos}) == {char} or extension_memory_get(offset + {pos}) == {char + 32 if 65 <= char <= 90 else char})" for pos, char in enumerate(name)) or "True"
        lines.append(f"        if {condition}: return {index}")
    lines += ["    return -1", "", "def extension_window_host_id() -> i32:"]
    window_id = next((index for index, path in enumerate(paths) if path.stem.lower() == "windowcursor"), -1)
    lines += [f"    return {window_id}", ""]
    lines += ["def extension_background_capable(identifier: i32) -> i32:"]
    background_paths = [(index, path) for index, path in enumerate(paths) if (extension_permissions(path) & 16) != 0 and f"def {extension_symbol(path)}_background(" in path.read_text(encoding="utf-8")]
    for position, (index, path) in enumerate(background_paths):
        keyword = "if" if position == 0 else "elif"
        lines.append(f"    {keyword} identifier == {index}: return 1")
    lines += ["    return 0", "", "def extension_background_start(identifier: i32) -> i32:", "    global extension_background_mask", "    if extension_background_capable(identifier) == 0: return -1", "    extension_background_mask = extension_background_mask | (1 << identifier)", "    return 0", ""]

    def dispatch_void(public: str, suffix: str) -> None:
        lines.extend([f"def {public}(identifier: i32) -> None:", "    global extension_current_id, extension_current_permissions", "    previous_id: i32 = extension_current_id", "    previous_permissions: i32 = extension_current_permissions", "    extension_current_id = identifier", "    extension_current_permissions = extension_permission_mask(identifier)"])
        for index, path in enumerate(paths):
            keyword = "if" if index == 0 else "elif"
            lines.append(f"    {keyword} identifier == {index}: {extension_symbol(path)}_{suffix}()")
        if suffix == "enter":
            lines.append("    extension_emit_event(2, identifier)")
        elif suffix == "exit":
            lines.append("    extension_emit_event(3, identifier)")
        lines.extend(["    extension_current_id = previous_id", "    extension_current_permissions = previous_permissions", ""])

    dispatch_void("extension_draw", "draw")
    dispatch_void("extension_enter", "enter")
    dispatch_void("extension_update", "update")
    dispatch_void("extension_exit", "exit")
    lines += ["def extension_native_overlay(identifier: i32) -> None:", "    global extension_current_id, extension_current_permissions", "    previous_id: i32 = extension_current_id", "    previous_permissions: i32 = extension_current_permissions", "    extension_current_id = identifier", "    extension_current_permissions = extension_permission_mask(identifier)"]
    for index, path in enumerate(paths):
        symbol = extension_symbol(path)
        source = path.read_text(encoding="utf-8")
        if f"def {symbol}_native_overlay(" in source:
            lines.append(f"    if identifier == {index}: {symbol}_native_overlay()")
    lines += ["    extension_current_id = previous_id", "    extension_current_permissions = previous_permissions", ""]
    lines += ["def extension_key(identifier: i32, key: i32) -> i32:", "    global extension_current_id, extension_current_permissions", "    previous_id: i32 = extension_current_id", "    previous_permissions: i32 = extension_current_permissions", "    extension_current_id = identifier", "    extension_current_permissions = extension_permission_mask(identifier)", "    result: i32 = 0"]
    for index, path in enumerate(paths):
        keyword = "if" if index == 0 else "elif"
        lines.append(f"    {keyword} identifier == {index}: result = {extension_symbol(path)}_key(key)")
    lines += ["    extension_current_id = previous_id", "    extension_current_permissions = previous_permissions", "    return result", ""]

    # Optional background callback. Only extensions that declare `background`
    # and enable themselves through extension_background_set() are scheduled.
    lines += ["def extension_background_update_all() -> None:", "    global extension_current_id, extension_current_permissions", "    previous_id: i32 = extension_current_id", "    previous_permissions: i32 = extension_current_permissions"]
    for index, path in enumerate(paths):
        symbol = extension_symbol(path)
        source = path.read_text(encoding="utf-8")
        if f"def {symbol}_background(" in source:
            lines += [f"    if (extension_background_mask & (1 << {index})) != 0:", f"        extension_current_id = {index}", f"        extension_current_permissions = extension_permission_mask({index})", f"        {symbol}_background()"]
    lines += ["    extension_current_id = previous_id", "    extension_current_permissions = previous_permissions", ""]

    # Event callbacks are synchronous and are delivered in registry order.
    lines += ["def extension_emit_event(event: i32, value: i32) -> None:", "    global extension_current_id, extension_current_permissions", "    previous_id: i32 = extension_current_id", "    previous_permissions: i32 = extension_current_permissions"]
    for index, path in enumerate(paths):
        symbol = extension_symbol(path)
        source = path.read_text(encoding="utf-8")
        if f"def {symbol}_event(" in source:
            lines += [f"    if (extension_permission_mask({index}) & 32) != 0:", f"        extension_current_id = {index}", f"        extension_current_permissions = extension_permission_mask({index})", f"        {symbol}_event(event, value)"]
    lines += ["    extension_current_id = previous_id", "    extension_current_permissions = previous_permissions", ""]

    # Direct extension-to-extension request/reply messaging.
    lines += ["def extension_send_message(target: i32, topic: i32, value: i32) -> i32:", "    global extension_current_id, extension_current_permissions", "    if extension_current_id < 0 or (extension_current_permissions & 128) == 0: return -1", "    if target < 0 or target >= extension_count_value: return -2", "    sender: i32 = extension_current_id", "    sender_permissions: i32 = extension_current_permissions", "    result: i32 = -3", "    extension_current_id = target", "    extension_current_permissions = extension_permission_mask(target)"]
    for index, path in enumerate(paths):
        symbol = extension_symbol(path)
        source = path.read_text(encoding="utf-8")
        if f"def {symbol}_message(" in source:
            lines.append(f"    if target == {index}: result = {symbol}_message(sender, topic, value)")
    lines += ["    extension_current_id = sender", "    extension_current_permissions = sender_permissions", "    return result", ""]
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
def build_keyboard_layouts() -> str:
    paths = sorted(KEYBOARDS.glob("*.keyboard"), key=lambda path: path.name.lower())
    if not paths:
        raise SystemExit("kernel/keyboard must contain at least one .keyboard file")
    layouts = []
    for path in paths:
        name = path.stem.upper()
        mapping = {}
        for number, raw in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            line = raw.strip()
            if not line or line.startswith("#"):
                continue
            if "=" not in line:
                raise SystemExit(f"{path}:{number}: expected key=value")
            key, value = (part.strip() for part in line.split("=", 1))
            if key.lower() == "name":
                name = value.upper()
                continue
            try:
                scan = int(key, 16)
                normal_text, shifted_text = (part.strip() for part in value.split(",", 1))
                normal, shifted = int(normal_text), int(shifted_text)
            except ValueError as error:
                raise SystemExit(f"{path}:{number}: invalid scancode or ASCII pair") from error
            if not (0 <= scan <= 255 and 0 <= normal <= 255 and 0 <= shifted <= 255):
                raise SystemExit(f"{path}:{number}: values must be bytes")
            mapping[scan] = (normal, shifted)
        encoded = name.encode("ascii", "strict")
        if not 1 <= len(encoded) <= 12:
            raise SystemExit(f"{path}: name must be 1..12 ASCII characters")
        layouts.append((name, mapping))
    lines = [f"keyboard_layout_count_value: i32 = {len(layouts)}", "", "def keyboard_layout_count() -> i32:", "    return keyboard_layout_count_value", "", "def keyboard_layout_name_length(layout: i32) -> i32:"]
    for index, (name, _) in enumerate(layouts):
        lines.append(f"    {'if' if index == 0 else 'elif'} layout == {index}: return {len(name)}")
    lines += ["    return 0", "", "def keyboard_layout_name_char(layout: i32, position: i32) -> i32:"]
    for index, (name, _) in enumerate(layouts):
        lines.append(f"    {'if' if index == 0 else 'elif'} layout == {index}:")
        for position, character in enumerate(name.encode("ascii")):
            lines.append(f"        if position == {position}: return {character}")
    lines += ["    return 0", "", "def keyboard_layout_ascii(layout: i32, key: i32, shifted: i32) -> i32:"]
    for index, (_, mapping) in enumerate(layouts):
        lines.append(f"    {'if' if index == 0 else 'elif'} layout == {index}:")
        for scan, (normal, shift) in sorted(mapping.items()):
            lines.append(f"        if key == {scan}: return {shift} if shifted == 1 else {normal}")
    lines += ["    return 0", ""]
    return "\n".join(lines)

def main() -> None:
    if len(sys.argv) != 2:
        raise SystemExit("usage: gen_kernel_source.py OUTPUT")
    output = Path(sys.argv[1])
    chunks = ["# Generated from kernel/parts, keyboard layouts, and extension; do not edit.\n", "\n# --- generated keyboard layouts ---\n", build_keyboard_layouts()]
    for name in ORDER[:-1]:
        chunks += [f"\n# --- {name} ---\n", (PARTS / name).read_text(encoding="utf-8")]
        if name == "00_platform.inc.py" and CRYPT.is_dir():
            for path in sorted(CRYPT.glob("*.inc.py"), key=lambda item: item.name.lower()):
                chunks += [f"\n# --- crypt/{path.name} ---\n", path.read_text(encoding="utf-8")]
            for path in sorted(IMAGE.glob("*.inc.py"), key=lambda item: item.name.lower()):
                chunks += [f"\n# --- image/{path.name} ---\n", path.read_text(encoding="utf-8")]
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