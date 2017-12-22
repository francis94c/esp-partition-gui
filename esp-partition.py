from Tkinter import *


class ESPPartitionGUI(Frame):
    def __init__(self, master=None, ):
        """
        Initialization of the Main GUI Form
        The Widgets are loaded and arranged here with the default ESP partition template.
        :param master: a Tk top level object obtained by calling Tk().
        """
        Frame.__init__(self, master)

        self.pack(fill=BOTH, side=TOP, expand=True)

        # Configure all columns to be of layout weight 1.
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)
        self.grid_columnconfigure(2, weight=1)
        self.grid_columnconfigure(3, weight=1)
        self.grid_columnconfigure(4, weight=1)
        self.grid_columnconfigure(5, weight=1)

        # IntVars to track checkboxes states
        self.sub_type_int_var = IntVar()
        self.offset_int_var = IntVar()
        self.size_int_var = IntVar()
        self.flags_int_var = IntVar()

        # Declare and add Checkboxes
        self.sub_type_checkbox = Checkbutton(self, text="Enable", variable=self.sub_type_int_var,
                                             command=self.toggle_sub_type).grid(row=0, column=3)
        self.offset_checkbox = Checkbutton(self, text="Enable", variable=self.offset_int_var,
                                           command=self.toggle_offset).grid(row=0, column=4)
        self.size_checkbox = Checkbutton(self, text="Enable", variable=self.size_int_var,
                                         command=self.toggle_size).grid(row=0, column=5)
        self.flags_checkbox = Checkbutton(self, text="Enable", variable=self.flags_int_var).grid(row=0, column=6)

        # Variable to hold references to widgets on screen.
        self.widgets = {"name": [], "type": [], "sub_type": [], "ar_buttons": [], "offset": [], "size": []}

        # Add buttons to screen.
        for i in range(6):
            b = Button(self, text="-", command=lambda index=i: self.delete_row(index))
            b.grid(row=2 + i, column=0)
            self.widgets["ar_buttons"].append(b)

        # The last '+' button.
        self.plus_button = Button(self, text="+", command=self.add_row)
        self.plus_button.grid(row=8, column=0)

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

        # Control variable for detecting the last logical input row index
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
        self.ui_entries["size_5"].set("0x169000")

        # Entries and Option Menus.
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

        # Set by default disabled widgets.
        self.disable_widgets("sub_type")
        self.disable_widgets("offset")
        self.disable_widgets("size")

    def toggle_sub_type(self):
        """
        Toggles widget states of the Entry widgets int he sub type column.
        :return: None
        """
        enable = self.sub_type_int_var.get()
        if enable:
            self.enable_widgets("sub_type")
        else:
            self.disable_widgets("sub_type")

    def toggle_offset(self):
        """
        Toggles widget states of the Entry widgets int he offset column.
        :return:
        """
        enable = self.offset_int_var.get()
        if enable:
            self.enable_widgets("offset")
        else:
            self.disable_widgets("offset")

    def toggle_size(self):
        enable = self.size_int_var.get()
        if enable:
            self.enable_widgets("size")
        else:
            self.disable_widgets("size")

    def disable_widgets(self, key):
        entries = self.widgets[key]
        for entry in entries:
            entry.config(state=DISABLED)

    def enable_widgets(self, key):
        entries = self.widgets[key]
        for entry in entries:
            entry.config(state=NORMAL)

    def delete_row(self, index):
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
        self.widgets["ar_buttons"][index].destroy()

    def add_row(self):
        self.last_logical_index += 1
        self.ui_entries["name_{}".format(self.last_logical_index)] = StringVar()
        self.ui_entries["type_{}".format(self.last_logical_index)] = StringVar()
        self.ui_entries["sub_type_{}".format(self.last_logical_index)] = StringVar()
        self.ui_entries["offset_{}".format(self.last_logical_index)] = StringVar()
        self.ui_entries["size_{}".format(self.last_logical_index)] = StringVar()
        e = Entry(self, textvariable=self.ui_entries["name_{}".format(self.last_logical_index)])
        e.grid(row=self.last_row + 1, column=1)
        self.widgets["name"].append(e)
        o = OptionMenu(self, self.ui_entries["type_{}".format(self.last_logical_index)], "data", "app")
        o.grid(row=self.last_row + 1, column=2)
        self.widgets["type"].append(o)
        e = Entry(self, textvariable=self.ui_entries["sub_type_{}".format(self.last_logical_index)])
        e.grid(row=self.last_row + 1, column=3)
        self.widgets["sub_type"].append(e)
        e = Entry(self, textvariable=self.ui_entries["offset_{}".format(self.last_logical_index)])
        e.grid(row=self.last_row + 1, column=4)
        self.widgets["offset"].append(e)
        e = Entry(self, textvariable=self.ui_entries["size_{}".format(self.last_logical_index)])
        e.grid(row=self.last_row + 1, column=5)
        self.widgets["size"].append(e)
        # 'index=self.last_row: self.delete_row(index)' because this value will be incremented a the end of this
        # function.
        b = Button(self, text="-", command=lambda index=self.last_logical_index: self.delete_row(index))
        b.grid(row=self.last_row + 1, column=0)
        self.widgets["ar_buttons"].append(b)
        self.plus_button.grid(row=self.last_row + 2, column=0)
        self.last_row += 1


if __name__ == "__main__":
    top = Tk()
    top.title("ESP Partition GUI")
    ESPPartitionGUI(top).mainloop()
