import numpy as np
from scipy.interpolate import interp1d
from scipy.optimize import differential_evolution
from joblib import Parallel, delayed
import json


def calculate_derivative_and_inverse(x, y):
    """
    Calculate the derivative and its inverse.

    Parameters:
        x (array-like): Array of x-values.
        y (array-like): Array of y-values.

    Returns:
        tuple: A tuple containing four arrays:
            - xd: The original x-values.
            - yd: The derivative of y with respect to x.
            - xi: The original x-values (same as xd).
            - yi: The reciprocal of the derivative (1/yd).
    """
    # Calculate the derivative using numpy.gradient
    xd = x
    yd = np.gradient(y, x)

    # Calculate the reciprocal of the derivative
    xi = xd
    yi = 1 / yd

    return xd, yd, xi, yi


def calculate_inverse_derivative(x, y):
    """
    Calculate the inverse of the derivative of a function.

    Parameters:
    - x: array-like
        X-axis values.
    - y: array-like
        Y-axis values.

    Returns:
    - yi: array-like
        Inverse of the derivative of the function.
    """
    yd = np.gradient(y, x)
    yi = 1 / yd
    return yi


def optimization(params, anode_interp, anode_x_values, cathode_interp,
                 cathode_x_values, OCV_battery, SOC_battery, battery=1,
                 derivative_inverse=0):
    """
    Objective function for optimization.

    Parameters:
    - params: tuple
        Optimization parameters:
        e_percentage, f_percentage, g_percentage, h_percentage.
    - anode_interp: callable
        Interpolated function for the anode.
    - anode_x_values: array-like
        X-axis values for the anode.
    - cathode_interp: callable
        Interpolated function for the cathode.
    - cathode_x_values: array-like
        X-axis values for the cathode.
    - OCV_battery: array-like
        Measured battery open-circuit voltage (OCV).
    - SOC_battery: array-like
        State of charge (SOC) values for the battery.
    - battery, derivative_inverse: float, optional
        Weighting factors for different components of the objective function.

    Returns:
    - RMSD: float
        Root Mean Square Deviation, the objective value for optimization.
    """
    e_percentage, f_percentage, g_percentage, h_percentage = params

    e = int(e_percentage * len(anode_x_values) * 0.3)
    f = len(anode_x_values) - int(f_percentage * len(anode_x_values) * 0.3)
    g = int(g_percentage * len(cathode_x_values) * 0.15)
    h = len(cathode_x_values) - int(
        h_percentage * len(cathode_x_values) * 0.15)

    if f > len(anode_x_values):
        f = len(anode_x_values)

    if h > len(cathode_x_values):
        h = len(cathode_x_values)

    v = anode_interp(anode_x_values)
    axv = anode_x_values
    w = interp1d(axv[e:f], v[e:f], kind='cubic', fill_value='extrapolate')
    x_a = np.linspace(axv[e:f][0], axv[e:f][-1], 1001)
    q = cathode_interp(cathode_x_values)
    cxv = cathode_x_values
    r = interp1d(cxv[g:h], q[g:h], kind='cubic', fill_value='extrapolate')
    x_c = np.linspace(cxv[g:h][0], cxv[g:h][-1], 1001)

    calculated_battery_OCV = r(x_c) - w(x_a)

    calculated_battery_OCV_d_in = calculate_inverse_derivative(
        SOC_battery,
        calculated_battery_OCV)
    OCV_battery_d_in = calculate_inverse_derivative(
        SOC_battery,
        OCV_battery)

    RMSD = battery * np.sqrt(
            np.mean((calculated_battery_OCV - OCV_battery) ** 2)) \
        + derivative_inverse * np.sqrt(
            np.mean((calculated_battery_OCV_d_in - OCV_battery_d_in) ** 2))
    return RMSD


