#%%
import time
import random
import asyncio
import pprint
import json
from io import StringIO
import decimal
import pickle
import os

import cantools
from canlib import canlib, Frame
import matplotlib as plt
import numpy as np
import matplotlib.pyplot as plt

################## 
# CONFIG #########
##################

use_last_CAN_RX_file = True

CAN_RX_name = 'CAN_RX_2023_04_13__08_01_58.pkl'
CAN_RX_dir = 'output/CAN_RESPONSES'
CAN_MESSAGES_path =  'output/messages_small.pkl'
DBC_path = 'src/can1.dbc'


##################


def get_latest_file(directory):
    # List all files in the directory
    all_files = [os.path.join(directory, f) for f in os.listdir(directory) if os.path.isfile(os.path.join(directory, f))]
    # Find the last modified file
    last_modified_file = max(all_files, key=os.path.getmtime).split("\\")[-1]
    return last_modified_file

if use_last_CAN_RX_file:
    CAN_RX_path = f'{CAN_RX_dir}/{get_latest_file(CAN_RX_dir)}'
    print(f"Loading latest CAN: {CAN_RX_path}")
else:
    CAN_RX_path = f'{CAN_RX_dir}/{CAN_RX_name}'
with open(CAN_RX_path, 'rb') as file:
    CAN_RX = pickle.load(file)

with open(CAN_MESSAGES_path, 'rb') as file:
    CAN_MESSAGES = pickle.load(file)

db = cantools.database.load_file(r"src/can1.dbc")
    
# pprint.pprint(CAN_RX, indent=4)
#%%

def analyze_system_response(target, output_data, time_data):
    # Step 1: Calculate step time
    step_time_10_idx = np.argmax(output_data >= 0.1 * target)
    step_time_10 = time_data[ste]
    step_time_90_idx = np.argmax(output_data >= 0.9 * target)
    step_time_90 = time_data[step_time_90_idx]

    # Step 2: Calculate overshoot
    overshoot = (max(output_data) / target) - 1

    # Step 3: Calculate oscillation
    output_data_after_step = output_data[step_time_90_idx:]
    target_crossings = np.where(np.diff(np.sign(output_data_after_step - target)))[0]
    oscillation = len(target_crossings)
    
    step_time = {
        'step_10': step_time_10,
        'step_90': step_time_90,
        'step_time': step_time_90 - step_time_10
    }

    return step_time, overshoot, oscillation


# Initialize an empty dictionary to store the key lists
def gather_data(message_of_interest):
    key_lists = {}
    # Iterate through the list of dictionaries
    for entry in CAN_RX[message_of_interest]['data']:
        # Iterate through each key-value pair in the current dictionary
        for key, value in entry.items():
            # If the key is not in the key_lists dictionary, create a new list for it
            if key not in key_lists:
                key_lists[key] = []
            # Append the value to the appropriate key list
            key_lists[key].append(value)
    x = CAN_RX[message_of_interest]['time']
    y = key_lists
            
    return x,y


def convert_to_angle(input_array):
    input_min = 0
    input_max = 2024
    output_min = -90.0
    output_max = 90.0

    output_array = ((input_array - input_min) / (input_max - input_min)) * (output_max - output_min) + output_min
    return output_array


def plot_at_same_time_axis(t, t_dv_driving_dynamics_1, steering_actual, steering_target):
    
    combined_time = np.unique(np.concatenate((t, t_dv_driving_dynamics_1)))
    # Interpolate data1 and data2 at the combined time points
    interp_data1 = np.interp(combined_time, t, steering_actual)
    interp_data2 = np.interp(combined_time, t_dv_driving_dynamics_1, steering_target)

    # Plot the interpolated data on the same plot
    plt.plot(combined_time, interp_data1, label="Steering Actual")
    plt.plot(combined_time, interp_data2, label="Steering Target")

    plt.xlabel("Time")
    plt.ylabel("Data")
    plt.legend()
    plt.grid()
    plt.show()

#######################
### PLOT CONFIG #######
#######################

plot_system_response = True
plot_step_time       = False
plot_overshoot       = False
plot_target          = False
print_stats          = False

######################
######################
######################

# Get the steering position from the DCU
message_of_interest = 'dcu_status_steering_brake'
t_dcu_status_steering_brake, data_dcu_status_steering_brake = gather_data(message_of_interest)
t = np.array(t_dcu_status_steering_brake) # Convert to numpy arrya
init_val = t[0]
t = t - t[0] # Make the time reference start from the first message

# We want to see when the step is
message_of_interest = 'dv_driving_dynamics_1'
t_dv_driving_dynamics_1, data_dv_driving_dynamics_1 = gather_data(message_of_interest)
t_dv_driving_dynamics_1 = np.array(t_dv_driving_dynamics_1) # Convert to numpy arrya
t_dv_driving_dynamics_1 = t_dv_driving_dynamics_1 - init_val # Make the time reference start from the first message

combined_time = np.unique(np.concatenate((t, t_dv_driving_dynamics_1)))


steering_actual = convert_to_angle(np.array(data_dcu_status_steering_brake['steering_angle_2']))
steering_target = np.array(data_dv_driving_dynamics_1['steering_angle_target'])

print("LEN: ", len(CAN_RX['dv_driving_dynamics_1']['time']))

if plot_step_time or plot_overshoot or plot_target or print_stats:
    step_time, overshoot, oscillation = analyze_system_response(steering_target, steering_actual, t)

if plot_system_response:
    # Plot the step response
    plt.plot(t, steering_actual, label='Response')

# Plot the target value
if plot_target:
    plt.axhline(steering_target, linestyle='--', color='r', label='Target')

# Add vertical lines for the 10% and 90% step times
if plot_step_time:
    plt.axvline(x=step_time['step_10'], color='r', linestyle='--', label='10% Step Time')
    plt.axvline(x=step_time['step_90'], color='g', linestyle='--', label='90% Step Time')

# Plot the overshoot
if plot_overshoot:
    max_value = max(steering_actual)
    overshoot_time = t[np.argmax(steering_actual)]
    plt.plot(overshoot_time, max_value, 'bo', label='Overshoot')
    plt.axhline(max_value, linestyle=':', color='b')

# Labels and stuff
if plot_system_response:
    plt.xlabel('Time (s)')
    plt.ylabel('Response')
    plt.title(f'Step Response with Overshoot')
    plt.legend()
    plt.grid()
    plt.show()

# Nice stats
if print_stats:
    stats = {
        'overshoot': round(max_value / steering_target,4),
        'step_time': round(step_time['step_time'],4),
        'Init value': steering_actual[0],
        'target'   : steering_target,
        'Nr of Data Points': len(t)
    }
    pprint.pprint(stats, indent=4)  


plt.plot(steering_target)