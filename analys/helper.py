
import os
import pickle
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


def analyze_system_response(file_data, config):
    
    
    ############################
    ### PLOT CONFIG ############
    ############################

    # config['']
    # DATA_FOLDER, folder, file, save_image=True, overwrite=False

    # plot_step_time       = True
    # plot_overshoot       = False
    # plot_settling_time   = False
    # print_stats          = False
    # type_of_test     =  DATA_FOLDER.split("\\")[-1]
    # output_folder    = f'output/{type_of_test}/{folder}'
    # output_file_name = file.split(".")[0]
    
    
    output_folder = config['output_folder']
    output_file_name   = config['output_file_name']

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
        overshoot_idx   = np.argmax(steering_actual[steering_actual_after_step_idx:])
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
    overshoot_time = steering_actual_time[steering_actual_after_step_idx+overshoot_idx]

    # Add vertical lines for the 10% and 90% step times
    if config['plot_step_time']:
        ax.axvline(x=time_10_percent, color='r', linestyle='--', label='10% Step Time', alpha=0.5)
        ax.axvline(x=time_90_percent, color='g', linestyle='--', label='90% Step Time', alpha=0.5)

    # Plot the overshoot
    if config['plot_overshoot']:
        ax.plot(overshoot_time, overshoot_value, 'xr', label='Overshoot Point')
        ax.axhline(overshoot_value, linestyle=':', color='b', alpha=0.5)

    # Step 3: 
    # Define the settling percentage (commonly 2% or 5%)
    settling_percentage = 0.05  # 5% settling

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

    if config['plot_settling_time'] and settling_time != None:
        ax.axhline(y=settling_upper_bound, color='c', linestyle='--', label=f'{settling_percentage*100} % Bound', alpha=0.5)
        ax.axhline(y=settling_lower_bound, color='c', linestyle='--', alpha=0.5)
        ax.axvline(x=settling_time_abs, color='r', linestyle='--', label=f'{settling_percentage*100} % Settling Time', alpha=0.5)
        
    # Calculate the difference array
    steering_difference = np.diff(steering_actual)

    # Calculate the variance of the difference array
    steering_variance = np.var(steering_difference)

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
        'settling_percentage': settling_percentage,
        'steering_variance'  : steering_variance
    }

    if config['print_stats']:
        pprint.pprint(response_char)

    folder = output_folder.split("\\")[-1]
    ax.set_title(f'{folder} | {output_file_name}')
    ax.legend(loc='best')

    # Create folders, the entire path
    if config['save_image']:

        if not os.path.exists(output_folder):
            os.makedirs(output_folder, exist_ok=True)

        # Save the plot to disk as an image file (PNG, JPG, SVG, etc.)
        output_filepath_png  = f'{output_folder}/{output_file_name}.png'
        if not os.path.exists(output_filepath_png) or config['overwrite']:
            plt.savefig(output_filepath_png, dpi=500)
            
        output_filepath_json  = f'{output_folder}/{output_file_name}.json'
        with open(output_filepath_json, 'w', encoding='utf-8') as f:
            json.dump(response_char, f, indent=4)

            
    if config['visual_mode']:
        plt.show()       
        

    # Close the plot to release resources
    plt.close(fig)
    
    return response_char


def calculate_response_avg(response_char_list, topics_to_sum, DATA_FOLDER, folder, verbose=False):
    
    type_of_test     =  DATA_FOLDER.split("\\")[-1]
    output_folder    = f'output/{type_of_test}/{folder}'

    if not os.path.exists(output_folder):
        os.makedirs(output_folder, exist_ok=True)
        print(f"Creating folder: {output_folder}")
    
    output_filepath  = f'{output_folder}/sum.json'
    
    # Create a pandas DataFrame from the list of dictionaries
    df = pd.DataFrame(response_char_list)

    # Calculate the sum while ignoring NaN values
    sums = df[topics_to_sum].sum(skipna=True)

    # Calculate the average by dividing the sums by the number of non-NaN values in each column

    try:
        averages = sums / df[topics_to_sum].notna().sum()
    except Exception as e:
        
        print(f'Error: {e} | folder: {folder}')
        
        print(df)
        print(df[topics_to_sum].notna())
        averages_dict = {'ERROR': e}
        return averages_dict
    
    if verbose:
        print(averages)
    
    # Convert the pandas Series to a dictionary
    averages_dict = averages.to_dict()
    # Save the dictionary as a JSON file
    with open(output_filepath, 'w') as json_file:
        json.dump(averages_dict, json_file, indent=4)

    return averages



