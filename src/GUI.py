import tkinter as tk
from tkinter import Label, Entry, filedialog, IntVar, Scale, Button, DoubleVar
from optimization_functions import perform_full_optimization_parallel_to_json_GUI  # noqa: E501
from optimization_functions import perform_full_optimization_parallel  # noqa: E501
from add_curves import add_half_cell_data
from add_battery import load_soc_ocv_data
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg


class OCVBatteryDecompositionGUI:
    def __init__(self, master):
        self.master = master
        master.title("OCV Battery Decomposition")
        screen_width = master.winfo_screenwidth()
        screen_height = master.winfo_screenheight()
        font_size = int(screen_height / 50)
        master.geometry(f"{int(screen_width)}x{int(screen_height)}")
        self.default_cathode_loc = ""
        self.default_anode_loc = ""
        self.default_battery_loc = ""
        self.cathode_loc = ""
        self.anode_loc = ""
        self.battery_loc = ""
        self.interpolated_cathodes = None
        self.interpolated_anodes = None
        self.SOC_battery = None
        self.OCV_battery = None
        self.dark_mode = False
        self.left_frame = tk.Frame(master, width=screen_width, bg="white")
        self.left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.right_frame = tk.Frame(master)
        self.right_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.create_file_location_entries(font_size)
        self.create_input_widgets(font_size)
        self.run_button = tk.Button(
            self.left_frame, text="Run Optimization",
            command=lambda: self.run_optimization(font_size),
            width=int(font_size),
            font=("Arial", int(font_size*0.8)))
        self.run_button.pack(pady=10)
        self.download_button = Button(
            self.left_frame, text="Download Result",
            command=self.download_result, width=int(font_size),
            font=("Arial", int(font_size*0.8)))
        self.result_label = None
        self.plot = self.create_empty_plot()
        self.plot.get_tk_widget().pack(
            side=tk.TOP, fill=tk.BOTH, expand=True)
        self.add_logo(font_size)
        self.add_theme_switch(font_size)

    def create_file_location_entries(self, font_size):
        self.label_cathode_loc = Label(
            self.left_frame, text="Cathode Folder Location:",
            font=("Arial", int(font_size*0.8)), bg="white")
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
            font=("Arial", int(font_size*0.8)), bg="white")
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
            font=("Arial", int(font_size*0.8)), bg="white")
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
        self.iterations_frame = tk.Frame(self.left_frame, bg="white")
        self.iterations_frame.pack(pady=(0, 0), padx=0, fill=tk.X)
        self.label_iterations = Label(
            self.iterations_frame, text="Iterations:",
            font=("Arial", int(font_size*0.8)), bg="white")
        self.label_iterations.pack()
        self.iterations_var = IntVar()
        self.scale_iterations = Scale(
            self.iterations_frame, from_=1, to=5, orient=tk.HORIZONTAL,
            variable=self.iterations_var, length=font_size*15)
        self.scale_iterations.set(1)
        self.scale_iterations.pack()
        self.battery_frame = tk.Frame(self.left_frame, bg="white")
        self.battery_frame.pack(pady=(0, 0), padx=0, fill=tk.X)
        self.label_battery = Label(
            self.battery_frame, text="Battery weight:",
            font=("Arial", int(font_size*0.8)), bg="white")
        self.label_battery.pack()
        self.battery_var = DoubleVar(value=1)
        self.scale_battery = Scale(
            self.battery_frame, from_=0, to=1, orient=tk.HORIZONTAL,
            variable=self.battery_var, length=font_size*15, resolution=0.2)
        self.scale_battery.pack()
        self.derivative_frame = tk.Frame(self.left_frame, bg="white")
        self.derivative_frame.pack(pady=(0, 0), padx=0, fill=tk.X)
        self.label_derivative = Label(
            self.derivative_frame, text="Differential capacity weight:",
            font=("Arial", int(font_size*0.8)), bg="white")
        self.label_derivative.pack()
        self.derivative_var = DoubleVar(value=0)
        self.scale_derivative = Scale(
            self.derivative_frame, from_=0, to=1, orient=tk.HORIZONTAL,
            variable=self.derivative_var, length=font_size*15, resolution=0.2)
        self.scale_derivative.pack()

    def browse_files(self, entry_widget):
        if entry_widget == self.entry_battery_loc:
            file_path = filedialog.askopenfilename(
                filetypes=[("Text files", "*.txt")])
        else:
            file_path = filedialog.askdirectory()
        if file_path:
            entry_widget.delete(0, tk.END)
            entry_widget.insert(0, file_path)

    def run_optimization(self, font_size):
        iterations = self.iterations_var.get()
        battery = self.battery_var.get()
        derivative_inverse = self.derivative_var.get()
        self.cathode_loc = self.entry_cathode_loc.get()
        self.anode_loc = self.entry_anode_loc.get()
        self.battery_loc = self.entry_battery_loc.get()
        if not (self.cathode_loc and self.anode_loc and self.battery_loc):
            print("Please select all folder locations.")
            return
        self.interpolated_cathodes = add_half_cell_data(self.cathode_loc)
        self.interpolated_anodes = add_half_cell_data(self.anode_loc)
        self.SOC_battery, self.OCV_battery = load_soc_ocv_data(self.battery_loc)  # noqa: E501
        result = perform_full_optimization_parallel(
            self.SOC_battery, self.OCV_battery,
            self.interpolated_cathodes, self.interpolated_anodes,
            iterations=iterations, battery=battery,
            derivative_inverse=derivative_inverse
        )

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
                                      font=("Arial", font_size))
            self.result_label.pack(pady=10)
            self.download_button.pack_forget()
            self.download_button.pack(pady=10)
        else:
            print("Interpolation for the best cathode or anode failed.")

    def download_result(self):
        result_filename = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSON files", "*.json")])
        if result_filename:
            perform_full_optimization_parallel_to_json_GUI(
                result_filename, self.SOC_battery, self.OCV_battery,
                self.interpolated_cathodes, self.interpolated_anodes,
                iterations=self.iterations_var.get(),
                battery=self.battery_var.get(),
                derivative_inverse=self.derivative_var.get()
            )
            print("Result downloaded successfully.")
            self.download_button.pack_forget()

    def plot_results(self, result):
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
        empty_fig = plt.figure(figsize=(8, 6))
        empty_plot = FigureCanvasTkAgg(empty_fig, master=self.right_frame)
        return empty_plot

    def add_logo(self, font_size):
        canvas = tk.Canvas(self.left_frame, width=font_size*20,
                           height=font_size*10, bg="#FFFFFF")
        canvas.pack(side=tk.BOTTOM, padx=0, pady=0)
        text = "LICeM"
        text_color = "#2C2F33"
        underline_color = "#55acee"
        underline_thickness = int(font_size/2)
        text_width = len(text) * font_size*2
        x_pos = (canvas.winfo_width() - text_width) // 2\
            + text_width - 2 * font_size
        y_pos = int(font_size * 4.8)
        canvas.create_line(x_pos - font_size,
                           y_pos + font_size*3,
                           x_pos + text_width + font_size * 6,
                           y_pos + font_size*3,
                           fill=underline_color,
                           width=underline_thickness)

        for letter in text:
            if letter == "e":
                x_pos += font_size
                canvas.create_text(x_pos, y_pos, text=letter,
                                   font=("Arial", font_size*4),
                                   fill=underline_color)
                x_pos += font_size
            else:
                canvas.create_text(x_pos, y_pos, text=letter,
                                   font=("Arial", font_size*4),
                                   fill=text_color)
            x_pos += font_size*3

    def toggle_theme(self):
        self.dark_mode = not self.dark_mode
        self.left_frame.config(bg="#2C2F33" if self.dark_mode else "white")  # noqa: E501
        self.iterations_frame.config(bg="#8bbcd6" if self.dark_mode else "white")  # noqa: E501
        self.battery_frame.config(bg="#8bbcd6" if self.dark_mode else "white")  # noqa: E501
        self.derivative_frame.config(bg="#8bbcd6" if self.dark_mode else "white")  # noqa: E501
        self.label_iterations.config(bg="#8bbcd6" if self.dark_mode else "white")  # noqa: E501
        self.label_battery.config(bg="#8bbcd6" if self.dark_mode else "white")  # noqa: E501
        self.label_derivative.config(bg="#8bbcd6" if self.dark_mode else "white")  # noqa: E501
        self.run_button.config(bg="#99aab5" if self.dark_mode else "SystemButtonFace",  # noqa: E501
                               fg="black" if self.dark_mode else "black")  # noqa: E501
        self.download_button.config(bg="#99aab5" if self.dark_mode else "SystemButtonFace",  # noqa: E501
                                    fg="black" if self.dark_mode else "black")  # noqa: E501
        self.label_cathode_loc.config(bg="#2C2F33" if self.dark_mode else "white",  # noqa: E501
                                      fg="white" if self.dark_mode else "black")  # noqa: E501
        self.label_anode_loc.config(bg="#2C2F33" if self.dark_mode else "white",  # noqa: E501
                                    fg="white" if self.dark_mode else "black")  # noqa: E501
        self.label_battery_loc.config(bg="#2C2F33" if self.dark_mode else "white",  # noqa: E501
                                      fg="white" if self.dark_mode else "black")  # noqa: E501
        self.browse_button.config(bg="#99aab5" if self.dark_mode else "SystemButtonFace",  # noqa: E501
                                  fg="black" if self.dark_mode else "black")
        self.master.config(bg="#2C2F33" if self.dark_mode else "white")

    def add_theme_switch(self, font_size):
        toggle_theme_button = Button(self.left_frame, text="LICeM Theme",
                                     command=self.toggle_theme,
                                     font=("Arial", int(font_size*0.8)))
        toggle_theme_button.pack(side=tk.TOP, pady=(20, 0), padx=10)


if __name__ == "__main__":
    root = tk.Tk()
    root.resizable(width=True, height=True)
    gui = OCVBatteryDecompositionGUI(root)
    root.mainloop()
