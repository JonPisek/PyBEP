from optimization_functions import perform_full_optimization_parallel
from add_curves import add_half_cell_data
from add_battery import load_soc_ocv_data

battery_loc = r'C:\Users\Uporabnik\Desktop\package_directory\battery_ocv_decomposition\battery_data.txt'

directory_name = 'battery_ocv_decomposition'
interpolated_cathodes = add_half_cell_data(directory_name + '/cathode_data')
interpolated_anodes = add_half_cell_data(directory_name + '/anode_data')
SOC_battery, OCV_battery = load_soc_ocv_data(battery_loc)

print(interpolated_cathodes)
print(interpolated_anodes)

# Example usage:
perform_full_optimization_parallel(SOC_battery, OCV_battery, interpolated_cathodes, interpolated_anodes, iterations=1)
