import tkinter as tk
from tkinter import Label, Entry, filedialog, IntVar, Checkbutton, Scale
from optimization_functions import perform_full_optimization_parallel
from add_curves import add_half_cell_data
from add_battery import load_soc_ocv_data
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

class OCVBatteryDecompositionGUI:
    def __init__(self, master):
        self.master = master
        master.title("OCV Battery Decomposition")

        # Set the initial window size
        master.geometry("800x600")

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

        # Create the left frame
        self.left_frame = tk.Frame(master)
        self.left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Create the right frame
        self.right_frame = tk.Frame(master)
        self.right_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Create GUI elements on the left side
        self.create_file_location_entries()
        self.create_input_widgets()

        self.run_button = tk.Button(self.left_frame, text="Run Optimization", command=self.run_optimization, width=20)
        self.run_button.pack(pady=10)

        # Create the label for displaying RMSD value on the right side
        self.result_label = Label(self.right_frame, text="")
        self.result_label.pack()

        # Initialize plot variable
        self.plot = None

    def create_file_location_entries(self):
        self.label_cathode_loc = Label(self.left_frame, text="Cathode Folder Location:")
        self.label_cathode_loc.pack()

        self.entry_cathode_loc = Entry(self.left_frame, width=50)
        self.entry_cathode_loc.insert(0, self.default_cathode_loc)  # Set default value
        self.entry_cathode_loc.pack()

        self.label_anode_loc = Label(self.left_frame, text="Anode Folder Location:")
        self.label_anode_loc.pack()

        self.entry_anode_loc = Entry(self.left_frame, width=50)
        self.entry_anode_loc.insert(0, self.default_anode_loc)  # Set default value
        self.entry_anode_loc.pack()

        self.label_battery_loc = Label(self.left_frame, text="Battery File Location:")
        self.label_battery_loc.pack()

        self.entry_battery_loc = Entry(self.left_frame, width=50)
        self.entry_battery_loc.insert(0, self.default_battery_loc)  # Set default value
        self.entry_battery_loc.pack()

        self.browse_button = tk.Button(self.left_frame, text="Browse", command=self.browse_files)
        self.browse_button.pack()

    def create_input_widgets(self):
        self.label_iterations = Label(self.left_frame, text="Iterations:")
        self.label_iterations.pack()

        self.iterations_var = IntVar()
        self.scale_iterations = Scale(self.left_frame, from_=1, to=5, orient=tk.HORIZONTAL, variable=self.iterations_var, length=200)
        self.scale_iterations.set(5)  # Set default value
        self.scale_iterations.pack()

        self.label_binary_params = Label(self.left_frame, text="Binary Optimization Parameters:")
        self.label_binary_params.pack()

        self.battery_var = IntVar(value=1)
        self.check_battery = Checkbutton(self.left_frame, text="Battery", variable=self.battery_var)
        self.check_battery.pack()

        self.anode_var = IntVar(value=0)
        self.check_anode = Checkbutton(self.left_frame, text="Anode", variable=self.anode_var)
        self.check_anode.pack()

        self.cathode_var = IntVar(value=0)
        self.check_cathode = Checkbutton(self.left_frame, text="Cathode", variable=self.cathode_var)
        self.check_cathode.pack()

        self.derivative_var = IntVar(value=0)
        self.check_derivative = Checkbutton(self.left_frame, text="Derivative Inverse", variable=self.derivative_var)
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

        if result['calculated_battery_OCV_opt'] is not None:
            self.plot_results(result)

            # Display the printed data
            data_label_text = f"Overall Best Cathode Data ID: {result['Overall Best Cathode Data ID']}\n"
            data_label_text += f"Overall Best Anode Data ID: {result['Overall Best Anode Data ID']}\n"
            data_label_text += f"Overall Best Parameters: {result['Overall Best Parameters']}\n"
            data_label_text += f"Overall Lowest RMSD: {result['Overall Lowest RMSD']}"
            self.result_label.config(text=data_label_text)
        else:
            print("Interpolation for the best cathode or anode failed.")

    def plot_results(self, result):
        if self.plot is None:
            self.plot = FigureCanvasTkAgg(plt.figure(figsize=(8, 6)), master=self.right_frame)
            self.plot.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=True)
        else:
            self.plot.get_tk_widget().destroy()
            self.plot = FigureCanvasTkAgg(plt.figure(figsize=(8, 6)), master=self.right_frame)
            self.plot.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=True)

        plt.plot(self.SOC_battery, self.OCV_battery, 'r-', label='Measured battery OCV')
        plt.plot(self.SOC_battery, result['calculated_battery_OCV_opt'], 'b-', label='Optimized Battery OCV')
        plt.plot(result['c_SOC_full'], result['r1_ns_x_c1_ns'], 'r--')
        plt.plot(result['c_SOC'], result['r1_x_c1'], 'g-', label='Optimized Cathode OCP')
        plt.plot(result['a_SOC_full'], result['w1_ns_x_a1_ns'], 'r--')
        plt.plot(result['a_SOC'], result['w1_x_a1'], 'k-', label='Optimized Anode OCP')
        plt.title("Optimization")
        plt.xlabel('SOC (% / 100)')
        plt.ylabel('OCV (V)')
        plt.grid(True)
        plt.legend()

if __name__ == "__main__":
    root = tk.Tk()
    gui = OCVBatteryDecompositionGUI(root)
    root.mainloop()
