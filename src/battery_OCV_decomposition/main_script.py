from optimization_functions import perform_full_optimization_parallel_to_json
from add_curves import add_half_cell_data
from add_battery import load_soc_ocv_data


def main():
    battery_loc = r'data\battery_data.txt'
    directory_name = 'data'
    interpolated_cathodes = add_half_cell_data(directory_name + '/cathode_data')  # noqa: E501
    interpolated_anodes = add_half_cell_data(directory_name + '/anode_data')
    SOC_battery, OCV_battery = load_soc_ocv_data(battery_loc)

    # Specify the file location where you want to save the JSON file
    file_location = 'results'

    # Run the function
    perform_full_optimization_parallel_to_json("test.json",
                                               file_location, SOC_battery,
                                               OCV_battery,
                                               interpolated_cathodes,
                                               interpolated_anodes,
                                               iterations=1, battery=1,
                                               cathode=0,
                                               anode=0, derivative_inverse=0)

    print("Optimization completed")


if __name__ == "__main__":
    main()
