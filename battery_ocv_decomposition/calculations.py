import numpy as np
import matplotlib.pyplot as plt
from scipy.interpolate import interp1d
from scipy.optimize import differential_evolution
from joblib import Parallel, delayed
from add_curves import add_half_cell_data
from add_battery import load_soc_ocv_data

cathode_loc = r'C:\Users\Uporabnik\Desktop\package_directory\battery_ocv_decomposition\cathode_data'
anode_loc = r'C:\Users\Uporabnik\Desktop\package_directory\battery_ocv_decomposition\anode_data'
battery_loc = r'C:\Users\Uporabnik\Desktop\package_directory\battery_ocv_decomposition\battery_data.txt'

interpolated_cathodes = add_half_cell_data(cathode_loc)
interpolated_anodes = add_half_cell_data(anode_loc)
SOC_battery, OCV_battery = load_soc_ocv_data(battery_loc)

print(interpolated_cathodes)
print(interpolated_anodes)

# OPTIMIZATION

def calculate_inverse_derivative(x, y):
    yd = np.gradient(y, x)
    yi = 1 / yd
    return yi

def perform_full_optimization(SOC_battery, OCV_battery, interpolated_cathodes, interpolated_anodes, iterations=5, battery = 1, anode = 0, cathode = 0, derivative_inverse = 0):
    def perform_optimization(cathode_number, cathode_info, anode_number, anode_info):
        cathode_interp = cathode_info['interpolated_function']
        cathode_x_values = cathode_info['x_values']

        anode_interp = anode_info['interpolated_function']
        anode_x_values = anode_info['x_values']

        def optimization(params):
            a, c, e_percentage, f_percentage, g_percentage, h_percentage = params

            e = int(e_percentage * len(anode_x_values) * 0.3)
            f = len(anode_x_values) - int(f_percentage * len(anode_x_values) * 0.3)
            g = int(g_percentage * len(cathode_x_values) * 0.15)
            h = len(cathode_x_values) - int(h_percentage * len(cathode_x_values) * 0.15)

            if f > len(anode_x_values):
                f = len(anode_x_values)

            if h > len(cathode_x_values):
                h = len(cathode_x_values)

            v = anode_interp(a * anode_x_values[e:f])
            w = interp1d(anode_x_values[e:f], v, kind='cubic', fill_value='extrapolate')
            x_a = np.linspace(anode_x_values[e:f][0], anode_x_values[e:f][-1], 1001)

            q = cathode_interp(c * cathode_x_values[g:h])
            r = interp1d(cathode_x_values[g:h], q, kind='cubic', fill_value='extrapolate')
            x_c = np.linspace(cathode_x_values[g:h][0], cathode_x_values[g:h][-1], 1001)

            anode_calculated = r(x_c) - OCV_battery
            cathode_calculated = w(x_a) + OCV_battery
            calculated_battery_OCV = r(x_c) - w(x_a)

            calculated_battery_OCV_d_in = calculate_inverse_derivative(SOC_battery, calculated_battery_OCV)
            OCV_battery_d_in = calculate_inverse_derivative(SOC_battery, OCV_battery)

            RMSD = battery * np.sqrt(np.mean((calculated_battery_OCV - OCV_battery) ** 2)) \
                   + anode * np.sqrt(np.mean((anode_calculated - w(x_a)) ** 2)) \
                   + cathode * np.sqrt(np.mean((cathode_calculated - r(x_c)) ** 2)) \
                   + derivative_inverse * np.sqrt(np.mean((calculated_battery_OCV_d_in - OCV_battery_d_in) ** 2))
            return RMSD

        bounds = [(0, 2), (0, 2), (0, 1), (0, 1), (0, 1), (0, 1)]

        opt_result = differential_evolution(optimization, bounds)
        optimized_params = opt_result.x
        RMSD_opt = opt_result.fun

        return {
            'cathode_data_ID': cathode_number,
            'anode_data_ID': anode_number,
            'optimized_params': optimized_params,
            'RMSD': RMSD_opt
        }

    best_optimization_results = []

    for iteration in range(iterations):
        optimization_results = []
        num_cores = -1

        results = Parallel(n_jobs=num_cores, timeout=120)(
            delayed(perform_optimization)(
                cathode_number, cathode_info, anode_number, anode_info
            ) for cathode_number, cathode_info in interpolated_cathodes.items()
              for anode_number, anode_info in interpolated_anodes.items()
        )

        optimization_results.extend(results)

        best_optimization_result_iteration = min(results, key=lambda x: x['RMSD'])
        best_optimization_results.append(best_optimization_result_iteration)

    best_optimization_result = min(best_optimization_results, key=lambda x: x['RMSD'])

    best_cathode_data_ID = best_optimization_result['cathode_data_ID']
    best_anode_data_ID = best_optimization_result['anode_data_ID']

    Best_Cathode = interpolated_cathodes.get(best_cathode_data_ID)
    Best_Anode = interpolated_anodes.get(best_anode_data_ID)

    if Best_Cathode is not None and Best_Anode is not None:
        a_opt, c_opt, e_percentage_opt, f_percentage_opt, g_percentage_opt, h_percentage_opt = best_optimization_result['optimized_params']
        e_opt = int(e_percentage_opt * len(Best_Anode['x_values']) * 0.3)
        f_opt = len(Best_Anode['x_values']) - int(f_percentage_opt * len(Best_Anode['x_values']) * 0.3)
        g_opt = int(g_percentage_opt * len(Best_Cathode['x_values']) * 0.15)
        h_opt = len(Best_Cathode['x_values']) - int(h_percentage_opt * len(Best_Cathode['x_values']) * 0.15)
        best_parameters = a_opt, c_opt, e_opt, f_opt, g_opt, h_opt

        v1 = Best_Anode['interpolated_function'](a_opt * Best_Anode['x_values'][e_opt:f_opt])
        w1 = interp1d(Best_Anode['x_values'][e_opt:f_opt], v1, kind='cubic', fill_value='extrapolate')
        x_a1 = np.linspace(Best_Anode['x_values'][e_opt:f_opt][0], Best_Anode['x_values'][e_opt:f_opt][-1], 1001)

        q1 = Best_Cathode['interpolated_function'](c_opt * Best_Cathode['x_values'][g_opt:h_opt])
        r1 = interp1d(Best_Cathode['x_values'][g_opt:h_opt], q1, kind='cubic', fill_value='extrapolate')
        x_c1 = np.linspace(Best_Cathode['x_values'][g_opt:h_opt][0], Best_Cathode['x_values'][g_opt:h_opt][-1], 1001)

        calculated_battery_OCV_opt = r1(x_c1) - w1(x_a1)

        plt.figure(figsize=(8, 6))
        plt.plot(SOC_battery, OCV_battery, 'r-', label='Measured battery OCV')
        plt.plot(SOC_battery, calculated_battery_OCV_opt, 'b-', label='Optimized Battery OCV')
        plt.plot(SOC_battery, r1(x_c1), 'g-', label='Optimized Cathode OCP')
        plt.plot(SOC_battery, w1(x_a1), 'k-', label='Optimized Anode OCP')
        plt.title("Optimization")
        plt.xlabel('SOC (% / 100)')
        plt.ylabel('OCV (V)')
        plt.grid(True)
        plt.legend()
        plt.show()
    else:
        print("Interpolation for the best cathode or anode failed.")

    print("Overall Best Cathode Data ID:", best_cathode_data_ID)
    print("Overall Best Anode Data ID:", best_anode_data_ID)
    print("Overall Best Parameters:", best_parameters)
    print("Overall Lowest RMSD:", best_optimization_result['RMSD'])

# Example usage:
perform_full_optimization(SOC_battery, OCV_battery, interpolated_cathodes, interpolated_anodes, iterations=1)
print('Finish')