def perform_optimization(cathode_number, cathode_info, anode_number,
                         anode_info, OCV_battery, SOC_battery, battery,
                         derivative_inverse):
    """
    Perform optimization for a specific cathode and anode combination.

    Parameters:
    - cathode_number: int
        Identifier for the cathode data.
    - cathode_info: dict
        Information about the cathode,
        including interpolated function and x values.
    - anode_number: int
        Identifier for the anode data.
    - anode_info: dict
        Information about the anode,
        including interpolated function and x values.
    - OCV_battery: array-like
        Measured battery open-circuit voltage (OCV).
    - SOC_battery: array-like
        State of charge (SOC) values for the battery.

    Returns:
    - optimization_results: dict
        Dictionary containing optimization results,
        including cathode and anode data IDs,
        optimized parameters, and RMSD (Root Mean Square Deviation).
    """
    cathode_interp = cathode_info['interpolated_function']
    cathode_x_values = cathode_info['x_values']

    anode_interp = anode_info['interpolated_function']
    anode_x_values = anode_info['x_values']

    bounds = [(0, 1), (0, 1), (0, 1), (0, 1)]

    battery = battery
    derivative_inverse = derivative_inverse

    opt_result = differential_evolution(
        lambda params: optimization(params, anode_interp, anode_x_values,
                                    cathode_interp, cathode_x_values,
                                    OCV_battery, SOC_battery, battery=battery,
                                    derivative_inverse=derivative_inverse),
        bounds
    )
    optimized_params = opt_result.x
    RMSD_opt = opt_result.fun

    return {
        'cathode_data_ID': cathode_number,
        'anode_data_ID': anode_number,
        'optimized_params': optimized_params,
        'RMSD': RMSD_opt
    }


