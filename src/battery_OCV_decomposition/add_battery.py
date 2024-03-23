import numpy as np


def load_soc_ocv_data(txt_file):
    """
    Load SOC and OCV data from a txt file.

    Parameters:
    - txt_file (str): Path to the txt file containing SOC and OCV data.

    Returns:
    - numpy.ndarray, numpy.ndarray: SOC_battery and OCV_battery arrays.
    """
    # Load data from the txt file
    with open(txt_file, 'r') as file:
        lines = file.readlines()

    # Extract x and y values from the file
    data_pairs = [map(float, line.strip().split()) for line in lines]
    SOC_battery, OCV_battery = zip(*data_pairs)

    # Convert to NumPy arrays
    SOC_battery = np.array(SOC_battery)
    OCV_battery = np.array(OCV_battery)

    return SOC_battery, OCV_battery


# Example usage:
txt_file_path = r'data\battery_data.txt'
SOC_battery, OCV_battery = load_soc_ocv_data(txt_file_path)
print("SOC_battery:", SOC_battery)
print("OCV_battery:", OCV_battery)
