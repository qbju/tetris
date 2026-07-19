"""TETRIS OS kernel build manifest.

Ordered source fragments live under kernel/parts. The build amalgamates them
into build/kernel.py so LPython sees the single global namespace required by
the freestanding kernel.
"""

KERNEL_PARTS = (
    "00_platform.inc.py",
    "10_storage.inc.py",
    "20_state_menu.inc.py",
    "30_game_render.inc.py",
    "40_entry.inc.py",
)