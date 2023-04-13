#%%
import time
import random
import asyncio
import pprint
import json
from io import StringIO
import decimal
import pickle

import cantools
from canlib import canlib, Frame
import matplotlib as plt
import numpy as np
import matplotlib.pyplot as plt


CAN_RX_path = 'output/CAN_RESPONSES/CAN_RX_2023_04_13__08_01_58.pkl'
with open(CAN_RX_path, 'rb') as file:
    CAN_RX = pickle.load(file)
    
CAN_MESSAGES_path = 'output/messages_small.pkl'
with open(CAN_MESSAGES_path, 'rb') as file:
    CAN_MESSAGES = pickle.load(file)

db = cantools.database.load_file(r"src/can1.dbc")
    
# pprint.pprint(CAN_RX, indent=4)
#%%

def analyze_system_response(target, output_data, time_data):
    # Step 1: Calculate step time
    step_time_10_idx = np.argmax(output_data >= 0.1 * target)
    step_time_10 = time_data[step_time_10_idx]
    
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

#######################
### PLOT CONFIG #######
#######################

plot_step_time = False
plot_overshoot = True
plot_target    = False
print_stats    = True

######################
######################
######################

message_of_interest = 'dv_driving_dynamics_1'
t, data = gather_data(message_of_interest)
t = np.array(t) # Convert to numpy arrya
t = t - t[0] # Make the time reference start from the first message

steering_actual = np.array(data['steering_angle_actual'])
steering_target = data['steering_angle_actual'][-1] # hmm

step_time, overshoot, oscillation = analyze_system_response(steering_target, steering_actual, t)

# Plot the step response
plt.plot(t, data['steering_angle_actual'], label='Response')

# Plot the target value
if plot_target:
    plt.axhline(steering_target, linestyle='--', color='r', label='Target')

# Add vertical lines for the 10% and 90% step times
if plot_step_time:
    plt.axvline(x=step_time['step_10'], color='r', linestyle='--', label='10% Step Time')
    plt.axvline(x=step_time['step_90'], color='g', linestyle='--', label='90% Step Time')

# Plot the overshoot
if plot_overshoot:
    max_value = max(data['steering_angle_actual'])
    overshoot_time = t[np.argmax(data['steering_angle_actual'])]
    plt.plot(overshoot_time, max_value, 'bo', label='Overshoot')
    plt.axhline(max_value, linestyle=':', color='b')

plt.xlabel('Time (s)')
plt.ylabel('Response')
plt.title(f'Step Response with Overshoot')
plt.legend()
plt.grid()
plt.show()

stats = {
    'overshoot': round(max_value / steering_target,4),
    'step_time': round(step_time['step_time'],4),
    'Init value': steering_actual[0],
    'target'   : steering_target,
    'Nr of Data Points': len(t)
}

if print_stats:
    pprint.pprint(stats, indent=4)  