def perform_full_optimization_parallel(SOC_battery, OCV_battery,
                                       interpolated_cathodes,
                                       interpolated_anodes, iterations=5,
                                       battery=1, derivative_inverse=0):
    """
    Perform parallelized full optimization for multiple iterations
    and find the overall best optimization result.

    Parameters:
    - SOC_battery: array-like
        State of charge (SOC) values for the battery.
    - OCV_battery: array-like
        Measured battery open-circuit voltage (OCV).
    - interpolated_cathodes: dict
        Dictionary containing information about interpolated cathode functions.
    - interpolated_anodes: dict
        Dictionary containing information about interpolated anode functions.
    - iterations: int, optional
        Number of iterations for optimization.
    - battery, derivative_inverse: float, optional
        Weighting factors for different components of the objective function.

    Returns:
    - result: dict
        Dictionary containing optimization results and plots.
    """
    best_optimization_results = []

    for iteration in range(iterations):
        optimization_results = []

        def optimize_single_case(
                cathode_number, cathode_info, anode_number, anode_info):
            return perform_optimization(cathode_number, cathode_info,
                                        anode_number, anode_info, OCV_battery,
                                        SOC_battery, battery,
                                        derivative_inverse)

        optimization_results = Parallel(n_jobs=-1)(
            delayed(optimize_single_case)(cathode_number, cathode_info,
                                          anode_number, anode_info)
            for cathode_number, cathode_info in interpolated_cathodes.items()
            for anode_number, anode_info in interpolated_anodes.items()
        )

        best_optimization_result = min(
            optimization_results, key=lambda x: x['RMSD'])
        best_optimization_results.append(best_optimization_result)

    best_optimization_result = min(
        best_optimization_results, key=lambda x: x['RMSD'])

    best_cathode_data_ID = best_optimization_result['cathode_data_ID']
    best_anode_data_ID = best_optimization_result['anode_data_ID']

    Best_Cathode = interpolated_cathodes.get(best_cathode_data_ID)
    Best_Anode = interpolated_anodes.get(best_anode_data_ID)

    if Best_Cathode is not None and Best_Anode is not None:
        e_percentage_opt, f_percentage_opt, g_percentage_opt, \
            h_percentage_opt = best_optimization_result['optimized_params']
        e_opt = int(e_percentage_opt * len(Best_Anode['x_values']) * 0.3)
        f_opt = len(Best_Anode['x_values']) - \
            int(f_percentage_opt * len(Best_Anode['x_values']) * 0.3)
        g_opt = int(g_percentage_opt * len(Best_Cathode['x_values']) * 0.15)
        h_opt = len(Best_Cathode['x_values']) - \
            int(h_percentage_opt * len(Best_Cathode['x_values']) * 0.15)
        best_parameters = e_opt, f_opt, g_opt, h_opt

        v1 = Best_Anode['interpolated_function'](Best_Anode['x_values'])
        axv_opt = Best_Anode['x_values']
        w1 = interp1d(
            axv_opt[e_opt:f_opt], v1[e_opt:f_opt],
            kind='cubic', fill_value='extrapolate')
        w1_ns = interp1d(
            axv_opt, v1,
            kind='cubic', fill_value='extrapolate')
        x_a1 = np.linspace(
            axv_opt[e_opt:f_opt][0], axv_opt[e_opt:f_opt][-1], 1001)
        x_a1_ns = np.linspace(
            axv_opt[0], axv_opt[-1], 1001+e_opt+(1001-f_opt))
        q1 = Best_Cathode['interpolated_function'](Best_Cathode['x_values'])
        cxv_opt = Best_Cathode['x_values']
        r1 = interp1d(
            cxv_opt[g_opt:h_opt], q1[g_opt:h_opt],
            kind='cubic', fill_value='extrapolate')
        r1_ns = interp1d(
            cxv_opt, q1,
            kind='cubic', fill_value='extrapolate')
        x_c1 = np.linspace(
            cxv_opt[g_opt:h_opt][0], cxv_opt[g_opt:h_opt][-1], 1001)
        x_c1_ns = np.linspace(
            cxv_opt[0], cxv_opt[-1], 1001+g_opt+(1001-h_opt))

        calculated_battery_OCV_opt = r1(x_c1) - w1(x_a1)

        cscalesoc = x_c1 - min(x_c1)
        c_SOC = cscalesoc / max(cscalesoc)

        cfullscalesoc = x_c1_ns - min(x_c1)
        c_SOC_full = cfullscalesoc / max(cscalesoc)
        ascalesoc = x_a1 - min(x_a1)
        a_SOC = ascalesoc / max(ascalesoc)

        afullscalesoc = x_a1_ns - min(x_a1)
        a_SOC_full = afullscalesoc / max(ascalesoc)

    result = {
        'Best Cathode Data ID': best_cathode_data_ID,
        'Best Anode Data ID': best_anode_data_ID,
        'Best Parameters': best_parameters,
        'Lowest RMSD': best_optimization_result['RMSD'],
        'SOC_battery': SOC_battery,
        'OCV_battery': OCV_battery,
        'calculated_battery_OCV_opt': calculated_battery_OCV_opt,
        'c_SOC_full': c_SOC_full,
        'r1_ns_x_c1_ns': r1_ns(x_c1_ns),
        'c_SOC': c_SOC,
        'r1_x_c1': r1(x_c1),
        'a_SOC_full': a_SOC_full,
        'w1_ns_x_a1_ns': w1_ns(x_a1_ns),
        'a_SOC': a_SOC,
        'w1_x_a1': w1(x_a1)
    }

    return result


