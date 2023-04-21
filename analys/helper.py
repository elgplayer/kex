
import os
import pprint
import json

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt


# Initialize an empty dictionary to store the key lists
def gather_data(_dict, message_of_interest):
    '''
    Get a message data recorded from a CAN file
    '''
    key_lists = {}
    
    # Iterate through the list of dictionaries
    for entry in _dict[message_of_interest]['data']:
        
        # Iterate through each key-value pair in the current dictionary
        for key, value in entry.items():
            
            # If the key is not in the key_lists dictionary, create a new list for it
            if key not in key_lists:
                key_lists[key] = []
            
            # Append the value to the appropriate key list
            key_lists[key].append(value)
    
    # Convert it as numpy array
    x = np.array(_dict[message_of_interest]['time'])
    y = key_lists
            
    return x,y


def convert_range(input_array):
    '''
    Convert the CAN readings to degrees!
    '''
    old_min = -2024
    old_max = 2024
    new_min = -90
    new_max = 90
    
    return new_min + (input_array - old_min) * (new_max - new_min) / (old_max - old_min)


def plot_at_same_time_axis(t, t_dv_driving_dynamics_1, steering_actual, steering_target):
    '''
    Plot at same time axis
    '''
    
    combined_time = np.unique(np.concatenate((t, t_dv_driving_dynamics_1)))
    # Interpolate data1 and data2 at the combined time points
    interp_data1 = np.interp(combined_time, t, steering_actual)
    interp_data2 = np.interp(combined_time, t_dv_driving_dynamics_1, steering_target)

    fig, ax = plt.subplots()
    fig.set_size_inches(10, 8)
    # Plot the interpolated data on the same plot
    ax.plot(combined_time, interp_data1, linestyle='-', markersize=2, label="Steering Actual")
    ax.plot(combined_time, interp_data2, label="Steering Target", alpha=0.5)

    ax.set_xlabel("Time [s]")
    ax.set_ylabel("Steering angle [°]")
    ax.legend(loc='best')
    # Display the plot
    ax.grid()
    
    # plt.grid()
    return fig, ax


