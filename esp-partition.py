from Tkinter import *
import tkMessageBox
from tkFileDialog import asksaveasfilename, askdirectory, askopenfilename
from tkMessageBox import askokcancel
import csv
import os
import json
import webbrowser

"""
Author: Francis Ilechukwu
Credits: Elochukwu Ifediora C.
"""


class Template:
    def __init__(self, template=None):
        self.spiffs_count = 0
        self.template = []
        self.__index = 1
        if template is not None:
            self.is_valid = True
            # For now, a simple validity check... this requires more. developers who want to create custom templates
            # compatible with this program should be very careful to follow the rules... this is for future purposes.
            self.is_valid = "0x" not in template[0]  # Column Headers expected here.
            self.__index = 1
            template[0] = [x.lower() for x in template[0]]
            self.template = template
            for x in range(1, len(self.template)):
                self.__move_to_index(x)
                if self.get_column("subtype") == "spiffs":
                    self.spiffs_count += 1
            self.is_valid = self.spiffs_count <= 1
            self.__index = 1

    def refresh(self):
        self.is_valid = "0x" not in self.template[0]
        cache_index = self.__index
        for x in range(1, len(self.template)):
            self.__move_to_index(x)
            if self.get_column("subtype") == "spiffs":
                self.spiffs_count += 1
        self.is_valid = self.spiffs_count <= 1
        self.__index = cache_index

    def add_row(self, row):
        self.template.append(row)

    def has_spiffs(self):
        return self.spiffs_count > 0

    def move_to_next(self):
        if self.is_valid:
            if self.__index + 1 < len(self.template):
                self.__index += 1
                return True
            return False

    def __move_to_index(self, index):
        self.__index = index

    def get_row_count_without_spiffs(self):
        """
        gets the number of partitions excluding spiffs.
        -2 for header and spiffs
        :return: [int] partition count.
        """
        if self.is_valid:
            return len(self.template) - 2
        return -1

    def get_row_count(self):
        return len(self.template) - 1

    def move_to_first(self):
        self.__index = 1

    def get_column(self, name):
        if self.is_valid:
            x = 0
            for column in self.template[0]:
                if name == column:
                    return self.template[self.__index][x]
                x += 1
        return None

    def get_rows(self, with_spiffs=False):
        if self.is_valid:
            rows = []
            if not with_spiffs:
                cache_index = self.__index
                for x in range(1, len(self.template)):
                    self.__move_to_index(x)
                    if self.get_column("subtype") != "spiffs":
                        rows.append(self.get_row())
                self.__index = cache_index
                return rows

    def get_row(self):
        if self.is_valid:
            return self.template[self.__index]

    def get_spiffs_property(self, _property):
        if self.is_valid:
            cache_index = self.__index
            for x in range(1, len(self.template)):
                self.__move_to_index(x)
                if self.get_column("subtype") == "spiffs":
                    value = self.get_column(_property)
                    self.__index = cache_index
                    return value
            self.__index = cache_index

    def get_next_offset(self):
        if self.is_valid:
            return int(self.get_spiffs_property("offset"), 16)


