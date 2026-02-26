# preferences.py
#
# Copyright 2025 Diego Povliuk
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

gi.require_version("Adw", "1")
gi.require_version("Gdk", "4.0")
gi.require_version("Gio", "2.0")
gi.require_version("Gtk", "4.0")
from gi.repository import Adw, Gdk, Gio, Gtk

from .anime4k import apply_anime4k_shaders, MODE_INDEX_MAP, MODE_TO_INDEX

settings = Gio.Settings.new("io.github.diegopvlk.Cine")


def sync_mpv_with_settings(window):
    """Apply settings values to the mpv instance"""
    player = window.mpv
    player["sub-color"] = settings.get_string("subtitle-color")
    player["sub-scale"] = settings.get_double("subtitle-scale")
    player["sub-font"] = settings.get_string("subtitle-font")
    player["slang"] = settings.get_string("subtitle-languages")
    player["alang"] = settings.get_string("audio-languages")
    player["save-position-on-quit"] = settings.get_boolean("save-video-position")
    player["volume"] = settings.get_int("volume")
    hwdec_enabled = settings.get_boolean("hwdec")
    norm_enabled = settings.get_boolean("normalize-volume")

    if hwdec_enabled:
        player.command_async("vf", "remove", "@hflip")
        player.command_async("vf", "remove", "@vflip")
        player["hwdec"] = window.conf_hwdec + ["auto"]
    else:
        player["hwdec"] = "no"

    if norm_enabled:
        player.command("af", "add", "@cine_loudnorm:lavfi=[loudnorm=I=-20]")

    # Apply Anime4K shaders if a default mode is set
    anime4k_mode = settings.get_string("anime4k-mode")
    if anime4k_mode != "off":
        apply_anime4k_shaders(player, anime4k_mode)