def generate_matrix(data, matrix_config):
    output_folder = matrix_config['output_folder']
    if not os.path.exists(output_folder):
        os.makedirs(output_folder, exist_ok=True)
        print(f"Creating folder: {output_folder}")
    
    # Extract unique values for stm and dspace
    y_values = sorted(set(int(key.split('_')[1]) for key in data.keys()))
    x_values = sorted(set(int(key.split('_')[3]) for key in data.keys()))

    # Create an empty 3D matrix
    matrix = np.zeros((len(y_values), len(x_values), 4))

    # Populate the matrix
    for key, df in data.items():
        y__idx, x__idx = [int(val) for val in key.split('_')[1::2]]
        x_pos = x_values.index(x__idx)
        y_pos = y_values.index(y__idx)
        
        overshoot_percentage = (df['overshoot'] - 1) * 100  # Convert overshoot to percentage
        matrix[y_pos, x_pos, :] = [df['rise_time'], overshoot_percentage, df['settling_time'], df['steering_variance']]
    
    if matrix_config['test_type'] == 'Prioritity':
        x_values = [f"{value} %" for value in x_values]
        y_values = [f"{value} %" for value in y_values]

    fig, axes = plt.subplots(nrows=2, ncols=2, figsize=(14, 14))
    
    for i,x in enumerate(matrix_config['bar_labels']):
        
        ix, iy = np.unravel_index(i, (2, 2))
        
        # Choose the metric you want to plot: 0 - rise_time, 1 - overshoot, 2 - settling_time
        metric_to_plot = i
        bar_label = matrix_config['bar_labels'][metric_to_plot]

        # Plot the matrix using a color gradient
        # viridis, coolwarm
        img = axes[ix, iy].imshow(matrix[:, :, metric_to_plot], cmap='viridis', aspect='auto', vmin=0)

        # Set the ticks and labels for the x and y axes
        axes[ix, iy].set_xticks( np.array(range(len(x_values))) )
        axes[ix, iy].set_yticks( np.array(range(len(y_values))) )

        axes[ix, iy].set_xticklabels(x_values)
        axes[ix, iy].set_yticklabels(y_values)

        # Set the x and y axis labels
        x_label = f"{matrix_config['x_axis']} {matrix_config['test_type']}"
        y_label = f"{matrix_config['y_axis']} {matrix_config['test_type']}"
        title   = f"{matrix_config['bar_labels'][i]}"
        
        # Add custom label
        if matrix_config['test_type'] == 'Periodicity':
            x_label += " [ms]"
            y_label += " [ms]"
        if matrix_config['test_type'] == 'Priority':
            x_label += " %"
            y_label += " %"
        
        axes[ix, iy].set_xlabel(x_label)
        axes[ix, iy].set_ylabel(y_label)
        axes[ix, iy].set_title(title)

        # Invert the y-axis
        axes[ix, iy].invert_yaxis()

        # Add a colorbar to show the color scale
        cbar = plt.colorbar(img, ax=axes[ix, iy], label=bar_label)
        # cbar.ax.set_ylabel('Label text', fontsize=14, labelpad=-45, rotation=270)
        # cbar.ax.set_yticklabels(cbar.ax.get_yticklabels(), rotation=0, ha='left')
        
    plt.tight_layout()
        
    if matrix_config['save_image']:
        # Save the image
        output_filepath = f"{output_folder}\\matrix.png"
        plt.savefig(output_filepath, dpi=500)
    
    # Display the plot
    if matrix_config['visual_mode']:
        plt.show()
        
    # Close the plot to release resources
    plt.close(fig)
        
    return matrix



