import tkinter as tk
from tkinter import Label, Entry, filedialog, IntVar, Scale, Button, DoubleVar
from PIL import Image, ImageTk
from .optimization_functions import perform_full_optimization_parallel_to_json_GUI  # noqa: E501
from .optimization_functions import perform_full_optimization_parallel  # noqa: E501
from .add_curves import add_half_cell_data
from .add_battery import load_soc_ocv_data
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

class OCVBatteryDecompositionGUI:
    def __init__(self, master):
        self.master = master
        master.title("PyBEP")
        
        # Set the window size to match the screen resolution
        screen_width = master.winfo_screenwidth()
        screen_height = master.winfo_screenheight()
        font_size = int(screen_height / 50)
        master.geometry(f"{int(screen_width)}x{int(screen_height)}")
        
        # Initialize default file locations
        self.default_cathode_loc = ""
        self.default_anode_loc = ""
        self.default_battery_loc = ""
        self.cathode_loc = ""
        self.anode_loc = ""
        self.battery_loc = ""
        
        # Initialize variables for interpolated data and battery SOC/OCV
        self.interpolated_cathodes = None
        self.interpolated_anodes = None
        self.SOC_battery = None
        self.OCV_battery = None
        
        # Create left and right frames for the GUI
        self.left_frame = tk.Frame(master, width=screen_width, bg="#2C2F33")
        self.left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.right_frame = tk.Frame(master)
        self.right_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # Create file location entries, input widgets, and buttons
        self.create_file_location_entries(font_size)
        self.create_input_widgets(font_size)
        
        # Run optimization button
        self.run_button = tk.Button(
            self.left_frame, text="Run Optimization",
            command=lambda: self.run_optimization(font_size),
            width=int(font_size),
            font=("Arial", int(font_size*0.8)))
        self.run_button.pack(pady=10)
        
        # Download result button
        self.download_button = Button(
            self.left_frame, text="Download Result",
            command=self.download_result, width=int(font_size),
            font=("Arial", int(font_size*0.8)))
        
        # Result label and plot
        self.result_label = None
        self.plot = self.create_empty_plot()
        self.plot.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=True)
        
        # Add logo
        self.add_logo(font_size)

        # Add logo to right frame initially
        self.add_initial_logo(font_size) 

    def create_file_location_entries(self, font_size):
        # Create labels and entries for cathode, anode, and battery file locations
        self.label_cathode_loc = Label(
            self.left_frame, text="Cathode Folder Location:",
            font=("Arial", int(font_size*0.8)), bg="#2C2F33", fg="white")
        self.label_cathode_loc.pack()
        self.entry_cathode_loc = Entry(self.left_frame, width=font_size*3,
                                         font=("Arial", int(font_size*0.8)))
        self.entry_cathode_loc.pack()
        self.browse_button_cathode = tk.Button(
            self.left_frame, text="Browse",
            command=lambda: self.browse_files(self.entry_cathode_loc),
            width=int(font_size*0.8),
            font=("Arial", int(font_size*0.8)))
        self.browse_button_cathode.pack()

        self.label_anode_loc = Label(
            self.left_frame, text="Anode Folder Location:",
            font=("Arial", int(font_size*0.8)), bg="#2C2F33", fg="white")
        self.label_anode_loc.pack()
        self.entry_anode_loc = Entry(self.left_frame, width=font_size*3,
                                           font=("Arial", int(font_size*0.8)))
        self.entry_anode_loc.pack()
        self.browse_button_anode = tk.Button(
            self.left_frame, text="Browse",
            command=lambda: self.browse_files(self.entry_anode_loc),
            width=int(font_size*0.8),
            font=("Arial", int(font_size*0.8)))
        self.browse_button_anode.pack()

        self.label_battery_loc = Label(
            self.left_frame, text="Battery File Location:",
            font=("Arial", int(font_size*0.8)), bg="#2C2F33", fg="white")
        self.label_battery_loc.pack()
        self.entry_battery_loc = Entry(self.left_frame, width=font_size*3,
                                         font=("Arial", int(font_size*0.8)))
        self.entry_battery_loc.pack()
        self.browse_button_battery = tk.Button(
            self.left_frame, text="Browse",
            command=lambda: self.browse_files(self.entry_battery_loc),
            width=int(font_size*0.8),
            font=("Arial", int(font_size*0.8)))
        self.browse_button_battery.pack()

    def create_input_widgets(self, font_size):
        # Create input widgets for iterations, battery weight, and derivative weight
        self.iterations_frame = tk.Frame(self.left_frame, bg="#2C2F33")
        self.iterations_frame.pack(pady=(0, 0), padx=0, fill=tk.X)
        self.label_iterations = Label(
            self.iterations_frame, text="Iterations:",
            font=("Arial", int(font_size*0.8)), bg="#2C2F33", fg="white")
        self.label_iterations.pack()
        self.iterations_var = IntVar()
        self.scale_iterations = Scale(
            self.iterations_frame, from_=1, to=5, orient=tk.HORIZONTAL,
            variable=self.iterations_var, length=font_size*15)
        self.scale_iterations.set(1)
        self.scale_iterations.pack()

        # Battery Weight Slider
        self.battery_frame = tk.Frame(self.left_frame, bg="#2C2F33")
        self.battery_frame.pack(pady=(0, 0), padx=0, fill=tk.X)
        self.label_battery = Label(
            self.battery_frame, text="Battery weight:",
            font=("Arial", int(font_size*0.8)), bg="#2C2F33", fg="white")
        self.label_battery.pack()
        self.battery_var = DoubleVar(value=1)
        self.scale_battery = Scale(
            self.battery_frame, from_=0, to=1, orient=tk.HORIZONTAL,
            variable=self.battery_var, length=font_size*15, resolution=0.05,
            command=self.update_derivative_weight) # Added command
        self.scale_battery.pack()

        # Differential Capacity Weight Slider
        self.derivative_frame = tk.Frame(self.left_frame, bg="#2C2F33")
        self.derivative_frame.pack(pady=(0, 0), padx=0, fill=tk.X)
        self.label_derivative = Label(
            self.derivative_frame, text="Differential capacity weight:",
            font=("Arial", int(font_size*0.8)), bg="#2C2F33", fg="white")
        self.label_derivative.pack()
        self.derivative_var = DoubleVar(value=0)
        self.scale_derivative = Scale(
            self.derivative_frame, from_=0, to=1, orient=tk.HORIZONTAL,
            variable=self.derivative_var, length=font_size*15, resolution=0.05,
            command=self.update_battery_weight) # Added command
        self.scale_derivative.pack()

    def update_derivative_weight(self, val):
        # Updates the derivative weight slider when battery weight changes.
        battery_val = float(val)
        derivative_val = round(1.0 - battery_val, 2) # Ensure sum is 1, round to resolution
        self.derivative_var.set(derivative_val)

    def update_battery_weight(self, val):
        # Updates the battery weight slider when derivative weight changes.
        derivative_val = float(val)
        battery_val = round(1.0 - derivative_val, 2) # Ensure sum is 1, round to resolution
        self.battery_var.set(battery_val)

    def browse_files(self, entry_widget):
        # Browse for files or directories based on the entry widget
        if entry_widget == self.entry_battery_loc:
            file_path = filedialog.askopenfilename(
                filetypes=[("Text files", "*.txt")])
        else:
            file_path = filedialog.askdirectory()
        if file_path:
            entry_widget.delete(0, tk.END)
            entry_widget.insert(0, file_path)

    def run_optimization(self, font_size):
        # Run the optimization process
        iterations = self.iterations_var.get()
        battery = self.battery_var.get()
        derivative_inverse = self.derivative_var.get()
        self.cathode_loc = self.entry_cathode_loc.get()
        self.anode_loc = self.entry_anode_loc.get()
        self.battery_loc = self.entry_battery_loc.get()
        
        # Check if all file locations are selected
        if not (self.cathode_loc and self.anode_loc and self.battery_loc):
            print("Please select all folder locations.")
            return
        
        # Load and interpolate cathode and anode data
        self.interpolated_cathodes = add_half_cell_data(self.cathode_loc)
        self.interpolated_anodes = add_half_cell_data(self.anode_loc)
        self.SOC_battery, self.OCV_battery = load_soc_ocv_data(self.battery_loc)  # noqa: E501
        
        # Perform optimization
        result = perform_full_optimization_parallel(
            self.SOC_battery, self.OCV_battery,
            self.interpolated_cathodes, self.interpolated_anodes,
            iterations=iterations, battery=battery,
            derivative_inverse=derivative_inverse
        )

        # Plot results and display optimization results
        if result['calculated_battery_OCV_opt'] is not None:
            self.plot_results(result)
            data_label_text = (
                f"Best Cathode Data ID: {result['Best Cathode Data ID']}\n"
                f"Best Anode Data ID: {result['Best Anode Data ID']}\n"
                f"Best Parameters: {result['Best Parameters']}\n"
                f"Lowest RMSD: {result['Lowest RMSD']}"
            )
            if self.result_label:
                self.result_label.destroy()
            self.result_label = Label(self.left_frame, text=data_label_text,
                                     font=("Arial", font_size), fg="white", bg="#2C2F33")
            self.result_label.pack(pady=10)

            # Destroy the initial logo canvas/label on the right frame
            if hasattr(self, 'logo_label'):
                self.logo_label.destroy()
            
            # Show download button
            self.download_button.pack(pady=10)

    def download_result(self):
        # Download the optimization result as a JSON file
        result_filename = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSON files", "*.json")]
        )
        if result_filename:
            perform_full_optimization_parallel_to_json_GUI(
                result_filename, self.SOC_battery, self.OCV_battery,
                self.interpolated_cathodes, self.interpolated_anodes,
                iterations=self.iterations_var.get(),
                battery=self.battery_var.get(),
                derivative_inverse=self.derivative_var.get()
            )
            print("Result downloaded successfully.")
        
        # Hide the download button after downloading
        self.download_button.pack_forget()

    def plot_results(self, result):
        # Plot the optimization results
        if self.plot is None:
            self.plot = FigureCanvasTkAgg(
                plt.figure(figsize=(8, 6)), master=self.right_frame)
            self.plot.get_tk_widget().pack(
                side=tk.TOP, fill=tk.BOTH, expand=True)
        else:
            self.plot.get_tk_widget().destroy()
            self.plot = FigureCanvasTkAgg(
                plt.figure(figsize=(8, 6)), master=self.right_frame)
            self.plot.get_tk_widget().pack(
                side=tk.TOP, fill=tk.BOTH, expand=True)

        # Plot the measured and optimized battery OCV, cathode OCP, and anode OCP
        plt.plot(
            self.SOC_battery, self.OCV_battery,
            'r-', label='Measured battery OCV')
        plt.plot(
            self.SOC_battery, result['calculated_battery_OCV_opt'],
            'b-', label='Optimized Battery OCV')
        plt.plot(
            result['c_SOC_full'], result['r1_ns_x_c1_ns'], 'r--')
        plt.plot(
            result['c_SOC'], result['r1_x_c1'],
            'g-', label='Optimized Cathode OCP')
        plt.plot(result['a_SOC_full'], result['w1_ns_x_a1_ns'], 'r--')
        plt.plot(
            result['a_SOC'], result['w1_x_a1'],
            'k-', label='Optimized Anode OCP')
        plt.title("Optimization")
        plt.xlabel('SOC (% / 100)')
        plt.ylabel('OCV (V)')
        plt.grid(True)
        plt.legend()

    def create_empty_plot(self):
        # Create an empty plot for initial display
        empty_fig = plt.figure(figsize=(8, 6))
        empty_plot = FigureCanvasTkAgg(empty_fig, master=self.right_frame)
        return empty_plot

    def add_logo(self, font_size):
        # Load the image
        logo_path = "LICEM/Logo1.png"
        image = Image.open(logo_path)

        resample_filter = Image.Resampling.LANCZOS  
        image = image.resize((font_size * 8, font_size * 8), resample_filter)

        logo_image = ImageTk.PhotoImage(image)
        self.logo_img = logo_image

        canvas = tk.Canvas(self.left_frame,
                           width=font_size * 8,
                           height=font_size * 8,
                           bg="#2C2F33",
                           highlightthickness=0)
        # Pack the canvas to the bottom right of the left_frame
        canvas.pack(side=tk.BOTTOM, anchor=tk.SE, padx=0, pady=0) 

        # Place the image at the bottom-right of the canvas using anchor
        canvas.create_image(font_size * 8, font_size * 8,
                             anchor=tk.SE,
                             image=self.logo_img)
        
    def add_initial_logo(self, font_size):
        logo_path = "LICEM/Logo3.png"
        image = Image.open(logo_path)

        # Maintain aspect ratio
        original_width, original_height = image.size
        aspect_ratio = original_width / original_height

        # Get current screen dimensions from the master window
        screen_width = self.master.winfo_screenwidth()
        screen_height = self.master.winfo_screenheight()

        target_max_height = screen_height * 0.8
        target_max_width = (screen_width / 2) * 0.9

        if (target_max_width / aspect_ratio) <= target_max_height:
            # Scale based on width
            new_width = int(target_max_width)
            new_height = int(target_max_width / aspect_ratio)
        else:
            # Scale based on height
            new_height = int(target_max_height)
            new_width = int(target_max_height * aspect_ratio)

        # Enforce a minimum size
        min_logo_size = font_size * 10
        if new_width < min_logo_size and new_height < min_logo_size:
            new_width = min_logo_size
            new_height = int(min_logo_size / aspect_ratio)


        resample_filter = Image.Resampling.LANCZOS
        image = image.resize((new_width, new_height), resample_filter)

        logo_image = ImageTk.PhotoImage(image)
        self.initial_logo_img = logo_image

        self.logo_label = tk.Label(self.right_frame, image=logo_image, bg="white")
        self.logo_label.place(relx=0.5, rely=0.5, anchor='center') 
            
# Main application loop
root = tk.Tk()
root.resizable(width=True, height=True)
gui = OCVBatteryDecompositionGUI(root)
# Small credit text at bottom-left corner
credit_label = tk.Label(
    root,
    text="Developed by LICeM",
    font=("Arial", 11),
    bg="#2C2F33",
    fg="white"
)
credit_label.place(x=5, rely=1.0, anchor='sw')
root.mainloop()