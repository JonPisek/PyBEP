from optimization_functions import perform_full_optimization_parallel
from add_curves import add_half_cell_data
from add_battery import load_soc_ocv_data

# change this so that it's not hardcoded; this should be provided by the user - note that they
# will not change the main script; the script should only accept arguments and do something with them
# but it is not intended to be changed by the user

battery_loc = r'data\battery_data.txt'
directory_name = 'data'
interpolated_cathodes = add_half_cell_data(directory_name + '/cathode_data')
interpolated_anodes = add_half_cell_data(directory_name + '/anode_data')
SOC_battery, OCV_battery = load_soc_ocv_data(battery_loc)

print(interpolated_cathodes)
print(interpolated_anodes)

# Example usage:
result = perform_full_optimization_parallel(SOC_battery, OCV_battery, interpolated_cathodes, interpolated_anodes, iterations=1)
print(result)
