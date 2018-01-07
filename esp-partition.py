from Tkinter import *
import tkMessageBox
from tkFileDialog import asksaveasfilename, askdirectory, askopenfilename
from tkMessageBox import askokcancel
import csv
import os
import json


class ESPPartitionGUI(Frame):
    def __init__(self, master=None, configs=None):
        """
        Initialization of the Main GUI Form
        The Widgets are loaded and arranged here with the default ESP partition template.
        :param master: a Tk top level object obtained by calling Tk().
        """
        Frame.__init__(self, master)

        if configs is None:
            self.configs = {}
        else:
            self.configs = configs

        self.pack(fill=BOTH, side=TOP, expand=True)

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
        self.next_offset = 0x291000
        self.spiffs_size = 0x16F000

        # Declare and add Checkboxes
        self.sub_type_checkbox = Checkbutton(self, text="Enable", variable=self.sub_type_int_var,
                                             command=self.toggle_sub_type).grid(row=0, column=3)
        self.offset_checkbox = Checkbutton(self, text="Enable", variable=self.offset_int_var,
                                           command=self.toggle_offset).grid(row=0, column=4)
        self.size_checkbox = Checkbutton(self, text="Enable", variable=self.size_int_var,
                                         command=self.toggle_size).grid(row=0, column=5)
        self.flags_checkbox = Checkbutton(self, text="Enable", variable=self.flags_int_var,
                                         command=self.toggle_flags).grid(row=0, column=6)

        # Variable to hold references to widgets on screen.
        self.widgets = {"name": [], "type": [], "sub_type": [], "ar_buttons": [], "offset": [], "size": [], "flags": []}

        # Add buttons to screen.
        for i in range(6):
            b = Button(self, text="-", command=lambda index=i: self.delete_row(index))
            self.widgets["ar_buttons"].append(b)
            if i != 5:
                b.grid(row=2 + i, column=0)

        # The last '+' button.
        self.plus_button = Button(self, text="+", command=self.add_row)
        self.plus_button.grid(row=8, column=0)
        self.export_to_binary_button = Button(self, text="Export to Binary", command=self.export_to_bin)
        self.export_to_binary_button.grid(row=8, column=6)
        self.export_to_csv_button = Button(self, text="Export to CSV", command=self.export_to_csv)
        self.export_to_csv_button.grid(row=8, column=5)

        # The last know row modified in the grid.
        self.last_row = 7
        self.row_treshold = 7
        self.forgotten_logical_indices = []

        # Labels
        Label(self, text="Name").grid(row=1, column=1)
        Label(self, text="Type").grid(row=1, column=2)
        Label(self, text="SubType").grid(row=1, column=3)
        Label(self, text="Offset").grid(row=1, column=4)
        Label(self, text="Size").grid(row=1, column=5)
        Label(self, text="Flags").grid(row=1, column=6)

        # Variable for references to inputs on the screen.
        self.ui_entries = {}
        for i in range(6):
            self.ui_entries["name_{}".format(i)] = StringVar()
        for i in range(6):
            self.ui_entries["type_{}".format(i)] = StringVar()
        for i in range(6):
            self.ui_entries["sub_type_{}".format(i)] = StringVar()
        for i in range(6):
            self.ui_entries["offset_{}".format(i)] = StringVar()
        for i in range(6):
            self.ui_entries["size_{}".format(i)] = StringVar()
        for i in range(6):
            self.ui_entries["flags_{}".format(i)] = StringVar()

        # Set Default Option Items.
        self.ui_entries["name_0"].set("nvs")
        self.ui_entries["name_1"].set("otadata")
        self.ui_entries["name_2"].set("app0")
        self.ui_entries["name_3"].set("app1")
        self.ui_entries["name_4"].set("eeprom")
        self.ui_entries["name_5"].set("spiffs")

        self.ui_entries["type_0"].set("data")
        self.ui_entries["type_1"].set("data")
        self.ui_entries["type_2"].set("app")
        self.ui_entries["type_3"].set("app")
        self.ui_entries["type_4"].set("data")
        self.ui_entries["type_5"].set("data")

        self.ui_entries["flags_0"].set("          ")
        self.ui_entries["flags_1"].set("          ")
        self.ui_entries["flags_2"].set("          ")
        self.ui_entries["flags_3"].set("          ")
        self.ui_entries["flags_4"].set("          ")
        self.ui_entries["flags_5"].set("          ")

        # Control variable for detecting the last logical input row index of widgets regardless of grid row.
        self.last_logical_index = 5

        # Default Entry Items
        self.ui_entries["sub_type_0"].set("nvs")
        self.ui_entries["sub_type_1"].set("ota")
        self.ui_entries["sub_type_2"].set("ota_0")
        self.ui_entries["sub_type_3"].set("ota_1")
        self.ui_entries["sub_type_4"].set("0x99")
        self.ui_entries["sub_type_5"].set("spiffs")

        self.ui_entries["offset_0"].set("0x9000")
        self.ui_entries["offset_1"].set("0xe000")
        self.ui_entries["offset_2"].set("0x10000")
        self.ui_entries["offset_3"].set("0x150000")
        self.ui_entries["offset_4"].set("0x290000")
        self.ui_entries["offset_5"].set("0x291000")

        self.ui_entries["size_0"].set("0x5000")
        self.ui_entries["size_1"].set("0x2000")
        self.ui_entries["size_2"].set("0x140000")
        self.ui_entries["size_3"].set("0x140000")
        self.ui_entries["size_4"].set("0x1000")
        self.ui_entries["size_5"].set("0x16F000")

        # Entries and Option Menus.
        # Dictionary keys are used to store reference to the widget objects so as to be able to enable and disable them.
        for i in range(6):
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
        self.menu_bar.add_cascade(label="File", menu=self.file_menu)
        if "arduino_path" in self.configs:
            self.file_menu.add_command(label="Set Arduino Directory [{}]".format(self.configs["arduino_path"]),
                                       command=self.choose_arduino_directory)
        else:
            self.file_menu.add_command(label="Set Arduino Directory", command=self.choose_arduino_directory)
        self.file_menu.add_command(label="Show Current Arduino Directory", command=self.show_current_arduino_directory)
        self.file_menu.add_command(label="Convert CSV to Binary", command=self.convert_csv_to_bin)
        self.file_menu.add_command(label="Convert Binary to CSV", command=self.convert_bin_to_csv)
        self.file_menu.add_command(label="Quit", command=self.frame_quit)

    def show_current_arduino_directory(self):
        """
        Shows a popup window with the current set arduino ide root path.
        :return: None
        """
        if self.configs is not None:
            if 'arduino_path' in self.configs:
                tkMessageBox.showinfo("Current Arduino Directory", self.configs["arduino_path"])
            else:
                tkMessageBox.showwarning("Current Arduino Directory", "No Arduino Directory Set.")
        else:
            tkMessageBox.showwarning("Current Arduino Directory", "No Arduino Directory Set.")

    def choose_arduino_directory(self):
        """
        Opens a directory chooser dialog to select the root path of an arduino ide installation. On selection, this
        function will check for the gen_esp32_part.py sript in the expected folder before it can marj the selected
        folder as valid.
        :return: None
        """
        folder_string = askdirectory()
        if os.path.isfile(folder_string + "/hardware/espressif/esp32/tools/gen_esp32part.py"):
            self.configs["arduino_path"] = folder_string
            json.dump(self.configs, open("init.json", "w"))
            tkMessageBox.showinfo("Success", "Arduino IDE root path was successfully set.")
        else:
            tkMessageBox.showerror("ESP Gen Script Error", "The Espressif ESP32 Gen Script was not found.")

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
        Toggles widget states of the Entry widgets int the size column.
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
        disables all widgets with the given key fom the self.widgets dictionary.
        :param key: key name of widget group.
        :return: None.
        """
        entries = self.widgets[key]
        for entry in entries:
            if entry.winfo_exists() == 1:
                entry.config(state=NORMAL)

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
        self.widgets["size"][index].destroy()
        del self.ui_entries["size_{}".format(index)]
        self.widgets["flags"][index].destroy()
        del self.ui_entries["flags_{}".format(index)]
        self.widgets["ar_buttons"][index].destroy()
        self.spiffs_size += 0x1000
        self.ui_entries["size_5"].set(hex(self.spiffs_size))
        # decrement control variables accordingly
        self.last_sub_type -= 0x1
        self.next_offset = self.next_offset - 0x1000

    def add_row(self):
        """
        adds a new widget row and shifts the add row button and exports button down by one position
        :return: None
        """

        # increment last_logical_index
        self.last_logical_index += 1

        # vars section start{
        # name section
        self.ui_entries["name_{}".format(self.last_logical_index)] = StringVar()
        self.ui_entries["name_{}".format(self.last_logical_index)].set(
            "new_partition_{}".format(self.last_logical_index))

        # type section
        self.ui_entries["type_{}".format(self.last_logical_index)] = StringVar()
        self.ui_entries["type_{}".format(self.last_logical_index)].set("data")

        # sub type section
        self.ui_entries["sub_type_{}".format(self.last_logical_index)] = StringVar()
        self.last_sub_type += 0x1
        self.ui_entries["sub_type_{}".format(self.last_logical_index)].set(hex(self.last_sub_type))

        # offset section
        self.ui_entries["offset_{}".format(self.last_logical_index)] = StringVar()
        self.ui_entries["offset_{}".format(self.last_logical_index)].set(hex(self.next_offset))
        self.next_offset += 0x1000

        # size section
        self.ui_entries["size_{}".format(self.last_logical_index)] = StringVar()
        self.ui_entries["size_{}".format(self.last_logical_index)].set(hex(0x1000))
        self.spiffs_size -= 0x1000
        self.ui_entries["size_5"].set(hex(self.spiffs_size))

        # type section
        self.ui_entries["flags_{}".format(self.last_logical_index)] = StringVar()
        self.ui_entries["flags_{}".format(self.last_logical_index)].set("          ")
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
        b = Button(self, text="-", command=lambda index=self.last_logical_index: self.delete_row(index))
        b.grid(row=self.last_row + 1, column=0)
        self.widgets["ar_buttons"].append(b)

        # Shift buttons down by one grid row
        self.plus_button.grid(row=self.last_row + 2)
        self.export_to_csv_button.grid(row=self.last_row + 2)
        self.export_to_binary_button.grid(row=self.last_row + 2)
        self.last_row += 1

    def export_to_bin(self):
        """
        exports current partition information in the widgets to binary.
        :return: None
        """
        if self.configs["arduino_path"] is None:
            tkMessageBox.showerror("Arduino IDE Root Path", "An Arduino IDE root path was not set.")
        else:
            bin_file_name = asksaveasfilename(defaultextension=".bin", title="Save bin file as...",
                                              filetypes=(("Binary File", "*.bin"), ("All Files", "*.*")))
            if bin_file_name.endswith(".bin"):
                csv_file_name = bin_file_name.replace(".bin", ".csv")
            else:
                bin_file_name += ".bin"
                csv_file_name = bin_file_name.replace(".bin", ".csv")

            # First write to csv before converting to binary
            self.write_to_csv(csv_file_name)

            # convert to binary
            if os.system(
                    "python {}\\hardware\\espressif\\esp32\\tools\\gen_esp32part.py --verify {} {}".format(
                        self.configs["arduino_path"], csv_file_name, bin_file_name)) == 0:
                tkMessageBox.showinfo("Done Writing", "Done Writing to Binary File")
            else:
                tkMessageBox.showerror("Execution Error", "Error Executing ESP32 Gen Script")

    def export_to_csv(self):
        """
        exports current partition information in the widgets to csv.
        :return:
        """
        file_name = asksaveasfilename(defaultextension=".csv", title="Save CSV file as...",
                                      filetypes=(("CSV File", "*.csv"), ("All Files", "*.*")))
        if file_name is not None:
            self.write_to_csv(file_name)
            tkMessageBox.showinfo("Done Writing", "Done Writing to CSV")

    def convert_csv_to_bin(self):
        """
        convert given csv file from file dialog to binary.
        :return: None.
        """
        if self.configs["arduino_path"] is not None:
            csv_file_name = askopenfilename(defaultextension=".csv", title="Open CSV file as...",
                                            filetypes=(("CSV File", "*.csv"), ("All Files", "*.*")))
            if csv_file_name is not "":
                if ".csv" not in csv_file_name:
                    csv_file_name += ".csv"
                bin_file_name = csv_file_name.replace(".csv", ".bin")

                # convert to bin
                if os.system(
                        "python {}\\hardware\\espressif\\esp32\\tools\\gen_esp32part.py --verify {} {}".format(
                            self.configs["arduino_path"], csv_file_name, bin_file_name)) == 0:

                    tkMessageBox.showinfo("Done Writing", "Done Writing to Binary File")
                else:
                    tkMessageBox.showerror("Execution Error", "Error Executing ESP32 Gen Script")
        else:
            tkMessageBox.showerror("Arduino IDE Root Path", "An Arduino IDE root path was not set.")

    def convert_bin_to_csv(self):
        """
        convert given binary file from dialog to csv.
        :return:
        """
        if self.configs["arduino_path"] is not None:
            bin_file_name = askopenfilename(defaultextension=".csv", title="Open Binary file as...",
                                            filetypes=(("Binary File", "*.bin"), ("All Files", "*.*")))
            if bin_file_name is not "":
                if ".bin" not in bin_file_name:
                    bin_file_name += ".bin"
                csv_file_name = bin_file_name.replace(".bin", ".csv")

                # convert to csv
                if os.system(
                        "python {}\\hardware\\espressif\\esp32\\tools\\gen_esp32part.py --verify {} {}".format(
                            self.configs["arduino_path"], bin_file_name, csv_file_name)) == 0:

                    tkMessageBox.showinfo("Done Writing", "Done Writing to CSV File")
                else:
                    tkMessageBox.showerror("Execution Error", "Error Executing ESP32 Gen Script")
        else:
            tkMessageBox.showerror("Arduino IDE Root Path", "An Arduino IDE root path was not set.")

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
                 self.ui_entries["flags_{}".format(nvs_index)].get(), ""])

            # ota
            ota_data_index = self.get_ota_data_index()
            csv_writer.writerow(
                [self.ui_entries["name_{}".format(ota_data_index)].get(),
                 self.ui_entries["type_{}".format(ota_data_index)].get(),
                 self.ui_entries["sub_type_{}".format(ota_data_index)].get(),
                 self.ui_entries["offset_{}".format(ota_data_index)].get(),
                 self.ui_entries["size_{}".format(ota_data_index)].get(),
                 self.ui_entries["flags_{}".format(ota_data_index)].get(), ""])

            # app ota data
            app_ota_indices = self.get_ota_app_indices()
            for i in app_ota_indices:
                csv_writer.writerow(
                    [self.ui_entries["name_{}".format(i)].get(),
                     self.ui_entries["type_{}".format(i)].get(),
                     self.ui_entries["sub_type_{}".format(i)].get(),
                     self.ui_entries["offset_{}".format(i)].get(),
                     self.ui_entries["size_{}".format(i)].get(),
                     self.ui_entries["flags_{}".format(i)].get(), ""])

            # data -- eeprom's
            data_indices = self.get_data_indices()
            for i in data_indices:
                csv_writer.writerow(
                    [self.ui_entries["name_{}".format(i)].get(),
                     self.ui_entries["type_{}".format(i)].get(),
                     self.ui_entries["sub_type_{}".format(i)].get(),
                     self.ui_entries["offset_{}".format(i)].get(),
                     self.ui_entries["size_{}".format(i)].get(),
                     self.ui_entries["flags_{}".format(i)].get(), ""])

            # spiffs
            spiffs_index = self.get_spiffs_index()
            csv_writer.writerow(
                [self.ui_entries["name_{}".format(spiffs_index)].get(),
                 self.ui_entries["type_{}".format(spiffs_index)].get(),
                 self.ui_entries["sub_type_{}".format(spiffs_index)].get(),
                 self.ui_entries["offset_{}".format(spiffs_index)].get(),
                 self.ui_entries["size_{}".format(spiffs_index)].get(),
                 self.ui_entries["flags_{}".format(spiffs_index)].get(), ""])

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


if __name__ == "__main__":
    top = Tk()
    top.title("ESP Partition GUI")
    init_file = None

    # load init file.
    if os.path.isfile("init.json"):
        init_file = json.load(open("init.json"))

    ESPPartitionGUI(top, init_file).mainloop()