def analyze_system_response(file_data, DATA_FOLDER, folder, file, save_image=True):
    
    
    ############################
    ### PLOT CONFIG ############
    ############################

    plot_step_time       = False
    plot_overshoot       = False
    plot_settling_time   = False
    print_stats          = False

    ############################
    ############################
    ############################
    
    # Get the steering position from the DCU
    message_of_interest = 'dcu_status_steering_brake'
    t_dcu_status_steering_brake, data_dcu_status_steering_brake = gather_data(file_data, message_of_interest)
    init_val = t_dcu_status_steering_brake[0]
    t_dcu_status_steering_brake = t_dcu_status_steering_brake - t_dcu_status_steering_brake[0] # Make the time reference start from the first message

    # We want to see when the step is
    message_of_interest = 'dv_driving_dynamics_1'
    t_dv_driving_dynamics_1, data_dv_driving_dynamics_1 = gather_data(file_data, message_of_interest)
    t_dv_driving_dynamics_1 = t_dv_driving_dynamics_1 - init_val # Make the time reference start from the first message

    # Combine the two to one time axis
    steering_actual_time = t_dcu_status_steering_brake
    steering_target_time = t_dv_driving_dynamics_1
    combined_time        = np.unique(np.concatenate((t_dcu_status_steering_brake, t_dv_driving_dynamics_1)))
    steering_actual      = convert_range(np.array(data_dcu_status_steering_brake['steering_angle_2']))
    steering_target      = np.array(data_dv_driving_dynamics_1['steering_angle_target']) / 2 # Scaling is wrong


    # TODO:
    # Maybe remove the settling of the initial response at the beginning
    # Cut off off the data when it does not comply with lets 
    # say a 5% settling band before the step.

    # Plotting
    fig, ax = plot_at_same_time_axis(t_dcu_status_steering_brake, t_dv_driving_dynamics_1, steering_actual, steering_target)

    response_char = {}
    step_time_idx = np.argmax(np.diff(steering_target) > 0)
    step_time     = steering_target_time[step_time_idx]
    initial_value = steering_target[step_time_idx-1]
    target        = steering_target[-1]

    # TODO
    # Maybe do smoothing or something similiar...
    # Now we are picking the last value before the step
    steering_actual_before_step_idx = np.argmin(steering_actual_time < steering_target_time[step_time_idx]) - 1
    steering_actual_before_step     = steering_actual[steering_actual_before_step_idx]
    steering_actual_after_step_idx  = np.argmax(steering_actual_time > step_time)
    

    # Determine the steady-state error (SSE)
    SSE = steering_actual_before_step - initial_value

    # Calculate the final value after the step
    final_value = target - initial_value

    # Calculate the 10% and 90% values
    value_10_percent = initial_value + SSE + 0.1 * (final_value - (initial_value + SSE))
    value_90_percent = initial_value + SSE + 0.9 * (final_value - (0 + SSE))

    # Identify the time it takes to reach the 10% and 90% values
    time_10_percent = np.interp(value_10_percent, steering_actual[steering_actual_after_step_idx:], steering_actual_time[steering_actual_after_step_idx:])
    time_90_percent = np.interp(value_90_percent, steering_actual[steering_actual_after_step_idx:], steering_actual_time[steering_actual_after_step_idx:])

    # Calculate the rise time
    rise_time = time_90_percent - time_10_percent

    # Step 2: Calculate overshoot
    overshoot       = 0
    overshoot_value = 0
    overshoot_idx   = 0
    overshoot_time  = 0

    if target > 0:
        overshoot_value = np.max(steering_actual[steering_actual_after_step_idx:])
        overshoot_idx   = np.argmax(overshoot_value == steering_actual)
    elif target == 0:
        # Aviod divison by zero
        print("Invalid target!")
        target = 1

    overshoot = (overshoot_value / target)
    # Set to zero if we don't have a overshoot
    if overshoot < 0:
        overshoot       = 0
        overshoot_value = 0
    overshoot_print = str(round((overshoot - 1) * 100,2)) + " %"
    overshoot_time = steering_actual_time[overshoot_idx]

    # Add vertical lines for the 10% and 90% step times
    if plot_step_time:
        ax.axvline(x=time_10_percent, color='r', linestyle='--', label='10% Step Time', alpha=0.5)
        ax.axvline(x=time_90_percent, color='g', linestyle='--', label='90% Step Time', alpha=0.5)

    # Plot the overshoot
    if plot_overshoot:
        ax.plot(overshoot_time, overshoot_value, 'xr', label='Overshoot Point')
        ax.axhline(overshoot_value, linestyle=':', color='b', alpha=0.5)

    # Step 3: 
    # Define the settling percentage (commonly 2% or 5%)
    settling_percentage = 0.5  # 5% settling

    # Calculate the settling range
    settling_upper_bound = target * (1 + settling_percentage)
    settling_lower_bound = target * (1 - settling_percentage)

    # Identify the time it takes to reach the settling range and stay within it
    settling_time = None
    for t, actual in zip(steering_actual_time[steering_actual_after_step_idx:], steering_actual[steering_actual_after_step_idx:]):
        if settling_lower_bound <= actual <= settling_upper_bound:
            if settling_time is None:
                settling_time_abs = t
                settling_time = t - steering_target_time[step_time_idx]
        else:
            settling_time = None

    if plot_settling_time and settling_time != None:
        ax.axhline(y=settling_upper_bound, color='c', linestyle='--', label=f'{settling_percentage*100} % Bound', alpha=0.5)
        ax.axhline(y=settling_lower_bound, color='c', linestyle='--', alpha=0.5)
        ax.axvline(x=settling_time_abs, color='r', linestyle='--', label=f'{settling_percentage*100} % Settling Time', alpha=0.5)

    response_char = {    
        'target'             : target,
        'rise_time'          : rise_time,
        'time_10_percent'    : time_10_percent,
        'time_90_percent'    : time_90_percent,
        'overshoot'          : overshoot,
        'overshoot_value'    : overshoot_value,
        'overshoot_print'    : overshoot_print,
        'overshoot_time'     : overshoot_time,
        'settling_time'      : settling_time,
        'settling_percentage': settling_percentage
    }

    if print_stats:
        pprint.pprint(response_char)

    ax.set_title(f'{folder} | {file}')
    ax.legend(loc='best')

    type_of_test     =  DATA_FOLDER.split("\\")[-1]
    output_folder    = f'output/{type_of_test}/{folder}'
    output_file_name = file.split(".")[0]

    # Create folders, the entire path
    if not os.path.exists(output_folder):
        os.makedirs(output_folder, exist_ok=True)

    if save_image:

        # Save the plot to disk as an image file (PNG, JPG, SVG, etc.)
        output_filepath_png  = f'{output_folder}/{output_file_name}.png'

        # Save the image
        plt.savefig(output_filepath_png, dpi=500)
        
        output_filepath_json  = f'{output_folder}/{output_file_name}.json'
        with open(output_filepath_json, 'w', encoding='utf-8') as f:
            json.dump(response_char, f, indent=4)

    # Close the plot to release resources
    plt.close(fig)
    
    return response_char


