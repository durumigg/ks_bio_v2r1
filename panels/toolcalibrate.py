import re
import logging
import gi

gi.require_version("Gtk", "3.0")
from gi.repository import Gtk
from ks_includes.KlippyGcodes import KlippyGcodes
from ks_includes.screen_panel import ScreenPanel


class Panel(ScreenPanel):
    distances = [".01", ".1", ".5", "1", "5", "10", "20"]
    distance = distances[-2]
    tools = ["T0","T1","T2"]
    toolson = tools[-2]
    test_cnt = 0

    def __init__(self, screen, title):
        title = title or _("Tool Calibrate")
        super().__init__(screen, title)

        if self.ks_printer_cfg is not None:
            dis = self.ks_printer_cfg.get("move_distances", "")
            if re.match(r"^[0-9,\.\s]+$", dis):
                dis = [str(i.strip()) for i in dis.split(",")]
                if 1 < len(dis) <= 7:
                    self.distances = dis
                    self.distance = self.distances[-2]
        self.current_pos =[.0, .0, .0, .0, .0] # U, Y, TZ1, TZ2, TZ3 1~5
        self.settings = {}
        self.menu.append("move_menu")
        self.buttons = {
            "y+": self._gtk.Button("arrow-up", "Y+", "color2"),
            "y-": self._gtk.Button("arrow-down", "Y-", "color2"),
            "tz1+": self._gtk.Button("arrow-up", "TZ1+", "color5"),
            "tz1-": self._gtk.Button("arrow-down", "TZ1-", "color5"),
            "tz2+": self._gtk.Button("arrow-up", "TZ2+", "color5"),
            "tz2-": self._gtk.Button("arrow-down", "TZ2-", "color5"),
            "tz3+": self._gtk.Button("arrow-up", "TZ3+", "color5"),
            "tz3-": self._gtk.Button("arrow-down", "TZ3-", "color5"),
            "u+": self._gtk.Button("arrow-right", "U+", "color5"),
            "u-": self._gtk.Button("arrow-left", "U-", "color5"),
            "savepos": self._gtk.Button("file", "Save\nPosition", "color6"),
            "initpos": self._gtk.Button("bed-level-center", "0 Set", "color6"),
            "setpos": self._gtk.Button("check", "Apply Position", "color6"),
        }
        # wolk_add : up to v-~tz1+
        self.buttons["y+"].connect("clicked", self.move, "Y", "+")
        self.buttons["y-"].connect("clicked", self.move, "Y", "-")
        # wolk_add
        self.buttons["tz1+"].connect("clicked", self.move, "TZ1", "+")
        self.buttons["tz1-"].connect("clicked", self.move, "TZ1", "-")
        self.buttons["tz2+"].connect("clicked", self.move, "TZ2", "+")
        self.buttons["tz2-"].connect("clicked", self.move, "TZ2", "-")
        self.buttons["tz3+"].connect("clicked", self.move, "TZ3", "+")
        self.buttons["tz3-"].connect("clicked", self.move, "TZ3", "-")
        self.buttons["u+"].connect("clicked", self.move, "U", "+")
        self.buttons["u-"].connect("clicked", self.move, "U", "-")
        
        self.buttons["setpos"].connect("clicked", self.setposition)
        save_script = {"script": "_EXT_OFFSETPOS_STORE AXIS=SAVE"}
        self.buttons["savepos"].connect(
            "clicked", 
            self._screen._confirm_send_action, 
            _("Store Memory?"),
            "printer.gcode.script",
            save_script,
            )
        init_script = {"script": "_EXT_OFFSETPOS_STORE AXIS=INIT"}
        self.buttons["initpos"].connect(
            "clicked", 
            self._screen._confirm_send_action, 
            _("Are you sure you wish to 0 pos set?"),
            "printer.gcode.script",
            init_script,
            )
        
        grid = Gtk.Grid(row_homogeneous=True, column_homogeneous=True)
        
        grid.attach(self.buttons["y+"], 2, 0, 1, 1)
        grid.attach(self.buttons["y-"], 2, 1, 1, 1)
        grid.attach(self.buttons["tz1+"], 4, 0, 1, 1)
        grid.attach(self.buttons["tz1-"], 5, 0, 1, 1)
        grid.attach(self.buttons["tz2+"], 4, 1, 1, 1)
        grid.attach(self.buttons["tz2-"], 5, 1, 1, 1)
        grid.attach(self.buttons["tz3+"], 4, 2, 1, 1)
        grid.attach(self.buttons["tz3-"], 5, 2, 1, 1)
        grid.attach(self.buttons["u+"], 3, 1, 1, 1)
        grid.attach(self.buttons["u-"], 1, 1, 1, 1)
        
        toolselect = Gtk.Grid()
        for j1, i1 in enumerate(self.tools):
            self.labels[i1] = self._gtk.Button(label=i1)
            self.labels[i1].set_direction(Gtk.TextDirection.LTR)
            self.labels[i1].connect("clicked", self.change_tool, i1)
            ctx = self.labels[i1].get_style_context()
            ctx.add_class("vertical_togglebuttons")
            if i1 == self.toolson:
                ctx.add_class("vertical_togglebuttons_active")
            toolselect.attach(self.labels[i1], 0, j1, 1, 1)
        grid.attach(toolselect, 8, 0, 1, 3)


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
        self.labels["pos_xy"] = Gtk.Label()
        self.labels["pos_z123"] = Gtk.Label()
        self.labels["pos_tz1"] = Gtk.Label()
        self.labels["pos_tz2"] = Gtk.Label()
        self.labels["pos_tz3"] = Gtk.Label()
        # end_add
        self.labels["move_dist"] = Gtk.Label(label=_("Move Dist. (mm)"))
        self.labels["abs_pos"] = Gtk.Label(label=_("Abs\nPos\n(mm)"))

        bottomgrid = Gtk.Grid(row_homogeneous=True, column_homogeneous=True)
        bottomgrid.set_direction(Gtk.TextDirection.LTR)
        grid.attach(self.labels["pos_xy"], 2, 2, 1, 1)
        grid.attach(self.labels["pos_z123"], 3, 2, 1, 1)
        bottomgrid.attach(self.buttons["savepos"], 3, 0, 3, 2)
        bottomgrid.attach(self.buttons["initpos"], 0, 0, 1, 2)
        bottomgrid.attach(self.buttons["setpos"], 1, 0, 2, 2)
        #bottomgrid.attach(self.labels["pos_z"], 2, 0, 1, 1)
        # wolk_add
        grid.attach(self.labels["pos_tz1"], 6, 0, 2, 1)
        grid.attach(self.labels["pos_tz2"], 6, 1, 2, 1)
        grid.attach(self.labels["pos_tz3"], 6, 2, 2, 1)
        grid.attach(self.labels["abs_pos"], 1, 2, 1, 1)
        bottomgrid.attach(self.labels["move_dist"], 6, 1, 2, 1) # wolk_chg org:0131
        # end
        self.labels["move_menu"] = Gtk.Grid(
            row_homogeneous=True, column_homogeneous=True
        )
        self.labels["move_menu"].attach(grid, 0, 0, 1, 3)
        self.labels["move_menu"].attach(bottomgrid, 0, 3, 1, 1)
        self.labels["move_menu"].attach(distgrid, 0, 4, 1, 1)

        self.content.add(self.labels["move_menu"])


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
        if ("gcode_macro _EXT_AXIS_STA" in data) or ("gcode_macro _EXT_OFFSETPOS_STORE" in data):
            Flag_test = True
        if "Store CMD :" in data :
            logging.info(f"############## refresh_screen_custom in :{data}")
            Flag_test = True
            self.test_cnt = 1
        # end_add
        if action != "notify_status_update":
            return
        if Flag_test or (self.test_cnt >= 1) or (
            "gcode_move" in data
            or "toolhead" in data
            and "homed_axes" in data["toolhead"]
        ):
            logging.info(f"### Refresh ###")
            self.test_cnt = self.test_cnt + 1
            if self.test_cnt >= 2 : self.test_cnt = 0
            #logging.info(f"### cnt ### : {self.test_cnt}")
            homed_axes = self._printer.get_stat("toolhead", "homed_axes")
            # wolk_add
            ex_axis_tz1 = self._printer.get_stat("gcode_macro _EXT_AXIS_STA", "a0_pos")
            ex_axis_tz2 = self._printer.get_stat("gcode_macro _EXT_AXIS_STA", "a1_pos")
            ex_axis_tz3 = self._printer.get_stat("gcode_macro _EXT_AXIS_STA", "a2_pos")
            ex_axis_u0 = self._printer.get_stat("gcode_macro _EXT_AXIS_STA", "u0_pos")
            ex_axis_v0 = self._printer.get_stat("gcode_macro _EXT_AXIS_STA", "v0_pos")
            
            cr_t0_xp = self._printer.get_stat("gcode_macro _EXT_OFFSETPOS_STA", "t0_x_pos")
            cr_t0_yp = self._printer.get_stat("gcode_macro _EXT_OFFSETPOS_STA", "t0_y_pos")
            cr_t0_zp = self._printer.get_stat("gcode_macro _EXT_OFFSETPOS_STA", "t0_z_pos")
            cr_t1_xp = self._printer.get_stat("gcode_macro _EXT_OFFSETPOS_STA", "t1_x_pos")
            cr_t1_yp = self._printer.get_stat("gcode_macro _EXT_OFFSETPOS_STA", "t1_y_pos")
            cr_t1_zp = self._printer.get_stat("gcode_macro _EXT_OFFSETPOS_STA", "t1_z_pos")
            cr_t2_xp = self._printer.get_stat("gcode_macro _EXT_OFFSETPOS_STA", "t2_x_pos")
            cr_t2_yp = self._printer.get_stat("gcode_macro _EXT_OFFSETPOS_STA", "t2_y_pos")
            cr_t2_zp = self._printer.get_stat("gcode_macro _EXT_OFFSETPOS_STA", "t2_z_pos")
            
            sv_t0xp = self._printer.get_stat("save_variables", "variables").get('t0xpos')
            sv_t0yp = self._printer.get_stat("save_variables", "variables").get('t0ypos')
            sv_t0zp = self._printer.get_stat("save_variables", "variables").get('t0zpos')
            sv_t1xp = self._printer.get_stat("save_variables", "variables").get('t1xpos')
            sv_t1yp = self._printer.get_stat("save_variables", "variables").get('t1ypos')
            sv_t1zp = self._printer.get_stat("save_variables", "variables").get('t1zpos')
            sv_t2xp = self._printer.get_stat("save_variables", "variables").get('t2xpos')
            sv_t2yp = self._printer.get_stat("save_variables", "variables").get('t2ypos')
            sv_t2zp = self._printer.get_stat("save_variables", "variables").get('t2zpos')
            # end_add
            for i, axis in enumerate(("x", "y", "z")):
                if axis not in homed_axes:
                    self.labels[f"pos_{axis}"].set_text(f"{axis.upper()}: ?")
                elif "gcode_move" in data and "gcode_position" in data["gcode_move"]:
                    self.labels[f"pos_{axis}"].set_text(
                        f"{axis.upper()}: {data['gcode_move']['gcode_position'][i]:.2f}"
                    )
            #self.current_pos[1] = data['gcode_move']['gcode_position'][1]
            self.current_pos[1] = self._printer.get_stat("gcode_move", "gcode_position")[1]
            #logging.info(f"### test2 logging {test2}")
            # wolk_add
            self.labels[f"pos_z123"].set_text(f"TZ1: {ex_axis_tz1:.2f}\nTZ2: {ex_axis_tz2:.2f}\nTZ3: {ex_axis_tz3:.2f}")
            self.labels[f"pos_xy"].set_text(f"U: {ex_axis_u0:.2f}\nY: {self.current_pos[1]:.2f}")
            self.labels[f"pos_tz1"].set_text(
                f"\tcurrent/stored\n  U: {cr_t0_xp:.2f}\t/ {sv_t0xp:.2f}\n  Y: {cr_t0_yp:.2f}\t/ {sv_t0yp:.2f}\n  Z: {cr_t0_zp:.2f}\t/ {sv_t0zp:.2f}")
            self.labels[f"pos_tz1"].set_alignment(0, .5)
            self.labels[f"pos_tz2"].set_text(
                f"  U: {cr_t1_xp:.2f}\t/ {sv_t1xp:.2f}\n  Y: {cr_t1_yp:.2f}\t/ {sv_t1yp:.2f}\n  Z: {cr_t1_zp:.2f}\t/ {sv_t1zp:.2f}")
            self.labels[f"pos_tz2"].set_alignment(0, .5)
            self.labels[f"pos_tz3"].set_text(
                f"  U: {cr_t2_xp:.2f}\t/ {sv_t2xp:.2f}\n  Y: {cr_t2_yp:.2f}\t/ {sv_t2yp:.2f}\n  Z: {cr_t2_zp:.2f}\t/ {sv_t2zp:.2f}")
            self.labels[f"pos_tz3"].set_alignment(0, .5)
            # end_add
            self.current_pos[0] = ex_axis_u0
            self.current_pos[2] = ex_axis_tz1
            self.current_pos[3] = ex_axis_tz2
            self.current_pos[4] = ex_axis_tz3

    def change_distance(self, widget, distance):
        logging.info(f"### Distance {distance}")
        self.labels[f"{self.distance}"].get_style_context().remove_class(
            "horizontal_togglebuttons_active"
        )
        self.labels[f"{distance}"].get_style_context().add_class(
            "horizontal_togglebuttons_active"
        )
        self.distance = distance
        
    def change_tool(self, widget, tool):
        logging.info(f"### tool {tool}")
        self.labels[f"{self.toolson}"].get_style_context().remove_class(
            "vertical_togglebuttons_active"
        )
        self.labels[f"{tool}"].get_style_context().add_class(
            "vertical_togglebuttons_active"
        )
        self.toolson = tool

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
        
    def setposition(self, widget):
        #_EXT_OFFSETPOS_STORE AXIS=TZ3 X=100.1 Y=-200.2 Z=300.3
        # self.current_pos[] U Y TZ1 TZ2 TZ3
        script_cs = "\tcurrent/stored\n"
        save_data = f"\n\n\tApply Data\nU: {self.current_pos[0]:.2f} Y: {self.current_pos[1]:.2f}"

        if self.toolson == "T0":
            tool = "T0"
            pos_info = "pos_tz1"
            zdist = self.current_pos[2]
            script_css = "\tMemory\n" + self.labels[pos_info].get_text()
            save_data = save_data + f" Z: {self.current_pos[2]:.2f}"
        elif self.toolson == "T1":
            tool = "T1"
            pos_info = "pos_tz2"
            zdist = self.current_pos[3]
            script_css = "\tMemory\n" + script_cs + self.labels[pos_info].get_text()
            save_data = save_data + f" Z: {self.current_pos[3]:.2f}"
        elif self.toolson == "T2":
            tool = "T2"
            pos_info = "pos_tz3"
            zdist = self.current_pos[4]
            script_css = "\tMemory\n" + script_cs + self.labels[pos_info].get_text()
            save_data = save_data + f" Z: {self.current_pos[4]:.2f}"
            
        script = f"_EXT_OFFSETPOS_STORE AXIS={tool} X={self.current_pos[0]} Y={self.current_pos[1]} Z={zdist}"
        #logging.info(f"############## no xyz~~ {script}")
    
        test3 = self._screen._confirm_send_action(
            widget,
            _("\tApply?") + f"\n\n\t{tool}\n\n" + script_css + save_data,
            "printer.gcode.script",
            {"script": script}
        )