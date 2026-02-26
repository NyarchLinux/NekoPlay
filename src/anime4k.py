# anime4k.py
#
# Copyright 2026 Francesco Caracciolo
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.
#
# SPDX-License-Identifier: GPL-3.0-or-later

import os


# Shader chains for Anime4K v4.0.1 (low-end preset only)
SHADER_CHAINS: dict[str, list[str]] = {
    "a": [
        "Anime4K_Clamp_Highlights.glsl",
        "Anime4K_Restore_CNN_M.glsl",
        "Anime4K_Upscale_CNN_x2_M.glsl",
        "Anime4K_AutoDownscalePre_x2.glsl",
        "Anime4K_AutoDownscalePre_x4.glsl",
        "Anime4K_Upscale_CNN_x2_S.glsl",
    ],
    "b": [
        "Anime4K_Clamp_Highlights.glsl",
        "Anime4K_Restore_CNN_Soft_M.glsl",
        "Anime4K_Upscale_CNN_x2_M.glsl",
        "Anime4K_AutoDownscalePre_x2.glsl",
        "Anime4K_AutoDownscalePre_x4.glsl",
        "Anime4K_Upscale_CNN_x2_S.glsl",
    ],
    "c": [
        "Anime4K_Clamp_Highlights.glsl",
        "Anime4K_Upscale_Denoise_CNN_x2_M.glsl",
        "Anime4K_AutoDownscalePre_x2.glsl",
        "Anime4K_AutoDownscalePre_x4.glsl",
        "Anime4K_Upscale_CNN_x2_S.glsl",
    ],
}

# Map dropdown index to mode string
MODE_INDEX_MAP: list[str] = ["off", "a", "b", "c"]

# Map mode string to dropdown index
MODE_TO_INDEX: dict[str, int] = {m: i for i, m in enumerate(MODE_INDEX_MAP)}


def get_shaders_dir() -> str:
    """Return the path to the Anime4K shaders directory."""
    # Common install paths
    from .utils import CONFIG_DIR

    candidates = [
        "/app/share/cine/shaders",  # Flatpak
        "/usr/share/cine/shaders",  # System install
        os.path.join(CONFIG_DIR, "shaders"),  # User override/dev fallback
    ]

    for path in candidates:
        if os.path.isdir(path):
            return path

    return candidates[-1]


def apply_anime4k_shaders(player, mode: str) -> None:
    """Apply Anime4K shader chain to the mpv player.

    Args:
        player: mpv.MPV instance
        mode: "off", "a", "b", or "c"
    """
    if mode == "off" or mode not in ("a", "b", "c"):
        player.command("change-list", "glsl-shaders", "clr", "")
        return

    chain = SHADER_CHAINS.get(mode)
    if not chain:
        player.command("change-list", "glsl-shaders", "clr", "")
        return

    shaders_dir = get_shaders_dir()
    shader_paths = [os.path.join(shaders_dir, s) for s in chain]

    # Verify all shader files exist
    missing = [p for p in shader_paths if not os.path.isfile(p)]
    if missing:
        print(f"Anime4K: missing shader files: {missing}")
        player.command("change-list", "glsl-shaders", "clr", "")
        return

    player.command("change-list", "glsl-shaders", "clr", "")
    for shader_path in shader_paths:
        player.command("change-list", "glsl-shaders", "append", shader_path)


def get_current_mode(player) -> str:
    """Detect the currently active Anime4K mode from mpv's glsl-shaders.

    Returns: "off", "a", "b", or "c"
    """
    try:
        shaders = player["glsl-shaders"]
    except Exception:
        return "off"

    if not shaders:
        return "off"

    shader_str = str(shaders) if not isinstance(shaders, str) else shaders
    if not shader_str:
        return "off"

    # Check for signature shaders to determine mode
    if "Anime4K_Restore_CNN_Soft_" in shader_str:
        return "b"
    elif "Anime4K_Upscale_Denoise_CNN_" in shader_str:
        return "c"
    elif "Anime4K_Restore_CNN_" in shader_str:
        return "a"

    return "off"