@Gtk.Template(resource_path="/io/github/diegopvlk/Cine/preferences.ui")
class Preferences(Adw.Dialog):
    __gtype_name__ = "Preferences"

    open_new_row: Adw.SwitchRow = Gtk.Template.Child()
    color_dialog_button: Gtk.ColorDialogButton = Gtk.Template.Child()
    sub_color_row: Adw.ActionRow = Gtk.Template.Child()
    reset_sub_color: Gtk.Button = Gtk.Template.Child()
    reset_sub_font: Gtk.Button = Gtk.Template.Child()
    font_row: Adw.ActionRow = Gtk.Template.Child()
    font_label: Gtk.Label = Gtk.Template.Child()
    subtitle_scale_row: Adw.SpinRow = Gtk.Template.Child()
    subtitle_lang_row: Adw.EntryRow = Gtk.Template.Child()
    audio_lang_row: Adw.EntryRow = Gtk.Template.Child()
    hwdec_row: Adw.SwitchRow = Gtk.Template.Child()
    normalize_volume_row: Adw.SwitchRow = Gtk.Template.Child()
    anime4k_mode_row: Adw.ComboRow = Gtk.Template.Child()
    save_position_switch: Gtk.Switch = Gtk.Template.Child()

    def __init__(self, active_window, **kwargs):
        super().__init__(**kwargs)
        self.win = active_window
        self.player = active_window.mpv

        self._bind_ui()
        self._setup_mpv_updates()

        font = settings.get_string("subtitle-font")
        self.font_label.set_label(font)

        # Initialize Anime4K combo rows from GSettings
        anime4k_mode = settings.get_string("anime4k-mode")
        mode_idx = MODE_TO_INDEX.get(anime4k_mode, 0)
        self.anime4k_mode_row.set_selected(mode_idx)

        self.anime4k_mode_row.connect("notify::selected", self._on_anime4k_mode_ui_changed)

        self.color_dialog_button.connect("notify::rgba", self._on_color_selected)
        self.reset_sub_color.connect("clicked", self._on_color_reset)
        self.font_row.connect("activated", self._on_font_activated)
        self.reset_sub_font.connect("clicked", self._on_font_reset)

        self.sub_color = Gdk.RGBA()
        self.sub_color.parse(settings.get_string("subtitle-color"))
        self.color_dialog_button.set_dialog(
            Gtk.ColorDialog(
                modal=True,
                with_alpha=False,
            )
        )
        self.color_dialog_button.set_rgba(self.sub_color)

        self.connect("closed", self._disconnect_settings)

    def _bind_ui(self):
        settings.bind(
            "open-new-windows",
            self.open_new_row,
            "active",
            Gio.SettingsBindFlags.DEFAULT,
        )
        settings.bind(
            "subtitle-scale",
            self.subtitle_scale_row,
            "value",
            Gio.SettingsBindFlags.DEFAULT,
        )
        settings.bind(
            "subtitle-languages",
            self.subtitle_lang_row,
            "text",
            Gio.SettingsBindFlags.DEFAULT,
        )
        settings.bind(
            "audio-languages",
            self.audio_lang_row,
            "text",
            Gio.SettingsBindFlags.DEFAULT,
        )
        settings.bind(
            "hwdec",
            self.hwdec_row,
            "active",
            Gio.SettingsBindFlags.DEFAULT,
        )
        settings.bind(
            "normalize-volume",
            self.normalize_volume_row,
            "active",
            Gio.SettingsBindFlags.DEFAULT,
        )
        settings.bind(
            "save-video-position",
            self.save_position_switch,
            "active",
            Gio.SettingsBindFlags.DEFAULT,
        )

    def _setup_mpv_updates(self):
        handlers = {
            "subtitle-color": self._on_sub_color_changed,
            "subtitle-scale": self._on_sub_scale_changed,
            "subtitle-font": self._on_sub_font_changed,
            "subtitle-languages": self._on_slang_changed,
            "audio-languages": self._on_alang_changed,
            "hwdec": self._on_hwdec_changed,
            "normalize-volume": self._on_norm_volume_changed,
            "save-video-position": self._on_save_pos_changed,
            "anime4k-mode": self._on_anime4k_mode_setting_changed,
        }

        self._setting_ids = [
            settings.connect(f"changed::{key}", callback)
            for key, callback in handlers.items()
        ]

    def _disconnect_settings(self, *a):
        for connection_id in self._setting_ids:
            settings.disconnect(connection_id)

    def _on_sub_color_changed(self, settings, _key):
        self.player["sub-color"] = settings.get_string("subtitle-color")

    def _on_sub_scale_changed(self, settings, _key):
        self.player["sub-scale"] = settings.get_double("subtitle-scale")

    def _on_sub_font_changed(self, settings, _key):
        self.player["sub-font"] = settings.get_string("subtitle-font")

    def _on_slang_changed(self, settings, _key):
        self.player["slang"] = settings.get_string("subtitle-languages")

    def _on_alang_changed(self, settings, _key):
        self.player["alang"] = settings.get_string("audio-languages")

    def _on_save_pos_changed(self, settings, _key):
        self.player["save-position-on-quit"] = settings.get_boolean(
            "save-video-position"
        )

    def _on_hwdec_changed(self, settings, _key):
        hwdec_enabled = settings.get_boolean("hwdec")
        if hwdec_enabled:
            self.player.command_async("vf", "remove", "@hflip")
            self.player.command_async("vf", "remove", "@vflip")
            self.player["hwdec"] = self.win.conf_hwdec + ["auto"]
        else:
            self.player["hwdec"] = "no"

    def _on_norm_volume_changed(self, settings, _key):
        norm_enabled = settings.get_boolean("normalize-volume")
        if norm_enabled:
            self.player.command("af", "add", "@cine_loudnorm:lavfi=[loudnorm=I=-20]")
        else:
            self.player.command("af", "remove", "@cine_loudnorm")

    def _on_anime4k_mode_ui_changed(self, row, *a):
        idx = row.get_selected()
        mode = MODE_INDEX_MAP[idx] if idx < len(MODE_INDEX_MAP) else "off"
        settings.set_string("anime4k-mode", mode)

    def _on_anime4k_mode_setting_changed(self, settings, _key):
        mode = settings.get_string("anime4k-mode")
        apply_anime4k_shaders(self.player, mode)

    def _on_color_selected(self, color_btn, *arg):
        rgba = color_btn.get_rgba()
        hex_color = "#{:02x}{:02x}{:02x}".format(
            int(rgba.red * 255), int(rgba.green * 255), int(rgba.blue * 255)
        )
        settings.set_string("subtitle-color", hex_color)

    def _on_color_reset(self, _button):
        default_color = "#ebebeb"
        self.sub_color.parse(default_color)
        self.color_dialog_button.set_rgba(self.sub_color)

    def _on_font_activated(self, _row):
        dialog = Gtk.FontDialog()

        def callback(dialog, result):
            try:
                face = dialog.choose_face_finish(result)

                family_obj = face.get_family()
                family_name = family_obj.get_name()
                style_name = face.get_face_name()

                ignored_styles = [
                    "Regular",
                    "Normal",
                    "Roman",
                    "Book",
                    "Standard",
                    "Plain",
                    "Text",
                    "Semi",
                    "Semi-Bold",
                    "Demi",
                    "Demi-Bold",
                    "Upright",
                    "Alt",
                ]

                if any(s == style_name for s in ignored_styles):
                    font_full = family_name
                else:
                    # prevents "Font Bold Bold"
                    if style_name.lower() in family_name.lower():
                        font_full = family_name
                    else:
                        font_full = f"{family_name} {style_name}"

                font_full = " ".join(font_full.split())

                settings.set_string("subtitle-font", font_full)
                self.font_label.set_label(font_full)

            except Exception as e:
                print(f"Features selection error: {e}")

        dialog.choose_face(self.win, None, None, callback)

    def _on_font_reset(self, _button):
        default_font = "Adwaita Sans SemiBold"
        settings.set_string("subtitle-font", default_font)
        self.font_label.set_label(default_font)
