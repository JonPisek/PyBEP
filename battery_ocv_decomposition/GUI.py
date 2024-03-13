import tkinter as tk
from tkinter import Label, Entry, filedialog, IntVar, Checkbutton, Scale
from optimization_functions import perform_full_optimization_parallel
from add_curves import add_half_cell_data
from add_battery import load_soc_ocv_data

class OCVBatteryDecompositionGUI:
    def __init__(self, master):
        self.master = master
        master.title("OCV Battery Decomposition")

        # Set the initial window size
        master.geometry("500x400")

        # Create input file locations with default values
        self.default_cathode_loc = "battery_ocv_decomposition/cathode_data"
        self.default_anode_loc = "battery_ocv_decomposition/anode_data"
        self.default_battery_loc = "battery_ocv_decomposition/battery_data.txt"

        self.cathode_loc = self.default_cathode_loc
        self.anode_loc = self.default_anode_loc
        self.battery_loc = self.default_battery_loc

        # Load data
        self.interpolated_cathodes = add_half_cell_data(self.cathode_loc)
        self.interpolated_anodes = add_half_cell_data(self.anode_loc)
        self.SOC_battery = None
        self.OCV_battery = None

        # Create GUI elements
        self.create_file_location_entries()
        self.create_input_widgets()

        self.run_button = tk.Button(master, text="Run Optimization", command=self.run_optimization, width=20)
        self.run_button.pack(pady=10)

    def create_file_location_entries(self):
        self.label_cathode_loc = Label(self.master, text="Cathode File Location:")
        self.label_cathode_loc.pack()

        self.entry_cathode_loc = Entry(self.master, width=50)
        self.entry_cathode_loc.insert(0, self.default_cathode_loc)  # Set default value
        self.entry_cathode_loc.pack()

        self.label_anode_loc = Label(self.master, text="Anode File Location:")
        self.label_anode_loc.pack()

        self.entry_anode_loc = Entry(self.master, width=50)
        self.entry_anode_loc.insert(0, self.default_anode_loc)  # Set default value
        self.entry_anode_loc.pack()

        self.label_battery_loc = Label(self.master, text="Battery File Location:")
        self.label_battery_loc.pack()

        self.entry_battery_loc = Entry(self.master, width=50)
        self.entry_battery_loc.insert(0, self.default_battery_loc)  # Set default value
        self.entry_battery_loc.pack()

        self.browse_button = tk.Button(self.master, text="Browse", command=self.browse_files)
        self.browse_button.pack()

    def create_input_widgets(self):
        self.label_iterations = Label(self.master, text="Iterations:")
        self.label_iterations.pack()

        self.iterations_var = IntVar()
        self.scale_iterations = Scale(self.master, from_=1, to=5, orient=tk.HORIZONTAL, variable=self.iterations_var, length=200)
        self.scale_iterations.set(5)  # Set default value
        self.scale_iterations.pack()

        self.label_binary_params = Label(self.master, text="Binary Parameters:")
        self.label_binary_params.pack()

        self.battery_var = IntVar()
        self.check_battery = Checkbutton(self.master, text="Battery", variable=self.battery_var)
        self.check_battery.pack()

        self.anode_var = IntVar()
        self.check_anode = Checkbutton(self.master, text="Anode", variable=self.anode_var)
        self.check_anode.pack()

        self.cathode_var = IntVar()
        self.check_cathode = Checkbutton(self.master, text="Cathode", variable=self.cathode_var)
        self.check_cathode.pack()

        self.derivative_var = IntVar()
        self.check_derivative = Checkbutton(self.master, text="Derivative Inverse", variable=self.derivative_var)
        self.check_derivative.pack()

    def browse_files(self):
        file_path = filedialog.askopenfilename(filetypes=[("Text files", "*.txt")])
        if file_path:
            current_entry = self.entry_battery_loc
            current_entry.delete(0, tk.END)
            current_entry.insert(0, file_path)

    def run_optimization(self):
        iterations = self.iterations_var.get()
        battery = self.battery_var.get()
        anode = self.anode_var.get()
        cathode = self.cathode_var.get()
        derivative_inverse = self.derivative_var.get()

        self.cathode_loc = self.entry_cathode_loc.get() or self.default_cathode_loc
        self.anode_loc = self.entry_anode_loc.get() or self.default_anode_loc
        self.battery_loc = self.entry_battery_loc.get() or self.default_battery_loc

        self.interpolated_cathodes = add_half_cell_data(self.cathode_loc)
        self.interpolated_anodes = add_half_cell_data(self.anode_loc)
        self.SOC_battery, self.OCV_battery = load_soc_ocv_data(self.battery_loc)

        result = perform_full_optimization_parallel(
            self.SOC_battery, self.OCV_battery,
            self.interpolated_cathodes, self.interpolated_anodes,
            iterations=iterations, battery=battery, anode=anode,
            cathode=cathode, derivative_inverse=derivative_inverse
        )

if __name__ == "__main__":
    root = tk.Tk()
    gui = OCVBatteryDecompositionGUI(root)
    root.mainloop()
