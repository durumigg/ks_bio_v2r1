import re
import logging
import gi

gi.require_version("Gtk", "3.0")
from gi.repository import Gtk
from ks_includes.KlippyGcodes import KlippyGcodes
from ks_includes.screen_panel import ScreenPanel


class Panel(ScreenPanel):
    distances = [".1", ".5", "1", "5", "10", "25", "50"]
    distance = distances[-2]

    def __init__(self, screen, title):
        title = title or _("Move")
        super().__init__(screen, title)

        if self.ks_printer_cfg is not None:
            dis = self.ks_printer_cfg.get("move_distances", "")
            if re.match(r"^[0-9,\.\s]+$", dis):
                dis = [str(i.strip()) for i in dis.split(",")]
                if 1 < len(dis) <= 7:
                    self.distances = dis
                    self.distance = self.distances[-2]

        self.settings = {}
        self.menu.append("move_menu")
        self.buttons = {
            "x+": self._gtk.Button("arrow-right", "X+", "color1"),
            "x-": self._gtk.Button("arrow-left", "X-", "color1"),
            "y+": self._gtk.Button("arrow-up", "Y+", "color2"),
            "y-": self._gtk.Button("arrow-down", "Y-", "color2"),
            "z+": self._gtk.Button("z-farther", "Z+", "color11"),
            "z-": self._gtk.Button("z-closer", "Z-", "color11"),
            "tz1+": self._gtk.Button("arrow-up", "TZ1+", "color31"),
            "tz1-": self._gtk.Button("arrow-down", "TZ1-", "color31"),
            "tz2+": self._gtk.Button("arrow-up", "TZ2+", "color31"),
            "tz2-": self._gtk.Button("arrow-down", "TZ2-", "color31"),
            "tz3+": self._gtk.Button("arrow-up", "TZ3+", "color31"),
            "tz3-": self._gtk.Button("arrow-down", "TZ3-", "color31"),
            "u+": self._gtk.Button("arrow-up", "U+", "color21"),
            "u-": self._gtk.Button("arrow-down", "U-", "color21"),
            "v+": self._gtk.Button("arrow-right", "V+", "color21"),
            "v-": self._gtk.Button("arrow-left", "V-", "color21"),
            "home": self._gtk.Button("home", _("Home"), "color1"),
            "motors_off": self._gtk.Button("motor-off", _("Disable Motors"), "color1"),
        }
        # wolk_add : up to v-~tz1+
        self.buttons["x+"].connect("clicked", self.move, "X", "+")
        self.buttons["x-"].connect("clicked", self.move, "X", "-")
        self.buttons["y+"].connect("clicked", self.move, "Y", "+")
        self.buttons["y-"].connect("clicked", self.move, "Y", "-")
        self.buttons["z+"].connect("clicked", self.move, "Z", "+")
        self.buttons["z-"].connect("clicked", self.move, "Z", "-")
        # wolk_add
        self.buttons["tz1+"].connect("clicked", self.move, "TZ1", "+")
        self.buttons["tz1-"].connect("clicked", self.move, "TZ1", "-")
        self.buttons["tz2+"].connect("clicked", self.move, "TZ2", "+")
        self.buttons["tz2-"].connect("clicked", self.move, "TZ2", "-")
        self.buttons["tz3+"].connect("clicked", self.move, "TZ3", "+")
        self.buttons["tz3-"].connect("clicked", self.move, "TZ3", "-")
        self.buttons["u+"].connect("clicked", self.move, "U", "+")
        self.buttons["u-"].connect("clicked", self.move, "U", "-")
        self.buttons["v+"].connect("clicked", self.move, "V", "+")
        self.buttons["v-"].connect("clicked", self.move, "V", "-")
        # end_add
        self.buttons["home"].connect("clicked", self.home)
        script = {"script": "M18"}
        self.buttons["motors_off"].connect(
            "clicked",
            self._screen._confirm_send_action,
            _("Are you sure you wish to disable motors?"),
            "printer.gcode.script",
            script,
        )
        adjust = self._gtk.Button(
            "settings", None, "color2", 1, Gtk.PositionType.LEFT, 1
        )
        adjust.connect("clicked", self.load_menu, "options", _("Settings"))
        adjust.set_hexpand(False)
        grid = Gtk.Grid(row_homogeneous=True, column_homogeneous=True)
        if self._screen.vertical_mode:
            if self._screen.lang_ltr:
                grid.attach(self.buttons["x+"], 2, 1, 1, 1)
                grid.attach(self.buttons["x-"], 0, 1, 1, 1)
                grid.attach(self.buttons["z+"], 2, 2, 1, 1)
                grid.attach(self.buttons["z-"], 0, 2, 1, 1)
            else:
                grid.attach(self.buttons["x+"], 0, 1, 1, 1)
                grid.attach(self.buttons["x-"], 2, 1, 1, 1)
                grid.attach(self.buttons["z+"], 0, 2, 1, 1)
                grid.attach(self.buttons["z-"], 2, 2, 1, 1)
            grid.attach(adjust, 1, 2, 1, 1)
            grid.attach(self.buttons["y+"], 1, 0, 1, 1)
            grid.attach(self.buttons["y-"], 1, 1, 1, 1)

        else:
            if self._screen.lang_ltr:
                grid.attach(self.buttons["x+"], 2, 1, 1, 1)
                grid.attach(self.buttons["x-"], 0, 1, 1, 1)
            else:
                grid.attach(self.buttons["x+"], 0, 1, 1, 1)
                grid.attach(self.buttons["x-"], 2, 1, 1, 1)
            grid.attach(self.buttons["y+"], 1, 0, 1, 1)
            grid.attach(self.buttons["y-"], 1, 1, 1, 1)
            if self._config.get_config()["main"].getboolean("invert_z", False):
                grid.attach(self.buttons["z+"], 0, 0, 1, 1)
                grid.attach(self.buttons["z-"], 2, 0, 1, 1)
            else:
                grid.attach(self.buttons["z+"], 3, 0, 1, 1) # 2011
                grid.attach(self.buttons["z-"], 3, 1, 1, 1) # 0011
            # wolk_add
            grid.attach(self.buttons["tz1+"], 7, 0, 1, 1) # 0211
            grid.attach(self.buttons["tz1-"], 7, 1, 1, 1) # 1211
            grid.attach(self.buttons["tz2+"], 8, 0, 1, 1) # 2211
            grid.attach(self.buttons["tz2-"], 8, 1, 1, 1) # 3211
            grid.attach(self.buttons["tz3+"], 9, 0, 1, 1) # 4211
            grid.attach(self.buttons["tz3-"], 9, 1, 1, 1) # 5211
            grid.attach(self.buttons["u+"], 5, 0, 1, 1)
            grid.attach(self.buttons["u-"], 5, 1, 1, 1)
            grid.attach(self.buttons["v+"], 6, 1, 1, 1)
            grid.attach(self.buttons["v-"], 4, 1, 1, 1)
            # end_add

        grid.attach(self.buttons["home"], 2, 2, 3, 1) # wolk_chg org:0011
        grid.attach(self.buttons["motors_off"], 5, 2, 3, 1) # wolk_chg org:2011

        distgrid = Gtk.Grid()
        for j, i in enumerate(self.distances):
            self.labels[i] = self._gtk.Button(label=i)
            self.labels[i].set_direction(Gtk.TextDirection.LTR)
            self.labels[i].connect("clicked", self.change_distance, i)
            ctx = self.labels[i].get_style_context()
            ctx.add_class("horizontal_togglebuttons")
            if i == self.distance:
                ctx.add_class("horizontal_togglebuttons_active")
            distgrid.attach(self.labels[i], j, 0, 1, 1)

        for p in ("pos_x", "pos_y", "pos_z"):
            self.labels[p] = Gtk.Label()
        # wolk_add
        self.labels["pos_tz1"] = Gtk.Label()
        self.labels["pos_tz2"] = Gtk.Label()
        self.labels["pos_tz3"] = Gtk.Label()
        # end_add
        self.labels["move_dist"] = Gtk.Label(label=_("Move Distance (mm)"))

        bottomgrid = Gtk.Grid(row_homogeneous=True, column_homogeneous=True)
        bottomgrid.set_direction(Gtk.TextDirection.LTR)
        bottomgrid.attach(self.labels["pos_x"], 0, 0, 1, 1)
        bottomgrid.attach(self.labels["pos_y"], 1, 0, 1, 1)
        bottomgrid.attach(self.labels["pos_z"], 2, 0, 1, 1)
        # wolk_add
        bottomgrid.attach(self.labels["pos_tz1"], 3, 0, 1, 2)
        bottomgrid.attach(self.labels["pos_tz2"], 4, 0, 1, 2)
        bottomgrid.attach(self.labels["pos_tz3"], 5, 0, 1, 2)
        bottomgrid.attach(self.labels["move_dist"], 0, 1, 3, 1) # wolk_chg org:0131
        # end
        if not self._screen.vertical_mode:
            bottomgrid.attach(adjust, 5, 0, 1, 2) # wolk_chg org:3012

        self.labels["move_menu"] = Gtk.Grid(
            row_homogeneous=True, column_homogeneous=True
        )
        self.labels["move_menu"].attach(grid, 0, 0, 1, 3)
        self.labels["move_menu"].attach(bottomgrid, 0, 3, 1, 1)
        self.labels["move_menu"].attach(distgrid, 0, 4, 1, 1)

        self.content.add(self.labels["move_menu"])

        printer_cfg = self._printer.get_config_section("printer")
        # The max_velocity parameter is not optional in klipper config.
        # The minimum is 1, but least 2 values are needed to create a scale
        max_velocity = max(int(float(printer_cfg["max_velocity"])), 2)
        if "max_z_velocity" in printer_cfg:
            max_z_velocity = max(int(float(printer_cfg["max_z_velocity"])), 2)
        else:
            max_z_velocity = max_velocity

        configurable_options = [
            {
                "invert_x": {
                    "section": "main",
                    "name": _("Invert X"),
                    "type": "binary",
                    "tooltip": _("This will affect screw positions and mesh graph"),
                    "value": "False",
                    "callback": self.reinit_panels,
                }
            },
            {
                "invert_y": {
                    "section": "main",
                    "name": _("Invert Y"),
                    "type": "binary",
                    "tooltip": _("This will affect screw positions and mesh graph"),
                    "value": "False",
                    "callback": self.reinit_panels,
                }
            },
            {
                "invert_z": {
                    "section": "main",
                    "name": _("Invert Z"),
                    "tooltip": _(
                        "Swaps buttons if they are on top of each other, affects other panels"
                    ),
                    "type": "binary",
                    "value": "False",
                    "callback": self.reinit_move,
                }
            },
            {
                "move_speed_xy": {
                    "section": "main",
                    "name": _("XY Speed (mm/s)"),
                    "type": "scale",
                    "tooltip": _("Only for the move panel"),
                    "value": "50",
                    "range": [1, max_velocity],
                    "step": 1,
                }
            },
            {
                "move_speed_z": {
                    "section": "main",
                    "name": _("Z Speed (mm/s)"),
                    "type": "scale",
                    "tooltip": _("Only for the move panel"),
                    "value": "10",
                    "range": [1, max_z_velocity],
                    "step": 1,
                }
            },
        ]

        self.labels["options_menu"] = self._gtk.ScrolledWindow()
        self.labels["options"] = Gtk.Grid()
        self.labels["options_menu"].add(self.labels["options"])
        self.options = {}
        for option in configurable_options:
            name = list(option)[0]
            self.options.update(
                self.add_option("options", self.settings, name, option[name])
            )

    def reinit_panels(self, value):
        self._screen.panels_reinit.append("bed_level")
        self._screen.panels_reinit.append("bed_mesh")

    def reinit_move(self, widget):
        self._screen.panels_reinit.append("move")
        self._screen.panels_reinit.append("zcalibrate")
        self.menu.clear()

    def process_update(self, action, data):
        # wolk_add
        Flag_test = False
        if ("gcode_macro _EXT_AXIS_STA" in data):
            #logging.info(f"############## data in :")
            Flag_test = True
        # end_add
        if action != "notify_status_update":
            return
        if "toolhead" in data and "max_velocity" in data["toolhead"]:
            max_vel = max(int(float(data["toolhead"]["max_velocity"])), 2)
            adj = self.options["move_speed_xy"].get_adjustment()
            adj.set_upper(max_vel)
        if Flag_test or (
            "gcode_move" in data
            or "toolhead" in data
            and "homed_axes" in data["toolhead"]
        ):
            homed_axes = self._printer.get_stat("toolhead", "homed_axes")
            # wolk_add
            ex_axis_tz1 = self._printer.get_stat("gcode_macro _EXT_AXIS_STA", "a0_pos")
            ex_axis_tz2 = self._printer.get_stat("gcode_macro _EXT_AXIS_STA", "a1_pos")
            ex_axis_tz3 = self._printer.get_stat("gcode_macro _EXT_AXIS_STA", "a2_pos")
            ex_axis_u0 = self._printer.get_stat("gcode_macro _EXT_AXIS_STA", "u0_pos")
            ex_axis_v0 = self._printer.get_stat("gcode_macro _EXT_AXIS_STA", "v0_pos")
            #logging.info(f"############## process update in :")
            # end_add
            for i, axis in enumerate(("x", "y", "z")):
                if axis not in homed_axes:
                    self.labels[f"pos_{axis}"].set_text(f"{axis.upper()}: ?")
                elif "gcode_move" in data and "gcode_position" in data["gcode_move"]:
                    self.labels[f"pos_{axis}"].set_text(
                        f"{axis.upper()}: {data['gcode_move']['gcode_position'][i]:.2f}"
                    )
            # wolk_add
            self.labels[f"pos_tz1"].set_text(f"TZ1: {ex_axis_tz1:.2f}\nTZ2: {ex_axis_tz2:.2f}\nTZ3: {ex_axis_tz3:.2f}")
            self.labels[f"pos_tz2"].set_text(f"U: {ex_axis_u0:.2f}\nV: {ex_axis_v0:.2f}")
            # end_add

    def change_distance(self, widget, distance):
        logging.info(f"### Distance {distance}")
        self.labels[f"{self.distance}"].get_style_context().remove_class(
            "horizontal_togglebuttons_active"
        )
        self.labels[f"{distance}"].get_style_context().add_class(
            "horizontal_togglebuttons_active"
        )
        self.distance = distance

    def move(self, widget, axis, direction):
        axis = axis.lower()
        # wolk_chg
        if axis == "x" or axis == "y" or axis == "z" :
            if (
                self._config.get_config()["main"].getboolean(f"invert_{axis}", False)
                and axis != "z"
            ):
                direction = "-" if direction == "+" else "+"

            dist = f"{direction}{self.distance}"
            config_key = "move_speed_z" if axis == "Z" else "move_speed_xy"
            speed = (
                None
                if self.ks_printer_cfg is None
                else self.ks_printer_cfg.getint(config_key, None)
            )
            if speed is None:
                speed = self._config.get_config()["main"].getint(config_key, 20)
            speed = 60 * max(1, speed)
            script = f"{KlippyGcodes.MOVE_RELATIVE}\nG0 {axis}{dist} F{speed}"
            self._screen._send_action(widget, "printer.gcode.script", {"script": script})
            if self._printer.get_stat("gcode_move", "absolute_coordinates"):
                self._screen._ws.klippy.gcode_script("G90")
        # wolk_add
        else :
            axis_ex = ""
            if axis == "tz1":
                axis_ex = "A0"
            elif axis == "tz2":
                axis_ex = "A1"
            elif axis == "tz3":
                axis_ex = "A2"
            elif axis == "u":
                axis_ex = "U0"
            elif axis == "v":
                axis_ex = "V0"
            dist = f"{direction}{self.distance}"
            script = f"{axis_ex} R{dist.strip('+')}"
            self._screen._send_action(widget, "printer.gcode.script", {"script": script})
            #logging.info(f"############## no xyz~~ {axis}")
        # end_chg_add

    def home(self, widget):
        if "delta" in self._printer.get_config_section("printer")["kinematics"]:
            self._screen._send_action(widget, "printer.gcode.script", {"script": "G28"})
            return
        name = "homing"
        disname = self._screen._config.get_menu_name("move", name)
        menuitems = self._screen._config.get_menu_items("move", name)
        self._screen.show_panel("menu", disname, items=menuitems)
