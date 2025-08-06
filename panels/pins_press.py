import logging
import gi
import functools

gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, Pango
from ks_includes.widgets.autogrid import AutoGrid
from ks_includes.KlippyGtk import find_widget

from ks_includes.screen_panel import ScreenPanel
from ks_includes.KlippyGcodes import KlippyGcodes
from ks_includes.widgets.numeric_keypad import NumericKeypad


class Panel(ScreenPanel):
    def __init__(self, screen, title, **kwargs):
        title = title or _("pins_press")
        super().__init__(screen, title)

        self._screen = screen
        self.labels = {}
        self.settings = {"speed": 3000, "distance": 5}
        self.devices = self._printer.get_pwm_tools() + self._printer.get_output_pins()
        self.numpad_visible = False

        self.right_panel = Gtk.Grid()
        self.right_panel.set_row_spacing(5)
        self.right_panel.set_column_spacing(5)

        self.grid = Gtk.Grid()
        self.grid.attach(self.create_left_panel(), 0, 0, 1, 1)
        self.grid.attach(self.create_right_panel(), 1, 0, 1, 1)
        self.content.add(self.grid)

    def create_left_panel(self):
        press_menu = Gtk.Grid(row_spacing=10, column_spacing=10)
        row = 0
        for pin in self.devices:
            out_name = pin.split()[1]
            if not out_name.startswith("EPRESS"):
                continue

            val = self._printer.get_pin_value(pin)
            label = Gtk.Label(label=f"{out_name}: {val:.3f} MPa")
            label.set_halign(Gtk.Align.START)
            self.labels[out_name] = label

            button = self._gtk.Button("edit", out_name.replace("EPRESS", "PRESS"), "color1", scale=0.2)
            button.connect("clicked", self.show_keypad_for_pin, out_name, pin)

            press_menu.attach(label, 0, row, 1, 1)
            press_menu.attach(button, 1, row, 1, 1)
            row += 1

        # Speed / Distance 조절용 버튼도 같은 패널에 추가
        btn_speed = self._gtk.Button("edit", "Speed", "color11", scale=0.2)
        btn_distance = self._gtk.Button("edit", "Distance", "color11", scale=0.2)
        btn_speed.connect("clicked", self.show_keypad_for_pin, "speed", None)
        btn_distance.connect("clicked", self.show_keypad_for_pin, "distance", None)
        #press_menu.attach(btn_speed, 0, row, 1, 1)
        #press_menu.attach(btn_distance, 1, row, 1, 1)

        self.labels["press_menu"] = press_menu
        return press_menu

    def create_right_panel(self):
        # keypad placeholder 자리 미리 확보
        self.labels["keypad_placeholder"] = Gtk.Box()
        self.right_panel.attach(self.labels["keypad_placeholder"], 0, 0, 1, 1)
        return self.right_panel

    def show_keypad_for_pin(self, widget, *args):
        """
        args: 
        - 첫번째: 키 이름 ("speed", "distance") 또는 압력핀 이름
        - 두번째: 압력핀일 경우 full name
        """
        out_name = args[0]
        pin_name = args[1] if len(args) > 1 else None
        is_pin = pin_name is not None and pin_name.startswith("output")

        def on_value_entered(value):
            try:
                val = float(value)
                if is_pin:
                    self._screen._ws.klippy.gcode_script(f"SET_PIN PIN={out_name} VALUE={val}")
                else:
                    self.settings[out_name] = val
            except ValueError:
                self._screen.show_popup_message("Invalid value")
            self.hide_keypad()

        self.hide_keypad()

        keypad = NumericKeypad(self._screen, on_value_entered, self.hide_keypad)
        self.labels["keypad"] = keypad
        self.right_panel.attach(keypad, 0, 0, 1, 1)
        self.right_panel.show_all()
        self.numpad_visible = True

    def hide_keypad(self, widget=None):
        if self.numpad_visible and "keypad" in self.labels and self.labels["keypad"]:
            self.right_panel.remove(self.labels["keypad"])
            self.labels["keypad"] = None
            self.numpad_visible = False

    def process_update(self, action, data):
        if action != "notify_status_update":
            return
        for pin in self.devices:
            out_name = pin.split()[1]
            if not out_name.startswith("EPRESS"):
                continue
            if pin in data and "value" in data[pin]:
                val = float(data[pin]["value"])
                if out_name in self.labels:
                    self.labels[out_name].set_text(f"{out_name}: {(val/2):.3f} MPa")