def calculate_response_avg(response_char_list, DATA_FOLDER, folder, print=False):
    
    
    type_of_test     =  DATA_FOLDER.split("\\")[-1]
    output_folder    = f'output/{type_of_test}/{folder}'
    output_filepath  = f'{output_folder}/sum.json'
    
    topics_to_sum = ['rise_time', 'overshoot', 'settling_time']

    # Create a pandas DataFrame from the list of dictionaries
    df = pd.DataFrame(response_char_list)

    # Select the columns to sum
    topics_to_sum = ['rise_time', 'overshoot', 'settling_time']

    # Calculate the sum while ignoring NaN values
    sums = df[topics_to_sum].sum(skipna=True)

    # Calculate the average by dividing the sums by the number of non-NaN values in each column

    try:
        averages = sums / df[topics_to_sum].notna().sum()
    except Exception as e:
        print(f'Error: {e} | folder: {folder}')
        averages_dict = {'ERROR': e}
        return averages_dict
    
    if print:
        print(averages)
    
    # Convert the pandas Series to a dictionary
    averages_dict = averages.to_dict()

    # Save the dictionary as a JSON file
    with open(output_filepath, 'w') as json_file:
        json.dump(averages_dict, json_file, indent=4)

    return averages


def generate_periodicity_matrix(full_data, output_folder, generate_figure=True, visual_mode=False):
    
    if not os.path.exists(output_folder):
        os.makedirs(output_folder, exist_ok=True)
    
    # Extract unique values for stm and dspace
    stm_values = sorted(set(int(key.split('_')[1]) for key in full_data.keys()))
    dspace_values = sorted(set(int(key.split('_')[3]) for key in full_data.keys()))

    # Create an empty 3D matrix
    matrix = np.zeros((len(stm_values), len(dspace_values), 3))

    # Populate the matrix
    for key, df in full_data.items():
        stm_idx, dspace_idx = [int(val) for val in key.split('_')[1::2]]
        stm_pos = stm_values.index(stm_idx)
        dspace_pos = dspace_values.index(dspace_idx)
        
        overshoot_percentage = (df['overshoot'] - 1) * 100  # Convert overshoot to percentage
        matrix[stm_pos, dspace_pos, :] = [df['rise_time'], overshoot_percentage, df['settling_time']]

    for i in range(0,3):
        
        # Choose the metric you want to plot: 0 - rise_time, 1 - overshoot, 2 - settling_time
        metric_to_plot = i

        # Plot the matrix using a color gradient
        # viridis, coolwarm
        plt.imshow(matrix[:, :, metric_to_plot], cmap='viridis', aspect='auto', vmin=0)

        # Set the ticks and labels for the x and y axes
        plt.xticks(range(len(dspace_values)), dspace_values)
        plt.yticks(range(len(stm_values)), stm_values)

        # Set the x and y axis labels
        plt.xlabel('dSPACE Periodicity [ms]')
        plt.ylabel('STM32 Periodicity [ms]')
        plt.title('Periodicity Matrix')

        # Invert the y-axis
        plt.gca().invert_yaxis()

        # Add a colorbar to show the color scale
        plt.colorbar(label='Overshoot [%]' if metric_to_plot == 1 else 'Rise time [s]' if metric_to_plot == 0 else 'Settling time [s]')

        # Display the plot
        if visual_mode:
            plt.show()
        else:
            # Save the image
            type_of_matrix = 'overshoot' if metric_to_plot == 1 else 'rise_time' if metric_to_plot == 0 else 'settling_time'
            output_filepath = f'{output_folder}\\{type_of_matrix}.png'
            plt.savefig(output_filepath, dpi=500)
            
        # Close the plot to release resources
        plt.close()
        
    return matrix