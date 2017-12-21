from Tkinter import *


class ESPPartitionGUI(Frame):
    def __init__(self, master=None):
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
                                           command=self.toggle_sub_type).grid(row=0, column=4)
        self.size_checkbox = Checkbutton(self, text="Enable", variable=self.size_int_var,
                                         command=self.toggle_sub_type).grid(row=0, column=5)
        self.flags_checkbox = Checkbutton(self, text="Enable", variable=self.flags_int_var,
                                          command=self.toggle_sub_type).grid(row=0, column=6)
        
        self.widgets = {"name": [], "ar_buttons": {}}  # Variable to hold references to widgets on screen.
        for i in range(6):
            b = Button(self, text="-")
            b.grid(row=2 + i, column=0)
            self.widgets["ar_buttons"]["button_{}".format(i)] = b
        b = Button(self, text="+")
        b.grid(row=8, column=0)
        self.last_row = 8
        Label(self, text="Name").grid(row=1, column=2)
        Label(self, text="Type").grid(row=1, column=3)
        Label(self, text="SubType").grid(row=1, column=4)
        Label(self, text="Offset").grid(row=1, column=5)
        Label(self, text="Size").grid(row=1, column=6)
        Label(self, text="Flags").grid(row=1, column=7)
        self.ui_entries = {"name_0": StringVar(), "name_1": StringVar(), "name_2": StringVar(), "name_3": StringVar(),
                           "name_4": StringVar(), "name_5": StringVar()}
        for i in range(6):
            e = Entry(self, textvariable=self.ui_entries["name_{}".format(i)])
            e.grid(row=2 + i, column=2)
            self.widgets["name"].append(e)
        self.ui_entries["name_0"].set("nvs")
        self.ui_entries["name_1"].set("otadata")
        self.ui_entries["name_2"].set("app0")
        self.ui_entries["name_3"].set("app1")
        self.ui_entries["name_4"].set("eeprom")
        self.ui_entries["name_5"].set("spiffs")

    def toggle_sub_type(self):
        enable = self.sub_type_int_var.get()
        entries = self.widgets["name"]
        for entry in entries:
            if enable:
                entry.config(state=NORMAL)
            else:
                entry.config(state=DISABLED)


if __name__ == "__main__":
    top = Tk()
    top.title("ESP Partition GUI")
    ESPPartitionGUI(top).mainloop()