def perform_full_optimization_parallel_to_json_GUI(filename, SOC_battery,
                                                   OCV_battery,
                                                   interpolated_cathodes,
                                                   interpolated_anodes,
                                                   iterations=5,
                                                   battery=1,
                                                   derivative_inverse=0):
    """
    Perform parallelized full optimization for multiple iterations
    and find the overall best optimization result.

    Parameters:
    - filename: str
        Name of the JSON file to write the results.
    - SOC_battery: array-like
        State of charge (SOC) values for the battery.
    - OCV_battery: array-like
        Measured battery open-circuit voltage (OCV).
    - interpolated_cathodes: dict
        Dictionary containing information about interpolated cathode functions.
    - interpolated_anodes: dict
        Dictionary containing information about interpolated anode functions.
    - iterations: int, optional
        Number of iterations for optimization.
    - battery, derivative_inverse: float, optional
        Weighting factors for different components of the objective function.

    Returns:
    None
    """
    best_optimization_results = []

    for iteration in range(iterations):
        optimization_results = []

        def optimize_single_case(
                cathode_number, cathode_info, anode_number, anode_info):
            return perform_optimization(cathode_number, cathode_info,
                                        anode_number, anode_info, OCV_battery,
                                        SOC_battery, battery,
                                        derivative_inverse)

        optimization_results = Parallel(n_jobs=-1)(
            delayed(optimize_single_case)(cathode_number, cathode_info,
                                          anode_number, anode_info)
            for cathode_number, cathode_info in interpolated_cathodes.items()
            for anode_number, anode_info in interpolated_anodes.items()
        )

        best_optimization_result = min(
            optimization_results, key=lambda x: x['RMSD'])
        best_optimization_results.append(best_optimization_result)

    best_optimization_result = min(
        best_optimization_results, key=lambda x: x['RMSD'])

    best_cathode_data_ID = best_optimization_result['cathode_data_ID']
    best_anode_data_ID = best_optimization_result['anode_data_ID']

    Best_Cathode = interpolated_cathodes.get(best_cathode_data_ID)
    Best_Anode = interpolated_anodes.get(best_anode_data_ID)

    if Best_Cathode is not None and Best_Anode is not None:
        e_percentage_opt, f_percentage_opt, g_percentage_opt, \
            h_percentage_opt = best_optimization_result['optimized_params']
        e_opt = int(e_percentage_opt * len(Best_Anode['x_values']) * 0.3)
        f_opt = len(Best_Anode['x_values']) - \
            int(f_percentage_opt * len(Best_Anode['x_values']) * 0.3)
        g_opt = int(g_percentage_opt * len(Best_Cathode['x_values']) * 0.15)
        h_opt = len(Best_Cathode['x_values']) - \
            int(h_percentage_opt * len(Best_Cathode['x_values']) * 0.15)
        best_parameters = e_opt, f_opt, g_opt, h_opt

        v1 = Best_Anode['interpolated_function'](Best_Anode['x_values'])
        axv_opt = Best_Anode['x_values']
        w1 = interp1d(
            axv_opt[e_opt:f_opt], v1[e_opt:f_opt],
            kind='cubic', fill_value='extrapolate')
        w1_ns = interp1d(
            axv_opt, v1,
            kind='cubic', fill_value='extrapolate')
        x_a1 = np.linspace(
            axv_opt[e_opt:f_opt][0], axv_opt[e_opt:f_opt][-1], 1001)
        x_a1_ns = np.linspace(
            axv_opt[0], axv_opt[-1], 1001+e_opt+(1001-f_opt))
        q1 = Best_Cathode['interpolated_function'](Best_Cathode['x_values'])
        cxv_opt = Best_Cathode['x_values']
        r1 = interp1d(
            cxv_opt[g_opt:h_opt], q1[g_opt:h_opt],
            kind='cubic', fill_value='extrapolate')
        r1_ns = interp1d(
            cxv_opt, q1,
            kind='cubic', fill_value='extrapolate')
        x_c1 = np.linspace(
            cxv_opt[g_opt:h_opt][0], cxv_opt[g_opt:h_opt][-1], 1001)
        x_c1_ns = np.linspace(
            cxv_opt[0], cxv_opt[-1], 1001+g_opt+(1001-h_opt))

        calculated_battery_OCV_opt = r1(x_c1) - w1(x_a1)

        cscalesoc = x_c1 - min(x_c1)
        c_SOC = cscalesoc / max(cscalesoc)

        cfullscalesoc = x_c1_ns - min(x_c1)
        c_SOC_full = cfullscalesoc / max(cscalesoc)
        ascalesoc = x_a1 - min(x_a1)
        a_SOC = ascalesoc / max(ascalesoc)

        afullscalesoc = x_a1_ns - min(x_a1)
        a_SOC_full = afullscalesoc / max(ascalesoc)

    # Convert NumPy arrays to Python lists
    SOC_battery_list = SOC_battery.tolist()
    OCV_battery_list = OCV_battery.tolist()
    calculated_battery_OCV_opt_list = calculated_battery_OCV_opt.tolist()
    c_SOC_full_list = c_SOC_full.tolist()
    r1_ns_x_c1_ns_list = r1_ns(x_c1_ns).tolist()
    c_SOC_list = c_SOC.tolist()
    r1_x_c1_list = r1(x_c1).tolist()
    a_SOC_full_list = a_SOC_full.tolist()
    w1_ns_x_a1_ns_list = w1_ns(x_a1_ns).tolist()
    a_SOC_list = a_SOC.tolist()
    w1_x_a1_list = w1(x_a1).tolist()

    result = {
        'Best Cathode Data ID': best_cathode_data_ID,
        'Best Anode Data ID': best_anode_data_ID,
        'Best Parameters': best_parameters,
        'Lowest RMSD': best_optimization_result['RMSD'],
        'Battery SOC': SOC_battery_list,
        'Battery OCV': OCV_battery_list,
        'Calculated Battery OCV': calculated_battery_OCV_opt_list,
        'Cathode SOC full': c_SOC_full_list,
        'Cathode OCP full': r1_ns_x_c1_ns_list,
        'Cathode SOC': c_SOC_list,
        'Cathode OCP': r1_x_c1_list,
        'Anode SOC full': a_SOC_full_list,
        'Anode OCP full': w1_ns_x_a1_ns_list,
        'Anode SOC': a_SOC_list,
        'Anode OCP': w1_x_a1_list
    }

    with open(filename, 'w') as f:
        json.dump(result, f)