class ESPPartitionGUI(Frame):
    def __init__(self, master=None, configs=None, templates=None):
        """
        Initialization of the Main GUI Form
        The Widgets are loaded and arranged here with the default ESP partition template.
        :param master: a Tk top level object obtained by calling Tk().
        """

        self.app_name = "ESP Partition GUI"

        Frame.__init__(self, master)

        if configs is None:
            self.configs = {}
        else:
            self.configs = configs

        if templates is None:
            self.templates = []
        else:
            self.templates = templates

        # Partition templating valid column order: used in the self.add_row(...) function. will also be used for
        # validation.
        self.template_column_order = {"name": 0, "type": 1, "subtype": 2, "offset": 3, "size": 4, "flags": 5}

        self.pack(fill=BOTH, side=TOP, expand=True)

        self.status_bar = Frame(master, borderwidth=1, relief=SUNKEN)
        self.status_bar.pack(side=LEFT, fill=BOTH, expand=True)
        self.message_var = StringVar()
        Label(self.status_bar, textvariable=self.message_var).pack(side=LEFT)

        # Configure all columns to be of layout weight 1.
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)
        self.grid_columnconfigure(2, weight=1)
        self.grid_columnconfigure(3, weight=1)
        self.grid_columnconfigure(4, weight=1)
        self.grid_columnconfigure(5, weight=1)
        self.grid_columnconfigure(6, weight=1)

        # IntVars to track checkboxes states
        self.sub_type_int_var = IntVar()
        self.offset_int_var = IntVar()
        self.size_int_var = IntVar()
        self.flags_int_var = IntVar()

        # Control Variables
        self.last_sub_type = 0x99
        self.next_offset = -1

        # StringVar to track radio button states.
        self.template_string_var = StringVar()
        self.template_string_var.set("U_DEF")

        # Builder list of tuples for radio buttons.
        self.template_tuples = [("Default Partition", "U_DEF", 1),
                                ("Minimal Partition", "U_MIN", 2)]

        # Declare and add radio buttons.
        for text, value, column in self.template_tuples:
            b = Radiobutton(self, text=text, variable=self.template_string_var, value=value,
                            command=self.template_radio_button_state_changed)
            b.grid(row=0, column=column)

        # Declare and add simple buttons
        self.add_partition_button = Button(self, text="Add Partition", command=self.add_row)
        self.add_partition_button.grid(row=0, column=3)
        self.plus_button = Button(self, text="+", command=self.add_row)

        b = Button(self, text="Remove Partition", command=self.remove_row)
        b.grid(row=0, column=4)
        b = Button(self, text="Refresh Partition", command=self.refresh)
        b.grid(row=0, column=5)
        self.generate_button = Button(self, text="Generate ->", command=self.generate)
        self.generate_button.grid(row=0, column=6)

        # Declare and add Checkboxes {Update These checkboxes have now become part of the header.}
        self.sub_type_checkbox = Checkbutton(self, text="SubType", variable=self.sub_type_int_var,
                                             command=self.toggle_sub_type).grid(row=1, column=3)
        self.offset_checkbox = Checkbutton(self, text="Offset", variable=self.offset_int_var,
                                           command=self.toggle_offset).grid(row=1, column=4)
        self.size_checkbox = Checkbutton(self, text="Size", variable=self.size_int_var,
                                         command=self.toggle_size).grid(row=1, column=5)

        self.flags_checkbox = Checkbutton(self, text="Flags", variable=self.flags_int_var,
                                          command=self.toggle_flags).grid(row=1, column=6)

        # Labels
        Label(self, text="Name").grid(row=1, column=1)
        Label(self, text="Type").grid(row=1, column=2)

        # Variable to hold references to widgets on screen.
        self.widgets = {"name": [], "type": [], "sub_type": [], "ar_buttons": [], "offset": [], "size": [], "flags": []}

        self.ui_entries = {}

        self.last_row = - 1
        self.forgotten_logical_indices = []

        # Control variable for detecting the last logical input row index of widgets regardless of grid row.
        self.last_logical_index = -1

        # Very Important and may differ in boards or templates to come.
        # a call to self.reflect_template
        self.spiffs_size = 0x0

        self.spiffs_logical_index = -1

        self.spiffs_row_index = -1

        self.ui_map = {}

        self.is_new_data = False

        self.max_spiffs_size = 0x3F7000

        self.reflect_template("default", self.templates[0]["template"])

        # Set by default disabled widgets.
        self.disable_widgets("sub_type")
        self.disable_widgets("offset")
        self.disable_widgets("size")
        self.disable_widgets("flags")

        # Menu bar
        self.menu_bar = Menu(self)
        self.master.config(menu=self.menu_bar)

        # File Menu
        self.file_menu = Menu(self.menu_bar, tearoff=0)
        self.menu_bar.add_cascade(label="Espressif", menu=self.file_menu)
        self.file_menu.add_command(label="New", command=self.new_partition_data)
        self.file_menu.add_command(label="Open", command=self.load_partition_data_from_file)
        self.recent_menu = Menu(self, tearoff=1)
        self.file_menu.add_cascade(label="Open Recent", menu=self.recent_menu)
        self.file_menu.add_command(label="Save", command=self.save_file)
        self.file_menu.add_command(label="Save As...", command=self.save_file_as)
        if "recent" in self.configs:
            for path in self.configs["recent"]:
                self.recent_menu.add_command(label=path, command=lambda x=path: self.load_partition_data_from_file(x))
        self.file_menu.add_separator()
        self.file_menu.add_command(label="Generate Partition", command=self.generate)
        self.file_menu.add_command(label="Convert Binary to CSV", command=self.convert_bin_to_csv)
        self.file_menu.add_command(label="Convert CSV to Binary", command=self.convert_csv_to_bin)
        self.file_menu.add_separator()
        self.file_menu.add_command(label="Preferences", command=self.show_preferences)
        self.file_menu.add_separator()
        self.file_menu.add_command(label="Help", command=self.help)
        self.file_menu.add_command(label="About", command=self.about)
        self.file_menu.add_separator()
        self.file_menu.add_command(label="Quit", command=self.frame_quit)

        self.preference_window = None
        self.about_window = None
        self.is_preference_open = False
        self.is_about_open = False
        self.currently_open_file = None

        self.generate_preference_string_var = StringVar()
        self.dump_path_preference_string_var = StringVar()
        self.esp32_path_string_var = StringVar()

        # Default.
        self.generate_preference_string_var.set("CSV")

    def save_file(self):
        if self.currently_open_file is not None:
            self.write_to_csv(self.currently_open_file)
            self.message_var.set("Partition Data Saved.")

    def save_file_as(self):
        file_name = asksaveasfilename(defaultextension=".csv", title="Open CSV file as...",
                                      filetypes=(("CSV File", "*.csv"), ("All Files", "*.*")))
        if file_name != "":
            self.write_to_csv(file_name)
            tkMessageBox.showinfo("Done Writing CSV File", "Done Writing CSV to {}".format(file_name))

    def close_preference_window(self):
        self.preference_window.destroy()
        self.is_preference_open = False

    def show_preferences(self):
        if not self.is_preference_open:
            self.is_preference_open = True
            self.preference_window = Toplevel()
            self.preference_window.protocol("WM_DELETE_WINDOW", self.close_preference_window)

            self.preference_window.maxsize(width=500, height=180)
            self.preference_window.title("Preferences")

            self.preference_window.grid_columnconfigure(0, weight=1)
            self.preference_window.grid_columnconfigure(1, weight=3)

            b = Radiobutton(self.preference_window, text="Generate Only CSV",
                            variable=self.generate_preference_string_var, value="CSV",
                            command=self.generate_radio_button_state_changed)
            b.grid(sticky=W)
            b = Radiobutton(self.preference_window, text="Generate Only Bin", value="BIN",
                            variable=self.generate_preference_string_var,
                            command=self.generate_radio_button_state_changed)
            b.grid(row=1, sticky=W)
            b = Radiobutton(self.preference_window, text="Generate Both", value="BOTH",
                            variable=self.generate_preference_string_var,
                            command=self.generate_radio_button_state_changed)
            b.grid(row=2, sticky=W)

            Label(self.preference_window, text="Set Arduino ESP32 Path:").grid(row=3, sticky=W)
            e = Entry(self.preference_window, textvariable=self.esp32_path_string_var, state=DISABLED,
                      width=70)
            e.grid(row=4, sticky=W)
            Button(self.preference_window, text="...", command=self.choose_esp32_path).grid(row=4, column=1, sticky=W,
                                                                                            padx=5)
            Label(self.preference_window, text="Set Partition Dump Path:").grid(row=5, sticky=W)
            e = Entry(self.preference_window, textvariable=self.dump_path_preference_string_var, state=DISABLED,
                      width=70)
            e.grid(row=6, sticky=W)
            Button(self.preference_window, text="...", command=self.choose_dump_path).grid(row=6, column=1, sticky=W,
                                                                                           padx=5)
            if "generate" in self.configs:
                self.generate_preference_string_var.set(self.configs["generate"])
            if "dump_path" in self.configs:
                self.dump_path_preference_string_var.set(self.configs["dump_path"])
            if "esp32_path" in self.configs:
                self.esp32_path_string_var.set(self.configs["esp32_path"])

    def generate_radio_button_state_changed(self):
        self.configs["generate"] = self.generate_preference_string_var.get()
        json.dump(self.configs, open("init.json", "w"))

    def choose_dump_path(self):
        dump_path = askdirectory()
        self.preference_window.focus()
        if dump_path != "":
            self.configs["dump_path"] = dump_path
            json.dump(self.configs, open("init.json", "w"))
            self.dump_path_preference_string_var.set(dump_path)

    def choose_esp32_path(self):
        """
        Opens a directory chooser dialog to select the root path of an arduino-esp32 installation. On selection, this
        function will check for the gen_esp32_part.py script in the expected folder before it can mark the selected
        folder as valid.
        :return: None
        """
        folder_string = askdirectory()
        if folder_string != "":
            if os.path.isfile(folder_string + "/tools/gen_esp32part.py"):
                self.configs["esp32_path"] = folder_string
                json.dump(self.configs, open("init.json", "w"))
                self.esp32_path_string_var.set(folder_string)
                tkMessageBox.showinfo("Success", "Arduino ESP32 root path was successfully set.")
            else:
                tkMessageBox.showerror("ESP Gen Script Error", "The Espressif ESP32 Gen Script was not found.")

    def refresh(self):
        self.next_offset = self.calibrate_offsets()

    def toggle_sub_type(self):
        """
        Toggles widget states of the Entry widgets int the sub type column.
        :return: None
        """
        enable = self.sub_type_int_var.get()
        if enable:
            self.enable_widgets("sub_type")
        else:
            self.disable_widgets("sub_type")

    def toggle_offset(self):
        """
        Toggles widget states of the Entry widgets int the offset column.
        :return: None
        """
        enable = self.offset_int_var.get()
        if enable:
            self.enable_widgets("offset")
        else:
            self.disable_widgets("offset")

    def toggle_size(self):
        """
        Toggles the widget states of the Entry widgets int the size column.
        :return:
        """
        enable = self.size_int_var.get()
        if enable:
            self.enable_widgets("size")
        else:
            self.disable_widgets("size")

    def toggle_flags(self):
        """
        Toggles widget states of the Entry widgets int the flags column.
        :return:
        """
        enable = self.flags_int_var.get()
        if enable:
            self.enable_widgets("flags")
        else:
            self.disable_widgets("flags")

    def disable_widgets(self, key):
        """
        disables all widgets with the given key fom the self.widgets dictionary.
        :param key: key name of widget group.
        :return: None.
        """
        entries = self.widgets[key]
        for entry in entries:
            if entry.winfo_exists() == 1:
                entry.config(state=DISABLED)

    def enable_widgets(self, key):
        """
        disables all widgets with the given key from the self.widgets dictionary.
        :param key: key name of widget group.
        :return: None.
        """
        entries = self.widgets[key]
        for entry in entries:
            if entry.winfo_exists() == 1:
                entry.config(state=NORMAL)

    def new_partition_data(self):
        self.clear_screen()
        self.is_new_data = True
        self.ui_entries["size_spiffs"].set(hex(self.max_spiffs_size))
        self.spiffs_size = self.max_spiffs_size
        self.ui_entries["offset_spiffs"].set(hex(0x9000))
        self.next_offset = 0x9000

    def delete_row(self, index):
        """
        calls destroy() on all the widgets in the given row index and adjusts spiffs size accordingly.
        :param index: row index
        :return: None
        """
        self.widgets["name"][index].destroy()
        del self.ui_entries["name_{}".format(index)]
        self.widgets["type"][index].destroy()
        del self.ui_entries["type_{}".format(index)]
        self.widgets["sub_type"][index].destroy()
        del self.ui_entries["sub_type_{}".format(index)]
        self.widgets["offset"][index].destroy()
        del self.ui_entries["offset_{}".format(index)]
        self.spiffs_size += int(self.ui_entries["size_{}".format(index)].get(), 16)
        self.ui_entries["size_spiffs"].set(hex(self.spiffs_size))
        self.widgets["size"][index].destroy()
        del self.ui_entries["size_{}".format(index)]
        self.widgets["flags"][index].destroy()
        del self.ui_entries["flags_{}".format(index)]
        self.widgets["ar_buttons"][index].destroy()

        del self.ui_map["ui_{}".format(index)]

        # decrement control variables accordingly
        self.last_sub_type -= 0x1
        self.calibrate_ui()
        self.next_offset = self.calibrate_offsets()

    def count_widget_rows(self):
        return len(self.ui_entries)

    def calibrate_ui(self):
        buff = sorted(self.ui_map.iteritems(), key=lambda (k, v): (v, k))

        # grid row start index of partitions.
        scan_index = 2

        for key, value in buff:
            if value != scan_index:
                self.ui_map[key] = scan_index
            scan_index += 1
        for key, value in self.ui_map.iteritems():
            index = int(key[key.rfind("_") + 1:])
            self.widgets["name"][index].grid(row=value, column=1)
            self.widgets["type"][index].grid(row=value, column=2)
            self.widgets["sub_type"][index].grid(row=value, column=3)
            self.widgets["offset"][index].grid(row=value, column=4)
            self.widgets["size"][index].grid(row=value, column=5)
            self.widgets["flags"][index].grid(row=value, column=6)
            if index != self.spiffs_logical_index:
                self.widgets["ar_buttons"][index].grid(row=value, column=0)
            else:
                self.plus_button.grid(row=value, column=0)

        self.last_row = buff[-1][1]

    def calibrate_offsets(self):
        # get all partition indices in group order before calibration.
        # nvs and ota first.
        sorted_indices = [self.get_nvs_index(), self.get_ota_data_index()]

        # app ota data
        sorted_indices += self.get_ota_app_indices()

        # data -- eeprom's
        sorted_indices += self.get_data_indices()

        # don't need spiffs here.

        first_offset = 0x9000
        first_size = 0x5000
        remainder_spiffs_size = self.max_spiffs_size

        sorted_indices = [x for x in sorted_indices if x is not None]

        # calibrate
        if len(sorted_indices) > 0:
            self.ui_entries["offset_{}".format(sorted_indices[0])].set(hex(first_offset))
            self.ui_entries["size_{}".format(sorted_indices[0])].set(hex(first_size))
            next_offset = first_offset + int(self.ui_entries["size_{}".format(sorted_indices[0])].get(), 16)
            remainder_spiffs_size -= int(self.ui_entries["size_{}".format(sorted_indices[0])].get(), 16)

            for i in range(1, len(sorted_indices)):
                self.ui_entries["offset_{}".format(sorted_indices[i])].set(hex(next_offset))
                next_offset += int(self.ui_entries["size_{}".format(sorted_indices[i])].get(), 16)
                remainder_spiffs_size -= int(self.ui_entries["size_{}".format(sorted_indices[i])].get(), 16)

            self.ui_entries["offset_spiffs"].set(hex(next_offset))
            self.spiffs_size = remainder_spiffs_size
            self.ui_entries["size_spiffs"].set(hex(remainder_spiffs_size))

            return next_offset
        return first_offset

    def remove_row(self):
        """
        On clicking "Remove Partition" button
        calls destroy() on all the widgets in the given row index JUST created and adjusts spiffs size accordingly.
        Edit: This is more like and undo button of add partition but with one step back.
        :return: None
        """
        if self.last_logical_index > 5:
            if "name_{}".format(self.last_logical_index) in self.ui_entries:
                self.delete_row(self.last_logical_index)

    def add_row(self, row=None):
        """
        adds a new widget row and shifts the add row button and exports button down by one position
        :return: None
        """

        # increment last_logical_index
        self.last_logical_index += 1

        # vars section start{
        # name section
        self.ui_entries["name_{}".format(self.last_logical_index)] = StringVar()
        if row is None:
            self.ui_entries["name_{}".format(self.last_logical_index)].set(
                "new_partition_{}".format(self.last_logical_index))
        else:
            self.ui_entries["name_{}".format(self.last_logical_index)].set(row[self.template_column_order["name"]])

        # type section
        self.ui_entries["type_{}".format(self.last_logical_index)] = StringVar()
        if row is None:
            self.ui_entries["type_{}".format(self.last_logical_index)].set("data")
        else:
            self.ui_entries["type_{}".format(self.last_logical_index)].set(row[self.template_column_order["type"]])

        # sub type section
        self.ui_entries["sub_type_{}".format(self.last_logical_index)] = StringVar()

        if row is None:
            self.last_sub_type += 0x1
            self.ui_entries["sub_type_{}".format(self.last_logical_index)].set(hex(self.last_sub_type))
        else:
            self.ui_entries["sub_type_{}".format(self.last_logical_index)].set(
                row[self.template_column_order["subtype"]])

        # offset section
        self.ui_entries["offset_{}".format(self.last_logical_index)] = StringVar()
        if row is None:
            self.ui_entries["offset_{}".format(self.last_logical_index)].set(hex(self.next_offset))
            self.next_offset += 0x1000
            self.ui_entries["offset_spiffs"].set(hex(self.next_offset))
        else:
            self.ui_entries["offset_{}".format(self.last_logical_index)].set(row[self.template_column_order["offset"]])

        # size section
        self.ui_entries["size_{}".format(self.last_logical_index)] = StringVar()
        if row is None:
            self.ui_entries["size_{}".format(self.last_logical_index)].set(hex(0x1000))
            self.spiffs_size -= 0x1000
            self.ui_entries["size_spiffs"].set(hex(self.spiffs_size))
        else:
            self.ui_entries["size_{}".format(self.last_logical_index)].set(row[self.template_column_order["size"]])

        # flags section
        self.ui_entries["flags_{}".format(self.last_logical_index)] = StringVar()
        if row is None:
            self.ui_entries["flags_{}".format(self.last_logical_index)].set("          ")
        else:
            self.ui_entries["flags_{}".format(self.last_logical_index)].set(row[self.template_column_order["flags"]])
        # } - vars section end

        # widgets section start {
        # tying widget references to dictionary keys and giving pre set states.
        e = Entry(self, textvariable=self.ui_entries["name_{}".format(self.last_logical_index)])
        e.grid(row=self.last_row + 1, column=1)
        self.widgets["name"].append(e)
        o = OptionMenu(self, self.ui_entries["type_{}".format(self.last_logical_index)], "data", "app")
        o.grid(row=self.last_row + 1, column=2)
        self.widgets["type"].append(o)
        e = Entry(self, textvariable=self.ui_entries["sub_type_{}".format(self.last_logical_index)])
        e.grid(row=self.last_row + 1, column=3)
        if self.sub_type_int_var.get():
            e.config(state=NORMAL)
        else:
            e.config(state=DISABLED)
        self.widgets["sub_type"].append(e)
        e = Entry(self, textvariable=self.ui_entries["offset_{}".format(self.last_logical_index)])
        e.grid(row=self.last_row + 1, column=4)
        if self.offset_int_var.get():
            e.config(state=NORMAL)
        else:
            e.config(state=DISABLED)
        self.widgets["offset"].append(e)
        e = Entry(self, textvariable=self.ui_entries["size_{}".format(self.last_logical_index)])
        e.grid(row=self.last_row + 1, column=5)
        if self.size_int_var.get():
            e.config(state=NORMAL)
        else:
            e.config(state=DISABLED)
        self.widgets["size"].append(e)
        o = OptionMenu(self, self.ui_entries["flags_{}".format(self.last_logical_index)], "          ", "encrypted")
        o.grid(row=self.last_row + 1, column=6)
        self.widgets["flags"].append(o)
        b = Button(self, text="-", command=lambda logical_index=self.last_logical_index: self.delete_row(logical_index))
        b.grid(row=self.last_row + 1, column=0)
        self.widgets["ar_buttons"].append(b)

        self.widgets["name"][self.spiffs_logical_index].grid(row=self.last_row + 2)
        self.widgets["type"][self.spiffs_logical_index].grid(row=self.last_row + 2)
        self.widgets["sub_type"][self.spiffs_logical_index].grid(row=self.last_row + 2)
        self.widgets["offset"][self.spiffs_logical_index].grid(row=self.last_row + 2)
        self.widgets["size"][self.spiffs_logical_index].grid(row=self.last_row + 2)
        self.widgets["flags"][self.spiffs_logical_index].grid(row=self.last_row + 2)
        self.ui_map["ui_{}".format(self.spiffs_logical_index)] = self.last_row + 2

        # Shift buttons down accordingly
        self.plus_button.grid(row=self.last_row + 2)
        self.ui_map["ui_{}".format(self.last_logical_index)] = self.last_row + 1
        self.last_row += 1

    def template_radio_button_state_changed(self):
        if "U_MIN" in self.template_string_var.get():
            template = self.get_template("minimal")
            if template is not None:
                self.reflect_template("minimal", template)
                self.max_spiffs_size = 0x1F7000
        elif "U_DEF" in self.template_string_var.get():
            template = self.get_template("default")
            if template is not None:
                self.reflect_template("default", template)
                self.max_spiffs_size = 0x3F7000

    def reflect_template(self, name, template):
        if isinstance(template, list):
            template = Template(template)
        if template.is_valid:
            self.is_new_data = False
            if len(self.ui_entries) == 0 and len(self.ui_map) == 0:
                # First time of loading template for current instance.
                row_count = template.get_row_count_without_spiffs()
                if row_count != -1:
                    # Buttons && build a logic map to hold important mapping information for all rows.
                    for i in range(template.get_row_count_without_spiffs()):
                        b = Button(self, text="-", command=lambda logical_index=i: self.delete_row(logical_index))
                        self.widgets["ar_buttons"].append(b)
                        b.grid(row=2 + i, column=0)
                        self.ui_map["ui_{}".format(i)] = 2 + i

                    # an un-rendered button for calibration, all widgets relating to spiffs are left out of the widgets
                    # dictionary and referenced as members of the application frame class 'ESPPartitionGUI'.
                    useless_button = Button(self)
                    self.widgets["ar_buttons"].append(useless_button)

                    # this is the index of the last used row without the generate button row included, then +1 to put
                    # widgets on the generate button row and the plus button.
                    bottom_row = 2 + template.get_row_count_without_spiffs()

                    # The last '+' button and others.
                    self.plus_button.grid(row=bottom_row, column=0)

                    for i in range(row_count):
                        self.ui_entries["name_{}".format(i)] = StringVar()
                    for i in range(row_count):
                        self.ui_entries["type_{}".format(i)] = StringVar()
                    for i in range(row_count):
                        self.ui_entries["sub_type_{}".format(i)] = StringVar()
                    for i in range(row_count):
                        self.ui_entries["offset_{}".format(i)] = StringVar()
                    for i in range(row_count):
                        self.ui_entries["size_{}".format(i)] = StringVar()
                    for i in range(row_count):
                        self.ui_entries["flags_{}".format(i)] = StringVar()

                    self.last_logical_index = row_count

                    # spiffs
                    self.ui_entries["name_spiffs"] = StringVar()
                    self.ui_entries["name_spiffs"].set(template.get_spiffs_property("name"))
                    self.ui_entries["type_spiffs"] = StringVar()
                    self.ui_entries["type_spiffs"].set(template.get_spiffs_property("type"))
                    self.ui_entries["flags_spiffs"] = StringVar()
                    self.ui_entries["flags_spiffs"].set("          ")
                    self.ui_entries["sub_type_spiffs"] = StringVar()
                    self.ui_entries["sub_type_spiffs"].set(template.get_spiffs_property("subtype"))
                    self.ui_entries["offset_spiffs"] = StringVar()
                    self.ui_entries["offset_spiffs"].set(template.get_spiffs_property("offset"))
                    self.ui_entries["size_spiffs"] = StringVar()
                    self.ui_entries["size_spiffs"].set(template.get_spiffs_property("size"))
                    self.spiffs_size = int(template.get_spiffs_property("size"), 16)

                    # Names.
                    template.move_to_first()
                    for i in range(row_count):
                        self.ui_entries["name_{}".format(i)].set(template.get_column("name"))
                        template.move_to_next()

                    # Types
                    template.move_to_first()
                    for i in range(row_count):
                        self.ui_entries["type_{}".format(i)].set(template.get_column("type"))
                        template.move_to_next()

                    # Flags
                    template.move_to_first()
                    for i in range(row_count):
                        self.ui_entries["flags_{}".format(i)].set(template.get_column("flags"))
                        template.move_to_next()

                    # Sub Types
                    template.move_to_first()
                    for i in range(row_count):
                        self.ui_entries["sub_type_{}".format(i)].set(template.get_column("subtype"))
                        template.move_to_next()

                    # Offsets
                    template.move_to_first()
                    for i in range(row_count):
                        self.ui_entries["offset_{}".format(i)].set(template.get_column("offset"))
                        template.move_to_next()

                    # Sizes
                    template.move_to_first()
                    for i in range(row_count):
                        self.ui_entries["size_{}".format(i)].set(template.get_column("size"))
                        template.move_to_next()

                    # Entries and Option Menus.
                    # Dictionary keys are used to store reference to the widget objects so as to be able to enable and
                    # disable them.
                    for i in range(row_count):
                        e = Entry(self, textvariable=self.ui_entries["name_{}".format(i)])
                        e.grid(row=2 + i, column=1)
                        self.widgets["name"].append(e)
                        o = OptionMenu(self, self.ui_entries["type_{}".format(i)], "data", "app")
                        o.grid(row=2 + i, column=2)
                        self.widgets["type"].append(o)
                        e = Entry(self, textvariable=self.ui_entries["sub_type_{}".format(i)])
                        e.grid(row=2 + i, column=3)
                        self.widgets["sub_type"].append(e)
                        e = Entry(self, textvariable=self.ui_entries["offset_{}".format(i)])
                        e.grid(row=2 + i, column=4)
                        self.widgets["offset"].append(e)
                        e = Entry(self, textvariable=self.ui_entries["size_{}".format(i)])
                        e.grid(row=2 + i, column=5)
                        self.widgets["size"].append(e)
                        o = OptionMenu(self, self.ui_entries["flags_{}".format(i)], "          ", "encrypted")
                        o.grid(row=2 + i, column=6)
                        self.widgets["flags"].append(o)

                    e = Entry(self, textvariable=self.ui_entries["name_spiffs"])
                    e.grid(row=2 + row_count, column=1)
                    self.widgets["name"].append(e)
                    o = OptionMenu(self, self.ui_entries["type_spiffs"], "data", "app")
                    o.grid(row=2 + row_count, column=2)
                    self.widgets["type"].append(o)
                    e = Entry(self, textvariable=self.ui_entries["sub_type_spiffs"])
                    e.grid(row=2 + row_count, column=3)
                    self.widgets["sub_type"].append(e)
                    e = Entry(self, textvariable=self.ui_entries["offset_spiffs"])
                    e.grid(row=2 + row_count, column=4)
                    self.widgets["offset"].append(e)
                    e = Entry(self, textvariable=self.ui_entries["size_spiffs"])
                    e.grid(row=2 + row_count, column=5)
                    self.widgets["size"].append(e)
                    o = OptionMenu(self, self.ui_entries["flags_spiffs"], "          ", "encrypted")
                    o.grid(row=2 + row_count, column=6)
                    self.widgets["flags"].append(o)

                    self.spiffs_logical_index = len(self.widgets["name"]) - 1
                    self.spiffs_row_index = 2 + row_count
                    self.ui_map["ui_{}".format(self.spiffs_logical_index)] = self.spiffs_row_index

                    # The last know row modified in the grid.
                    self.last_row = bottom_row - 1
                    self.next_offset = template.get_next_offset()

                    self.message_var.set("{} Template Loaded!".format(name))
            else:
                # Has loaded a template before.
                self.clear_screen()
                rows = template.get_rows()
                for row in rows:
                    self.add_row(row)

                self.ui_entries["name_spiffs"].set(template.get_spiffs_property("name"))
                self.ui_entries["type_spiffs"].set(template.get_spiffs_property("type"))
                self.ui_entries["sub_type_spiffs"].set(template.get_spiffs_property("subtype"))
                self.ui_entries["offset_spiffs"].set(template.get_spiffs_property("offset"))
                self.ui_entries["size_spiffs"].set(template.get_spiffs_property("size"))
                self.spiffs_size = int(template.get_spiffs_property("size"), 16)
                self.ui_entries["flags_spiffs"].set("          ")

                self.next_offset = template.get_next_offset()

                self.message_var.set("{} Template Loaded!".format(name))

    def clear_screen(self):
        indices = []
        for key, value in self.ui_entries.iteritems():
            if "name" in key:
                index = key[key.rfind("_") + 1:]
                if index != "spiffs":
                    indices.append(int(index))
        for index in indices:
            self.delete_row(index)

    def get_template(self, name):
        for template in self.templates:
            if name is template["name"]:
                return template["template"]
        return None

    def load_partition_data_from_file(self, file_name=None):
        if file_name is None:
            file_name = askopenfilename(defaultextension=".csv", title="Open CSV File...",
                                        filetypes=(("CSV File", "*.csv"),
                                                   ("All Files", "*.*")))
        if file_name != "":
            if os.path.isfile(file_name):
                with open(file_name, "rb") as csv_file:
                    rows = csv.reader(csv_file, delimiter=",")
                    found_header = False
                    template = Template()
                    for row in rows:
                        if "#" in row[0] and not found_header:
                            column_header = row
                            column_header[0] = column_header[0].replace("#", "")
                            column_header = [x.lower() for x in column_header]
                            column_header = [x.strip() for x in column_header]
                            if not self.match_template_column_order(column_header):
                                if self.set_template_column_order(column_header):
                                    found_header = True
                                    template.add_row(column_header)
                                else:
                                    tkMessageBox.showerror("Loading Error", "Improper CSV Header, Mismatched Length")
                                    break
                            else:
                                found_header = True
                                column_header = [x.strip() for x in column_header]
                                template.add_row(column_header)
                        elif "#" not in row[0]:
                            row = [x.strip() for x in row]
                            template.add_row(row)
                    template.refresh()
                    self.reflect_template("Selected File", template)
                    if "recent" not in self.configs:
                        self.configs["recent"] = []
                    if file_name not in self.configs["recent"]:
                        self.configs["recent"].append(file_name)
                        json.dump(self.configs, open("init.json", "w"))
                    self.currently_open_file = file_name
            else:
                if "recent" in self.configs:
                    if file_name in self.configs["recent"]:
                        tkMessageBox.showinfo("File Non Existent",
                                              "The file {} does not exist anymore.".format(file_name))
                        self.configs["recent"].remove(file_name)
                        json.dump(self.configs, open("init.json", "w"))

    def match_template_column_order(self, columns):
        for key, value in self.template_column_order.iteritems():
            if key != columns[value]:
                return False
        return True

    def set_template_column_order(self, columns):
        if len(columns) == len(self.template_column_order):
            index = 0
            for column in columns:
                self.template_column_order[column] = index
                index += 1
            return True
        return False

    def get_output_dump_path(self):
        return "{}\\hardware\\espressif\\esp32\\tools\\partitions".format(self.configs["esp32_path"])

    def generate(self):
        """
        exports current partition information in the widgets to csv in the esp32 partition dump path of your Arduino
        IDE installation.
        :return: None.
        """
        if "esp32_path" not in self.configs:
            tkMessageBox.showerror("Arduino ESP32 Path", "An Arduino ESP32 path was not set.")
        else:
            if "dump_path" not in self.configs:
                if "generate" not in self.configs:
                    file_name = asksaveasfilename(defaultextension=".csv", title="Save CSV file as...",
                                                  filetypes=(("CSV File", "*.csv"), ("All Files", "*.*")))
                elif self.configs["generate"] != "BOTH":
                    file_name = asksaveasfilename(defaultextension=".{}".format(self.configs["generate"].lower()),
                                                  title="Save {} file as...".format(self.configs["generate"].lower()),
                                                  filetypes=(("{} File".format(self.configs["generate"].lower()),
                                                              "*.{}".format(self.configs["generate"].lower())),
                                                             ("All Files", "*.*")))
                else:
                    file_name = asksaveasfilename(title="Save BIN and CSV file as...")
                if file_name != "":
                    if ".csv" in file_name:
                        self.write_to_csv(file_name)
                        self.message_var.set("CSV File written to {}".format(file_name))
                    elif ".bin" in file_name:
                        csv_file_name = file_name.replace(".bin", ".csv")

                        # First write to csv before converting to binary
                        self.write_to_csv(csv_file_name)

                        # convert to binary
                        if os.system(
                                "python {}\\tools\\gen_esp32part.py --verify {} {}".format(
                                    self.configs["esp32_path"], csv_file_name, file_name)) == 0:
                            self.message_var.set("Binary File written to {}".format(file_name))
                            os.remove(csv_file_name)
                        else:
                            tkMessageBox.showerror("Execution Error", "Error Executing ESP32 Gen Script")
                    else:
                        csv_file_name = file_name + ".csv"
                        file_name += ".bin"

                        # First write to csv before converting to binary
                        self.write_to_csv(csv_file_name)

                        # convert to binary
                        if os.system(
                                "python {}\\tools\\gen_esp32part.py --verify {} {}".format(
                                    self.configs["esp32_path"], csv_file_name, file_name)) == 0:
                            self.message_var.set("Done writing CSV and Binary Files")
                        else:
                            tkMessageBox.showerror("Execution Error", "Error Executing ESP32 Gen Script")
            else:
                if "generate" not in self.configs:
                    file_name = "{}/{}".format(self.configs["dump_path"], "default.csv")
                    self.write_to_csv(file_name)
                    self.message_var.set("CSV File written to {}".format(file_name))
                elif self.configs["generate"] != "BOTH":
                    file_name = "{}/default.{}".format(self.configs["dump_path"], self.configs["generate"].lower())
                    if self.configs["generate"] == "BIN":
                        csv_file_name = file_name.replace(".bin", ".csv")
                        self.write_to_csv(csv_file_name)
                        if os.system(
                                "python {}\\tools\\gen_esp32part.py --verify {} {}".format(
                                    self.configs["esp32_path"], csv_file_name, file_name)) == 0:
                            self.message_var.set("Binary File written to {}".format(file_name))
                            os.remove(csv_file_name)
                        else:
                            tkMessageBox.showerror("Execution Error", "Error Executing ESP32 Gen Script")
                    else:
                        self.write_to_csv(file_name)
                        self.message_var.set("CSV File written to {}".format(file_name))
                else:
                    file_name = "{}/{}".format(self.configs["dump_path"], "default.csv")
                    bin_file_name = file_name.replace(".csv", ".bin")
                    self.write_to_csv(file_name)
                    if os.system(
                            "python {}\\tools\\gen_esp32part.py --verify {} {}".format(
                                self.configs["esp32_path"], file_name, bin_file_name)) == 0:
                        self.message_var.set("Done writing CSV and Binary Files")
                    else:
                        tkMessageBox.showerror("Execution Error", "Error Executing ESP32 Gen Script")

    def convert_csv_to_bin(self):
        """
        convert given csv file from file dialog to binary.
        :return: None.
        """
        if self.configs["esp32_path"] is not None:
            csv_file_name = askopenfilename(defaultextension=".csv", title="Open CSV file as...",
                                            filetypes=(("CSV File", "*.csv"), ("All Files", "*.*")))
            if csv_file_name is not "":
                if ".csv" not in csv_file_name:
                    csv_file_name += ".csv"
                bin_file_name = csv_file_name.replace(".csv", ".bin")

                # convert to bin
                if os.system(
                        "python {}/tools/gen_esp32part.py --verify {} {}".format(
                            self.configs["esp32_path"], csv_file_name, bin_file_name)) == 0:

                    tkMessageBox.showinfo("Done Writing", "Done Writing to Binary File")
                else:
                    tkMessageBox.showerror("Execution Error", "Error Executing ESP32 Gen Script")
        else:
            tkMessageBox.showerror("Arduino ESP32 Root Path", "An Arduino ESP32 root path was not set.")

    def convert_bin_to_csv(self):
        """
        convert given binary file from dialog to csv.
        :return:
        """
        if self.configs["esp32_path"] is not None:
            bin_file_name = askopenfilename(defaultextension=".csv", title="Open Binary file as...",
                                            filetypes=(("Binary File", "*.bin"), ("All Files", "*.*")))
            if bin_file_name is not "":
                if ".bin" not in bin_file_name:
                    bin_file_name += ".bin"
                csv_file_name = bin_file_name.replace(".bin", ".csv")

                # convert to csv
                if os.system(
                        "python {}/tools/gen_esp32part.py --verify {} {}".format(
                            self.configs["esp32_path"], bin_file_name, csv_file_name)) == 0:

                    tkMessageBox.showinfo("Done Writing", "Done Writing to CSV File")
                else:
                    tkMessageBox.showerror("Execution Error", "Error Executing ESP32 Gen Script")
        else:
            tkMessageBox.showerror("Arduino ESP32 Root Path", "An Arduino ESP32 root path was not set.")

    def write_to_csv(self, output_file_name):
        """
        takes in the current input values of the widgets on screen, forms a csv partition table and saves it with the
        given file name.
        :param output_file_name: file name of output csv file (absolute).
        :return: None
        """
        with open(output_file_name, "wb") as csv_file:
            csv_writer = csv.writer(csv_file, delimiter=",", quoting=csv.QUOTE_MINIMAL)
            csv_writer.writerow(["# Name", "Type", "SubType", "Offset", "Size", "Flags"])

            # nvs
            nvs_index = self.get_nvs_index()
            csv_writer.writerow(
                [self.ui_entries["name_{}".format(nvs_index)].get(),
                 self.ui_entries["type_{}".format(nvs_index)].get(),
                 self.ui_entries["sub_type_{}".format(nvs_index)].get(),
                 self.ui_entries["offset_{}".format(nvs_index)].get(),
                 self.ui_entries["size_{}".format(nvs_index)].get(),
                 self.ui_entries["flags_{}".format(nvs_index)].get().replace("          ", "")])

            # ota
            ota_data_index = self.get_ota_data_index()
            csv_writer.writerow(
                [self.ui_entries["name_{}".format(ota_data_index)].get(),
                 self.ui_entries["type_{}".format(ota_data_index)].get(),
                 self.ui_entries["sub_type_{}".format(ota_data_index)].get(),
                 self.ui_entries["offset_{}".format(ota_data_index)].get(),
                 self.ui_entries["size_{}".format(ota_data_index)].get(),
                 self.ui_entries["flags_{}".format(ota_data_index)].get().replace("          ", "")])

            # app ota data
            app_ota_indices = self.get_ota_app_indices()
            for i in app_ota_indices:
                csv_writer.writerow(
                    [self.ui_entries["name_{}".format(i)].get(),
                     self.ui_entries["type_{}".format(i)].get(),
                     self.ui_entries["sub_type_{}".format(i)].get(),
                     self.ui_entries["offset_{}".format(i)].get(),
                     self.ui_entries["size_{}".format(i)].get(),
                     self.ui_entries["flags_{}".format(i)].get().replace("          ", "")])

            # data -- eeprom's
            data_indices = self.get_data_indices()
            for i in data_indices:
                csv_writer.writerow(
                    [self.ui_entries["name_{}".format(i)].get(),
                     self.ui_entries["type_{}".format(i)].get(),
                     self.ui_entries["sub_type_{}".format(i)].get(),
                     self.ui_entries["offset_{}".format(i)].get(),
                     self.ui_entries["size_{}".format(i)].get(),
                     self.ui_entries["flags_{}".format(i)].get().replace("          ", "")])

            # spiffs
            csv_writer.writerow(
                [self.ui_entries["name_spiffs"].get(),
                 self.ui_entries["type_spiffs"].get(),
                 self.ui_entries["sub_type_spiffs"].get(),
                 self.ui_entries["offset_spiffs"].get(),
                 self.ui_entries["size_spiffs"].get(),
                 self.ui_entries["flags_spiffs"].get().replace("          ", "")])

    def get_nvs_index(self):
        """
        gets the only nvs subtype widget val index.
        :return: (int) nvs subtype widget val index
        """
        for k, v in self.ui_entries.iteritems():
            if "sub_type" in k and "nvs" in v.get():
                return k[k.rfind("_") + 1:]

    def get_ota_data_index(self):
        """
        gets the only ota data subtype widget val index.
        :return: (int) ota data subtype widget val index.
        """
        for k, v in self.ui_entries.iteritems():
            if "type" in k and "data" in v.get():
                row_index = k[k.rfind("_") + 1:]
                if "ota" in self.ui_entries["sub_type_{}".format(row_index)].get():
                    return row_index

    def get_ota_app_indices(self):
        """
        gets ota app type widget val indices.
        :return: (list) ota app type indices.
        """
        indices = []
        for k, v in self.ui_entries.iteritems():
            if "type" in k and "app" in v.get():
                indices.append(k[k.rfind("_") + 1:])
        sub_types = {}
        for i in indices:
            sub_types["a_{}".format(i)] = self.ui_entries["sub_type_{}".format(i)].get()

        # sort
        sub_types = sorted(sub_types.iteritems(), key=lambda (ak, av): (av, ak))

        # extract proper indices.
        for i in range(len(indices)):
            k, v = sub_types[i]
            indices[i] = k[2:]
        return indices

    def get_data_indices(self):
        """
        gets data type widget val indices.
        :return: (list) data type indices.
        """
        indices = []
        for k, v in self.ui_entries.iteritems():
            if "type" in k and "data" in v.get():
                row_index = k[k.rfind("_") + 1:]
                if "spiffs" not in self.ui_entries["sub_type_{}".format(row_index)].get() and "ota" not in \
                        self.ui_entries["sub_type_{}".format(row_index)].get() and "nvs" not in self.ui_entries[
                    "sub_type_{}".format(row_index)].get():
                    indices.append(row_index)
        sub_types = {}
        for i in indices:
            sub_types["a_{}".format(i)] = self.ui_entries["sub_type_{}".format(i)].get()

        # sort
        sub_types = sorted(sub_types.iteritems(), key=lambda (ak, av): (av, ak))

        # extract proper indices
        for i in range(len(indices)):
            k, v = sub_types[i]
            indices[i] = k[2:]
        return indices

    def get_spiffs_index(self):
        """
        gets the spiffs widget val index.
        :return: (int) the spiffs widget val index.
        """
        for k, v in self.ui_entries.iteritems():
            if "sub_type" in k and "spiffs" in v.get():
                return k[k.rfind("_") + 1:]

    def frame_quit(self):
        """
        quits the application.
        :return: None.
        """
        if askokcancel("Quit", "Do you really wish to quit?"):
            Frame.quit(self)

    @staticmethod
    def help():
        webbrowser.open_new("https://github.com/francis94c/esp-partition-gui#readme")

    def close_about_window(self):
        self.is_about_open = False
        self.about_window.destroy()

    def about(self):
        if not self.is_about_open:
            self.is_about_open = True
            self.about_window = Toplevel()
            self.about_window.maxsize(width=250, height=250)
            self.about_window.protocol("WM_DELETE_WINDOW", self.close_about_window)

            about = "ESP32 Partition GUI / ESP32 Partition Manager\nv0.0.4"

            Label(self.about_window, text=about, wraplength=250).pack(side=LEFT and TOP)
            Button(self.about_window, text="Ok", command=self.close_about_window).pack(side=TOP)


