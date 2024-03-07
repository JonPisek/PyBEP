import os
from scipy.interpolate import interp1d
import numpy as np

def add_half_cell_data(folder_path):
    """
    Add half-cell data from text files in a specified folder to a dictionary.

    Parameters:
    - folder_path (str): The path to the folder containing text files with data.

    Raises:
    - ValueError: If the specified folder does not exist.

    Returns:
    - dict: A dictionary containing half-cell data.
    """
    # Check if the folder exists
    if not os.path.exists(folder_path):
        raise ValueError(f"The folder '{folder_path}' does not exist.")

    # Create a dictionary to store the half-cell data
    half_cell_dictionary = {}

    # Get a list of all txt files in the folder
    txt_files = [f for f in os.listdir(folder_path) if f.endswith('.txt')]

    # Iterate through each txt file
    for file_number, txt_file in enumerate(txt_files, start=1):
        file_path = os.path.join(folder_path, txt_file)

        # Load data from the txt file
        with open(file_path, 'r') as file:
            lines = file.readlines()

        # Extract x and y values from the file
        x_values, y_values = zip(*[map(float, line.strip().split()) for line in lines])

        # Check if x values are in increasing order
        if all(x > y for x, y in zip(x_values, x_values[1:])):
            # If increasing, reverse the x, y values
            x_values = x_values[::-1]
            y_values = y_values[::-1]

        # Interpolate the OCP function
        interpolated_function = interp1d(x_values, y_values, kind='cubic', fill_value='extrapolate')

        # Create a new dataset
        new_dataset = {
            'ID_number': file_number,
            'x_values': np.array(x_values),
            'interpolated_function': interpolated_function
        }

        # Add the new dataset to the dictionary
        half_cell_dictionary[new_dataset['ID_number']] = new_dataset

    return half_cell_dictionary

# Example usage
#folder_path = "path/to/your/folder"
#dictionary = add_half_cell_data(folder_path)

cathode_loc = r'C:\Users\Uporabnik\Desktop\package_directory\battery_ocv_decomposition\cathode_data'
anode_loc = r'C:\Users\Uporabnik\Desktop\package_directory\battery_ocv_decomposition\anode_data'

interpolated_cathodes = add_half_cell_data(cathode_loc)
interpolated_anodes = add_half_cell_data(anode_loc)

print(interpolated_cathodes)
print(interpolated_anodes)

