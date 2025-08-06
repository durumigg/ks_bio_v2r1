import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk


class NumericKeypad(Gtk.Box):
    def __init__(self, screen, on_value_entered, on_cancel):
        super().__init__(orientation=Gtk.Orientation.VERTICAL)
        self.screen = screen
        self.on_value_entered = on_value_entered
        self._gtk = screen.gtk

        self.entry = Gtk.Entry(hexpand=True, xalign=0.5, max_length=5)
        self.entry.connect("activate", self._on_confirm)

        top = Gtk.Box(spacing=5)
        top.add(self.entry)

        btn_cancel = self._gtk.Button("cancel", scale=.66)
        btn_cancel.connect("clicked", on_cancel)
        top.add(btn_cancel)

        grid = Gtk.Grid(row_homogeneous=True, column_homogeneous=True)
        keys = ["1", "2", "3", "4", "5", "6", "7", "8", "9", "B", "0", "."]
        for idx, key in enumerate(keys):
            button = self._gtk.Button(label=key, style="numpad_key")
            button.connect("clicked", self._on_key_press, key)
            grid.attach(button, idx % 3, idx // 3, 1, 1)

        bottom = Gtk.Box()
        btn_ok = self._gtk.Button("complete", style="color1", scale=1.1)
        btn_ok.connect("clicked", self._on_confirm)
        bottom.add(btn_ok)

        self.pack_start(top, False, False, 0)
        self.pack_start(grid, True, True, 0)
        self.pack_start(bottom, False, False, 0)

    def _on_key_press(self, widget, key):
        current = self.entry.get_text()
        if key == "B":
            self.entry.set_text(current[:-1])
        else:
            self.entry.set_text(current + key)

    def _on_confirm(self, widget=None):
        try:
            value = float(self.entry.get_text())
            self.on_value_entered(value)
        except ValueError:
            self.screen.show_popup_message(_("Invalid value"))