def perform_full_optimization_parallel_to_json(filename, file_location,
                                               SOC_battery,
                                               OCV_battery,
                                               interpolated_cathodes,
                                               interpolated_anodes,
                                               iterations=5,
                                               battery=1,
                                               derivative_inverse=0):
    """
    Perform parallelized full optimization for multiple iterations
    and find the overall best optimization result.

    Parameters:
    - filename: str
        Name of the JSON file to write the results.
    - file_location: str
        Location where the JSON file will be saved.
    - SOC_battery: array-like
        State of charge (SOC) values for the battery.
    - OCV_battery: array-like
        Measured battery open-circuit voltage (OCV).
    - interpolated_cathodes: dict
        Dictionary containing information about interpolated cathode functions.
    - interpolated_anodes: dict
        Dictionary containing information about interpolated anode functions.
    - iterations: int, optional
        Number of iterations for optimization.
    - battery, derivative_inverse: float, optional
        Weighting factors for different components of the objective function.

    Returns:
    None
    """
    best_optimization_results = []

    for iteration in range(iterations):
        optimization_results = []

        def optimize_single_case(
                cathode_number, cathode_info, anode_number, anode_info):
            return perform_optimization(cathode_number, cathode_info,
                                        anode_number, anode_info, OCV_battery,
                                        SOC_battery, battery,
                                        derivative_inverse)

        optimization_results = Parallel(n_jobs=-1)(
            delayed(optimize_single_case)(cathode_number, cathode_info,
                                          anode_number, anode_info)
            for cathode_number, cathode_info in interpolated_cathodes.items()
            for anode_number, anode_info in interpolated_anodes.items()
        )

        best_optimization_result = min(
            optimization_results, key=lambda x: x['RMSD'])
        best_optimization_results.append(best_optimization_result)

    best_optimization_result = min(
        best_optimization_results, key=lambda x: x['RMSD'])

    best_cathode_data_ID = best_optimization_result['cathode_data_ID']
    best_anode_data_ID = best_optimization_result['anode_data_ID']

    Best_Cathode = interpolated_cathodes.get(best_cathode_data_ID)
    Best_Anode = interpolated_anodes.get(best_anode_data_ID)

    if Best_Cathode is not None and Best_Anode is not None:
        e_percentage_opt, f_percentage_opt, g_percentage_opt, \
            h_percentage_opt = best_optimization_result['optimized_params']
        e_opt = int(e_percentage_opt * len(Best_Anode['x_values']) * 0.3)
        f_opt = len(Best_Anode['x_values']) - \
            int(f_percentage_opt * len(Best_Anode['x_values']) * 0.3)
        g_opt = int(g_percentage_opt * len(Best_Cathode['x_values']) * 0.15)
        h_opt = len(Best_Cathode['x_values']) - \
            int(h_percentage_opt * len(Best_Cathode['x_values']) * 0.15)
        best_parameters = e_opt, f_opt, g_opt, h_opt

        v1 = Best_Anode['interpolated_function'](Best_Anode['x_values'])
        axv_opt = Best_Anode['x_values']
        w1 = interp1d(
            axv_opt[e_opt:f_opt], v1[e_opt:f_opt],
            kind='cubic', fill_value='extrapolate')
        w1_ns = interp1d(
            axv_opt, v1,
            kind='cubic', fill_value='extrapolate')
        x_a1 = np.linspace(
            axv_opt[e_opt:f_opt][0], axv_opt[e_opt:f_opt][-1], 1001)
        x_a1_ns = np.linspace(
            axv_opt[0], axv_opt[-1], 1001+e_opt+(1001-f_opt))
        q1 = Best_Cathode['interpolated_function'](Best_Cathode['x_values'])
        cxv_opt = Best_Cathode['x_values']
        r1 = interp1d(
            cxv_opt[g_opt:h_opt], q1[g_opt:h_opt],
            kind='cubic', fill_value='extrapolate')
        r1_ns = interp1d(
            cxv_opt, q1,
            kind='cubic', fill_value='extrapolate')
        x_c1 = np.linspace(
            cxv_opt[g_opt:h_opt][0], cxv_opt[g_opt:h_opt][-1], 1001)
        x_c1_ns = np.linspace(
            cxv_opt[0], cxv_opt[-1], 1001+g_opt+(1001-h_opt))

        calculated_battery_OCV_opt = r1(x_c1) - w1(x_a1)

        cscalesoc = x_c1 - min(x_c1)
        c_SOC = cscalesoc / max(cscalesoc)

        cfullscalesoc = x_c1_ns - min(x_c1)
        c_SOC_full = cfullscalesoc / max(cscalesoc)
        ascalesoc = x_a1 - min(x_a1)
        a_SOC = ascalesoc / max(ascalesoc)

        afullscalesoc = x_a1_ns - min(x_a1)
        a_SOC_full = afullscalesoc / max(ascalesoc)

    # Convert NumPy arrays to Python lists
    SOC_battery_list = SOC_battery.tolist()
    OCV_battery_list = OCV_battery.tolist()
    calculated_battery_OCV_opt_list = calculated_battery_OCV_opt.tolist()
    c_SOC_full_list = c_SOC_full.tolist()
    r1_ns_x_c1_ns_list = r1_ns(x_c1_ns).tolist()
    c_SOC_list = c_SOC.tolist()
    r1_x_c1_list = r1(x_c1).tolist()
    a_SOC_full_list = a_SOC_full.tolist()
    w1_ns_x_a1_ns_list = w1_ns(x_a1_ns).tolist()
    a_SOC_list = a_SOC.tolist()
    w1_x_a1_list = w1(x_a1).tolist()

    result = {
        'Best Cathode Data ID': best_cathode_data_ID,
        'Best Anode Data ID': best_anode_data_ID,
        'Best Parameters': best_parameters,
        'Lowest RMSD': best_optimization_result['RMSD'],
        'SOC_battery': SOC_battery_list,
        'OCV_battery': OCV_battery_list,
        'calculated_battery_OCV_opt': calculated_battery_OCV_opt_list,
        'c_SOC_full': c_SOC_full_list,
        'r1_ns_x_c1_ns': r1_ns_x_c1_ns_list,
        'c_SOC': c_SOC_list,
        'r1_x_c1': r1_x_c1_list,
        'a_SOC_full': a_SOC_full_list,
        'w1_ns_x_a1_ns': w1_ns_x_a1_ns_list,
        'a_SOC': a_SOC_list,
        'w1_x_a1': w1_x_a1_list
    }

    with open(file_location + '/' + filename, 'w') as f:
        json.dump(result, f)