if __name__ == "__main__":
    top = Tk()
    top.title("ESP Partition GUI")
    init_file = None

    # load init file.
    if os.path.isfile("init.json"):
        init_file = json.load(open("init.json"))

    # some partitioning templates
    partition_templates = [
        {
            "name": "default",
            "template":
                [
                    ["Name", "Type", "SubType", "Offset", "Size", "Flags"],
                    ["nvs", "data", "nvs", "0x9000", "0x5000", "          "],
                    ["otadata", "data", "ota", "0xe000", "0x2000", "          "],
                    ["app0", "app", "ota_0", "0x10000", "0x140000", "          "],
                    ["app1", "app", "ota_1", "0x150000", "0x140000", "          "],
                    ["eeprom", "data", "0x99", "0x290000", "0x1000", "          "],
                    ["spiffs", "data", "spiffs", "0x291000", "0x16F000", "          "]
                ]
        },
        {
            "name": "minimal",
            "template":
                [
                    ["Name", "Type", "SubType", "Offset", "Size", "Flags"],
                    ["nvs", "data", "nvs", "0x9000", "0x5000", "          "],
                    ["otadata", "data", "ota", "0xe000", "0x2000", "          "],
                    ["app0", "app", "ota_0", "0x10000", "0x140000", "          "],
                    ["eeprom", "data", "0x99", "0x150000", "0x1000", "          "],
                    ["spiffs", "data", "spiffs", "0x151000", "0xAF000", "          "]
                ]
        }
    ]

    ESPPartitionGUI(top, init_file, partition_templates).mainloop()