def calc_jitter(file_data, folder, matrix_config):

    split_folder  = folder.split("_")
    y_period    = 50
    x_period = int(split_folder[3])
    
    # The priority is not fixed!
    if matrix_config['test_type'] == 'Periodicity':
        y_period = int(split_folder[1])

    # Extract the 'steering_angle_2' values from the list of dictionaries
    time                    = file_data['dcu_status_steering_brake']['time']
    steering_angle_2_values = [entry['steering_angle_2'] for entry in file_data['dcu_status_steering_brake']['data']]

    # Convert the list of 'steering_angle_2'  values to a numpy array
    data = np.array(steering_angle_2_values)
    time = np.array(time)

    # Compute the differences between consecutive time values
    if matrix_config['test_type'] == 'Prioritity':
        time_diff = np.diff(time) * 1000 - y_period
    
    if matrix_config['test_type'] == 'Periodicity':
        time_diff = y_period - np.diff(time) * 1000

    return time_diff

def plot_jitter(jitter_data, matrix_config, rotation=45, plot_outliers=True):
    
    output_folder = matrix_config['output_folder']
    
    # Calculate JITTER
    comb_dict = {}
    comb_data = []
    labels =  []
    
    for k,x in enumerate(jitter_data):
        
        y__idx, x__idx = [int(val) for val in x.split('_')[1::2]]
        
        if 'key_mapping' in matrix_config:
            x__idx =  matrix_config['key_mapping']['x'][x__idx]
            y__idx =  matrix_config['key_mapping']['y'][y__idx]
        

        folder = f"{matrix_config['y_axis']}_{y__idx}_{matrix_config['x_axis']}_{x__idx}"
        
        if folder not in comb_dict:
            comb_dict[folder] = jitter_data[x]
        else:
            comb_dict[folder] = np.concatenate( (comb_dict[folder], jitter_data[x]) )  
            

    comb_dict = {key: comb_dict[key] for key in sorted(comb_dict)}
    for k,x in enumerate(comb_dict):
        
        # print(f"STD for {x} ms - {np.std(comb_dict[x])}")
        split_name = x.split("_")
        if matrix_config['test_type'] == 'Prioritity':
            label = f"{matrix_config['y_axis']}: {split_name[1]} % - {matrix_config['x_axis']}: {split_name[3]} %"
        else:
            label = f"{matrix_config['y_axis']}: {split_name[1]} - {matrix_config['x_axis']}: {split_name[3]}"
        
        comb_data.append(comb_dict[x])
        labels.append(label)


    # Create a boxplot of the data
    fig, ax = plt.subplots(figsize=(12, 6))
    if plot_outliers:
        ax.boxplot(comb_data)
    else:
        ax.boxplot(comb_data, sym='')

    # Set the title and labels
    ax.set_title(f"Jitter of STM - {matrix_config['test_type']}")
    ax.set_xticklabels(labels, rotation=rotation)
    ax.set_ylabel('Time delay [ms]')
    ax.set_xlabel(f"{matrix_config['test_type']} of {matrix_config['y_axis']} and {matrix_config['x_axis']}")
    
    plt.tight_layout()
    
    if matrix_config['save_image']:
        # Save the image
        output_filepath = f"{output_folder}\\jitter_plot.png"
        plt.savefig(output_filepath, dpi=500)
        
    # Display the plot
    if matrix_config['visual_mode']:
        plt.show()
        
    # Close the plot to release resources
    plt.close()
    

def list_files_recursively(path):
    all_files = []
    all
    for root, dirs, files in os.walk(path):
        for file in files:
            if '.pkl' in file:
                all_files.append(os.path.join(root, file))
    return all_files

def plot_step(selected_file_name, config):
    
    base_path = "C:\\Users\\carlv\\Documents\\carl\projects\\kex\\resultat\\CAN_RESPONSES"
    folders = ['periodicity', 'prioritity', 'tracking']
    files_dict = {}
    
    for folder in folders:
        new_folder = f"{base_path}\\{folder}"
        files = list_files_recursively(new_folder)
        for file in files:
            file_name = file.split("\\")[-1].split(".")[0]
            if file_name not in files_dict:
                files_dict[file_name] = file
                
    if selected_file_name not in files_dict:
        print("File does not exists!")
        return
    
    config['output_folder'] = ''
    config['output_file_name'] = selected_file_name
    
    with open(files_dict[selected_file_name], 'rb') as f:
        print(f"Loading: {selected_file_name}")
        file_data = pickle.load(f)
        analyze_system_response(file_data, config)
                
