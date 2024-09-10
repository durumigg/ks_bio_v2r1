import logging
import re
import gi

gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, GLib, Pango
from ks_includes.KlippyGcodes import KlippyGcodes
from ks_includes.screen_panel import ScreenPanel
from ks_includes.widgets.autogrid import AutoGrid
from ks_includes.KlippyGtk import find_widget
from ks_includes.functions import parse_bool

#wolk_add : GLib, import parse_bool

class Panel(ScreenPanel):

    def __init__(self, screen, title):
        title = title or _("Extrude")
        super().__init__(screen, title)
        self.current_extruder = self._printer.get_stat("toolhead", "extruder")
        macros = self._printer.get_config_section_list("gcode_macro ")
        self.load_filament = any("LOAD_FILAMENT" in macro.upper() for macro in macros)
        self.unload_filament = any("UNLOAD_FILAMENT" in macro.upper() for macro in macros)

        self.speeds = ['1', '2', '5', '25']
        self.distances = ['5', '10', '15', '25']
        if self.ks_printer_cfg is not None:
            dis = self.ks_printer_cfg.get("extrude_distances", '')
            if re.match(r'^[0-9,\s]+$', dis):
                dis = [str(i.strip()) for i in dis.split(',')]
                if 1 < len(dis) < 5:
                    self.distances = dis
            vel = self.ks_printer_cfg.get("extrude_speeds", '')
            if re.match(r'^[0-9,\s]+$', vel):
                vel = [str(i.strip()) for i in vel.split(',')]
                if 1 < len(vel) < 5:
                    self.speeds = vel
        self.distance = int(self.distances[1])
        self.speed = int(self.speeds[1])
        self.buttons = {
            'extrude': self._gtk.Button("extrude", _("Extrude"), "color4"),
            'load': self._gtk.Button("arrow-down", _("Load"), "color3"),
            'unload': self._gtk.Button("arrow-up", _("Unload"), "color2"),
            'retract': self._gtk.Button("retract", _("Retract"), "color1"),
            'temperature': self._gtk.Button("heat-up", _("Temperature"), "color4"),
            'spoolman': self._gtk.Button("spoolman", "Spoolman", "color3"),
            'pressure': self._gtk.Button("settings", _("Pressure Advance"), "color2"),
            'retraction': self._gtk.Button("settings", _("Retraction"), "color1")
        }
        self.buttons['extrude'].connect("clicked", self.extrude, "+")
        self.buttons['load'].connect("clicked", self.load_unload, "+")
        self.buttons['unload'].connect("clicked", self.load_unload, "-")
        self.buttons['retract'].connect("clicked", self.extrude, "-")
        self.buttons['temperature'].connect("clicked", self.menu_item_clicked, {
            "panel": "temperature"
        })
        self.buttons['spoolman'].connect("clicked", self.menu_item_clicked, {
            "panel": "spoolman"
        })
        self.buttons['pressure'].connect("clicked", self.menu_item_clicked, {
            "panel": "pressure_advance"
        })
        self.buttons['retraction'].connect("clicked", self.menu_item_clicked, {
            "panel": "retraction"
        })

        xbox = Gtk.Box(homogeneous=True)
        limit = 4
        i = 0
        extruder_buttons = []
        self.labels = {}
        for extruder in self._printer.get_tools():
            if self._printer.extrudercount == 1:
                self.labels[extruder] = self._gtk.Button("extruder", "")
            else:
                n = self._printer.get_tool_number(extruder)
                self.labels[extruder] = self._gtk.Button(f"extruder-{n}", f"T{n}")
                self.labels[extruder].connect("clicked", self.change_extruder, extruder)
            if extruder == self.current_extruder:
                self.labels[extruder].get_style_context().add_class("button_active")
            if self._printer.extrudercount < limit:
                xbox.add(self.labels[extruder])
                i += 1
            else:
                extruder_buttons.append(self.labels[extruder])
        for widget in self.labels.values():
            label = find_widget(widget, Gtk.Label)
            label.set_justify(Gtk.Justification.CENTER)
            label.set_line_wrap(True)
            label.set_lines(2)
        if extruder_buttons:
            self.labels['extruders'] = AutoGrid(extruder_buttons, vertical=self._screen.vertical_mode)
            self.labels['extruders_menu'] = self._gtk.ScrolledWindow()
            self.labels['extruders_menu'].add(self.labels['extruders'])
        if self._printer.extrudercount >= limit:
            changer = self._gtk.Button("toolchanger")
            changer.connect("clicked", self.load_menu, 'extruders', _('Extruders'))
            xbox.add(changer)
            self.labels["current_extruder"] = self._gtk.Button("extruder", "")
            xbox.add(self.labels["current_extruder"])
            self.labels["current_extruder"].connect("clicked", self.load_menu, 'extruders', _('Extruders'))
        if not self._screen.vertical_mode:
            #xbox.add(self.buttons['pressure']) #wolk_chg
            i += 1
        if self._printer.get_config_section("firmware_retraction") and not self._screen.vertical_mode:
            xbox.add(self.buttons['retraction'])
            i += 1
        if i < limit:
            xbox.add(self.buttons['temperature'])
        if i < (limit - 1) and self._printer.spoolman:
            xbox.add(self.buttons['spoolman'])

        distgrid = Gtk.Grid()
        for j, i in enumerate(self.distances):
            self.labels[f"dist{i}"] = self._gtk.Button(label=i)
            self.labels[f"dist{i}"].connect("clicked", self.change_distance, int(i))
            ctx = self.labels[f"dist{i}"].get_style_context()
            ctx.add_class("horizontal_togglebuttons")
            if int(i) == self.distance:
                ctx.add_class("horizontal_togglebuttons_active")
            distgrid.attach(self.labels[f"dist{i}"], j, 0, 1, 1)

        speedgrid = Gtk.Grid()
        for j, i in enumerate(self.speeds):
            self.labels[f"speed{i}"] = self._gtk.Button(label=i)
            self.labels[f"speed{i}"].connect("clicked", self.change_speed, int(i))
            ctx = self.labels[f"speed{i}"].get_style_context()
            ctx.add_class("horizontal_togglebuttons")
            if int(i) == self.speed:
                ctx.add_class("horizontal_togglebuttons_active")
            speedgrid.attach(self.labels[f"speed{i}"], j, 0, 1, 1)

        distbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.labels['extrude_dist'] = Gtk.Label(_("Distance (mm)"))
        distbox.pack_start(self.labels['extrude_dist'], True, True, 0)
        distbox.add(distgrid)
        speedbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.labels['extrude_speed'] = Gtk.Label(_("Speed (mm/s)"))
        speedbox.pack_start(self.labels['extrude_speed'], True, True, 0)
        speedbox.add(speedgrid)

        filament_sensors = self._printer.get_filament_sensors()
        sensors = Gtk.Grid(valign=Gtk.Align.CENTER, row_spacing=5, column_spacing=5)
        if len(filament_sensors) > 0:
            for s, x in enumerate(filament_sensors):
                if s > limit:
                    break
                name = x[23:].strip()
                self.labels[x] = {
                    'label': Gtk.Label(label=self.prettify(name), hexpand=True, halign=Gtk.Align.CENTER,
                                       ellipsize=Pango.EllipsizeMode.END),
                    'switch': Gtk.Switch(width_request=round(self._gtk.font_size * 2),
                                         height_request=round(self._gtk.font_size)),
                    'box': Gtk.Box()
                }
                self.labels[x]['switch'].connect("notify::active", self.enable_disable_fs, name, x)
                self.labels[x]['box'].pack_start(self.labels[x]['label'], True, True, 10)
                self.labels[x]['box'].pack_start(self.labels[x]['switch'], False, False, 0)
                self.labels[x]['box'].get_style_context().add_class("filament_sensor")
                sensors.attach(self.labels[x]['box'], s, 0, 1, 1)

        grid = Gtk.Grid(column_homogeneous=True)
        grid.attach(xbox, 0, 0, 4, 1)

        if self._screen.vertical_mode:
            grid.attach(self.buttons['extrude'], 0, 1, 2, 1)
            grid.attach(self.buttons['retract'], 2, 1, 2, 1)
            grid.attach(self.buttons['load'], 0, 2, 2, 1)
            grid.attach(self.buttons['unload'], 2, 2, 2, 1)
            settings_box = Gtk.Box(homogeneous=True)
            settings_box.add(self.buttons['pressure'])
            if self._printer.get_config_section("firmware_retraction"):
                settings_box.add(self.buttons['retraction'])
            grid.attach(settings_box, 0, 3, 4, 1)
            grid.attach(distbox, 0, 4, 4, 1)
            grid.attach(speedbox, 0, 5, 4, 1)
            grid.attach(sensors, 0, 6, 4, 1)
        else:
            grid.attach(self.buttons['extrude'], 0, 1, 1, 1) # 0211
            #grid.attach(self.buttons['load'], 1, 2, 1, 1) #wolk_chg
            #grid.attach(self.buttons['unload'], 2, 2, 1, 1)
            grid.attach(self.buttons['retract'], 1, 1, 1, 1) # 3211
            grid.attach(distbox, 0, 4, 2, 1)
            grid.attach(speedbox, 2, 4, 2, 1)
            grid.attach(sensors, 0, 4, 4, 1)
        
        #wolk_add
        self.devices = {}
        # Create a grid for all devices
        self.labels['devices'] = Gtk.Grid(column_homogeneous=True)#valign=Gtk.Align.CENTER)    

        grid.attach(self.labels['devices'],0,2,4,1)
        output_pins = self._printer.get_pwm_tools() + self._printer.get_output_pins()
        logging.info(f"output pin: {output_pins}")
        for pin in output_pins:
            # Support for hiding devices by name
            out_name = pin.split()[1]
            if out_name.startswith("_"):
                continue
            if out_name.startswith("EPRESS"):
                logging.info(f"EPRESS search: {out_name}")
                out_name = Gtk.Label(
                    hexpand=True, vexpand=True, halign=Gtk.Align.START, valign=Gtk.Align.CENTER,
                    wrap=True, wrap_mode=Pango.WrapMode.WORD_CHAR)
                out_name.set_markup(f'\n<big><b>{" ".join(pin.split(" ")[1:])}</b></big>\n')
                self.devices[pin] = {}
                section = self._printer.get_config_section(pin)
                if parse_bool(section.get('pwm', 'false')) or parse_bool(section.get('hardware_pwm', 'false')):
                    #logging.info(f"in if: {out_name}, pin: {pin}")
                    scale = Gtk.Scale.new_with_range(Gtk.Orientation.HORIZONTAL, min=0, max=100, step=1)
                    scale.set_value(self.check_pin_value(pin))
                    scale.set_digits(0)
                    scale.set_hexpand(True)
                    scale.set_has_origin(True)
                    scale.get_style_context().add_class("fan_slider")
                    self.devices[pin]['scale'] = scale
                    scale.connect("button-release-event", self.set_output_pin, pin)

                    min_btn = self._gtk.Button("cancel", None, "color1", 0.4) #1)
                    min_btn.set_hexpand(False)
                    min_btn.connect("clicked", self.update_pin_value, pin, 0)
                    pin_col = Gtk.Box(spacing=5)
                    pin_col.add(min_btn)
                    pin_col.add(scale)
                    self.devices[pin]["row"] = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
                    self.devices[pin]["row"].add(out_name)
                    self.devices[pin]["row"].add(pin_col)
                    
                    #logging.info(f"pinpinpinpinout_name: {pin}")
                    
        self.labels['devices'].attach(self.devices['output_pin EPRESS1']['row'], 0, 1, 1, 1)
        self.labels['devices'].attach(self.devices['output_pin EPRESS2']['row'], 1, 1, 1, 1)
        self.labels['devices'].attach(self.devices['output_pin EPRESS3']['row'], 2, 1, 1, 1)
        
        # add_end

        self.menu = ['extrude_menu']
        self.labels['extrude_menu'] = grid
        self.content.add(self.labels['extrude_menu'])
    
    # wolk_add
    def set_output_pin(self, widget, event, pin):
        if isinstance(widget, Gtk.Switch):
            widget.set_sensitive(False)
        if 'scale' in self.devices[pin]:
            value = self.devices[pin]["scale"].get_value() / 100
        elif 'switch' in self.devices[pin]:
            value = 1 if self.devices[pin]['switch'].get_active() else 0
        else:
            logging.error(f'unknown value for {widget} {event} {pin}')
            return
        self._screen._ws.klippy.gcode_script(f'SET_PIN PIN={" ".join(pin.split(" ")[1:])} VALUE={value}')
        GLib.timeout_add_seconds(1, self.check_pin_value, pin, widget)
                
    def check_pin_value(self, pin, widget=None):
        self.update_pin_value(None, pin, self._printer.get_pin_value(pin))
        if widget and isinstance(widget, Gtk.Switch):
            widget.set_sensitive(True)
        return False

    def update_pin_value(self, widget, pin, value):
        if pin not in self.devices:
            return
        if 'scale' in self.devices[pin]:
            self.devices[pin]['scale'].disconnect_by_func(self.set_output_pin)
            self.devices[pin]['scale'].set_value(round(float(value) * 100))
            self.devices[pin]['scale'].connect("button-release-event", self.set_output_pin, pin)
        elif 'switch' in self.devices[pin]:
            self.devices[pin]['switch'].set_active(value == 1)
        if widget is not None:
            self.set_output_pin(widget, None, pin)
    # add_end

    def enable_buttons(self, enable):
        for button in self.buttons:
            if button in ("pressure", "retraction", "spoolman", "temperature"):
                continue
            self.buttons[button].set_sensitive(enable)

    def activate(self):
        self.enable_buttons(self._printer.state in ("ready", "paused"))

    def process_update(self, action, data):
        if action == "notify_gcode_response":
            if "action:cancel" in data or "action:paused" in data:
                self.enable_buttons(True)
            elif "action:resumed" in data:
                self.enable_buttons(False)
            return
        if action != "notify_status_update":
            return
        for x in self._printer.get_tools():
            if x in data:
                self.update_temp(
                    x,
                    self._printer.get_stat(x, "temperature"),
                    self._printer.get_stat(x, "target"),
                    self._printer.get_stat(x, "power"),
                )
        if "current_extruder" in self.labels:
            self.labels["current_extruder"].set_label(self.labels[self.current_extruder].get_label())

        if ("toolhead" in data and "extruder" in data["toolhead"] and
                data["toolhead"]["extruder"] != self.current_extruder):
            for extruder in self._printer.get_tools():
                self.labels[extruder].get_style_context().remove_class("button_active")
            self.current_extruder = data["toolhead"]["extruder"]
            self.labels[self.current_extruder].get_style_context().add_class("button_active")
            if "current_extruder" in self.labels:
                n = self._printer.get_tool_number(self.current_extruder)
                self.labels["current_extruder"].set_image(self._gtk.Image(f"extruder-{n}"))

        for x in self._printer.get_filament_sensors():
            if x in data:
                if 'enabled' in data[x]:
                    self.labels[x]['switch'].set_active(data[x]['enabled'])
                if 'filament_detected' in data[x]:
                    if self._printer.get_stat(x, "enabled"):
                        if data[x]['filament_detected']:
                            self.labels[x]['box'].get_style_context().remove_class("filament_sensor_empty")
                            self.labels[x]['box'].get_style_context().add_class("filament_sensor_detected")
                        else:
                            self.labels[x]['box'].get_style_context().remove_class("filament_sensor_detected")
                            self.labels[x]['box'].get_style_context().add_class("filament_sensor_empty")
                logging.info(f"{x}: {self._printer.get_stat(x)}")
        # wolk_add        
        for pin in self.devices:
            if pin in data and "value" in data[pin]:
                self.update_pin_value(None, pin, data[pin]["value"])
        # add_end

    def change_distance(self, widget, distance):
        logging.info(f"### Distance {distance}")
        self.labels[f"dist{self.distance}"].get_style_context().remove_class("horizontal_togglebuttons_active")
        self.labels[f"dist{distance}"].get_style_context().add_class("horizontal_togglebuttons_active")
        self.distance = distance

    def change_extruder(self, widget, extruder):
        logging.info(f"Changing extruder to {extruder}")
        for tool in self._printer.get_tools():
            self.labels[tool].get_style_context().remove_class("button_active")
        self.labels[extruder].get_style_context().add_class("button_active")
        self._screen._send_action(widget, "printer.gcode.script",
                                  {"script": f"T{self._printer.get_tool_number(extruder)}"})

    def change_speed(self, widget, speed):
        logging.info(f"### Speed {speed}")
        self.labels[f"speed{self.speed}"].get_style_context().remove_class("horizontal_togglebuttons_active")
        self.labels[f"speed{speed}"].get_style_context().add_class("horizontal_togglebuttons_active")
        self.speed = speed

    def extrude(self, widget, direction):
        self._screen._ws.klippy.gcode_script(KlippyGcodes.EXTRUDE_REL)
        self._screen._send_action(widget, "printer.gcode.script",
                                  {"script": f"G1 E{direction}{self.distance} F{self.speed * 60}"})

    def load_unload(self, widget, direction):
        if direction == "-":
            if not self.unload_filament:
                self._screen.show_popup_message("Macro UNLOAD_FILAMENT not found")
            else:
                self._screen._send_action(widget, "printer.gcode.script",
                                          {"script": f"UNLOAD_FILAMENT SPEED={self.speed * 60}"})
        if direction == "+":
            if not self.load_filament:
                self._screen.show_popup_message("Macro LOAD_FILAMENT not found")
            else:
                self._screen._send_action(widget, "printer.gcode.script",
                                          {"script": f"LOAD_FILAMENT SPEED={self.speed * 60}"})

    def enable_disable_fs(self, switch, gparams, name, x):
        if switch.get_active():
            self._screen._ws.klippy.gcode_script(f"SET_FILAMENT_SENSOR SENSOR={name} ENABLE=1")
            if self._printer.get_stat(x, "filament_detected"):
                self.labels[x]['box'].get_style_context().add_class("filament_sensor_detected")
            else:
                self.labels[x]['box'].get_style_context().add_class("filament_sensor_empty")
        else:
            self._screen._ws.klippy.gcode_script(f"SET_FILAMENT_SENSOR SENSOR={name} ENABLE=0")
            self.labels[x]['box'].get_style_context().remove_class("filament_sensor_empty")
            self.labels[x]['box'].get_style_context().remove_class("filament_sensor_detected")

    def update_temp(self, extruder, temp, target, power):
        if not temp:
            return
        new_label_text = f"{temp or 0:.0f}"
        if target:
            new_label_text += f"/{target:.0f}"
        new_label_text += "°\n"
        if self._show_heater_power and power:
            new_label_text += f" {power * 100:.0f}%"
        #find_widget(self.labels[extruder], Gtk.Label).set_text(new_label_text) # wolk_chg
    
    # wolk_add
    def update_pin_value(self, widget, pin, value):
        if pin not in self.devices:
            return
        if 'scale' in self.devices[pin]:
            self.devices[pin]['scale'].disconnect_by_func(self.set_output_pin)
            self.devices[pin]['scale'].set_value(round(float(value) * 100))
            self.devices[pin]['scale'].connect("button-release-event", self.set_output_pin, pin)
        elif 'switch' in self.devices[pin]:
            self.devices[pin]['switch'].set_active(value == 1)
        if widget is not None:
            self.set_output_pin(widget, None, pin)
    # add_end