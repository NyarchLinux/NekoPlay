# utils.py
#
# Copyright 2026 Diego Povliuk
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

import gi
import os
import ctypes
from gettext import gettext as _

gi.require_version("GLib", "2.0")
from gi.repository import GLib

xdg_pictures = GLib.get_user_special_dir(GLib.UserDirectory.DIRECTORY_PICTURES)
SCREENSHOT_DIR = os.path.join(xdg_pictures, "Cine Screenshots") if xdg_pictures else ""

base_config = GLib.get_user_config_dir()
CONFIG_DIR = os.path.join(base_config, "cine")
INPUT_CONF = os.path.join(CONFIG_DIR, "input.conf")
os.makedirs(CONFIG_DIR, exist_ok=True)


def get_gpu_vendor(display, libgl):
    try:
        context = display.get_default_seat().get_display().create_gl_context()
        context.realize()
        context.make_current()

        glGetString = libgl.glGetString
        glGetString.restype = ctypes.c_char_p
        glGetString.argtypes = [ctypes.c_uint]

        # GL_VENDOR is 0x1F00
        return glGetString(0x1F00).decode("utf-8").lower()
    except Exception as e:
        print(f"get_gpu_vendor error: {e}")
        return None


def format_time(seconds):
    if not seconds:
        return "0:00"

    seconds = int(seconds)
    d = seconds // 86400
    h = (seconds % 86400) // 3600
    m = (seconds % 3600) // 60
    s = seconds % 60

    if d > 0:
        return f"{d}:{h:02d}:{m:02d}:{s:02d}"
    elif h > 0:
        return f"{h}:{m:02d}:{s:02d}"
    else:
        return f"{m}:{s:02d}"


MBTN_MAP: dict = {
    1: "MBTN_LEFT",
    2: "MBTN_MID",
    3: "MBTN_RIGHT",
    8: "MBTN_BACK",
    9: "MBTN_FORWARD",
}


KEY_REMAP: dict = {
    "plus": "+",
    "minus": "-",
    "equal": "=",
    "period": ".",
    "comma": ",",
    "bracketleft": "[",
    "bracketright": "]",
    "slash": "/",
    "backslash": "\\",
    "grave": "`",
    "apostrophe": "'",
    "semicolon": ";",
    "Escape": "ESC",
    "BackSpace": "BS",
    "Page_Up": "PGUP",
    "Page_Down": "PGDWN",
    "Left": "LEFT",
    "Right": "RIGHT",
    "Up": "UP",
    "Down": "DOWN",
}


SUB_EXTS: tuple = (
    ".ass",
    ".idx",
    ".lrc",
    ".mks",
    ".pgs",
    ".rt",
    ".sbv",
    ".scc",
    ".smi",
    ".srt",
    ".ssa",
    ".sub",
    ".sup",
    ".utf",
    ".utf-8",
    ".utf8",
)
