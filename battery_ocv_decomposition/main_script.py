import numpy as np
import matplotlib.pyplot as plt
from scipy.interpolate import interp1d
from scipy.optimize import differential_evolution
from joblib import Parallel, delayed
from add_curves import add_half_cell_data
from add_battery import load_soc_ocv_data
from calculations import perform_full_optimization

cathode_loc = r'C:\Users\Uporabnik\Desktop\package_directory\battery_ocv_decomposition\cathode_data'
anode_loc = r'C:\Users\Uporabnik\Desktop\package_directory\battery_ocv_decomposition\anode_data'
battery_loc = r'C:\Users\Uporabnik\Desktop\package_directory\battery_ocv_decomposition\battery_data.txt'

interpolated_cathodes = add_half_cell_data(cathode_loc)
interpolated_anodes = add_half_cell_data(anode_loc)
SOC_battery, OCV_battery = load_soc_ocv_data(battery_loc)

print(interpolated_cathodes)
print(interpolated_anodes)

# OPTIMIZATION

def calculate_derivative(x, y):
    yd = np.gradient(y, x)
    return yd

def calculate_inverse_derivative(x, y):
    yd = np.gradient(y, x)
    yi = 1 / yd
    return yi

# Example usage:
perform_full_optimization(SOC_battery, OCV_battery, interpolated_cathodes, interpolated_anodes, iterations=1)
print('Finish')