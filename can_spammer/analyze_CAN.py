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


CAN_RX_path = 'output/CAN_RX.pkl'
with open(CAN_RX_path, 'rb') as file:
    CAN_RX = pickle.load(file)
    
CAN_MESSAGES_path = 'output/messages_small.pkl'
with open(CAN_MESSAGES_path, 'rb') as file:
    CAN_MESSAGES = pickle.load(file)

db = cantools.database.load_file(r"src/can1.dbc")
    
# pprint.pprint(CAN_RX, indent=4)
#%%

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

message_of_interest = 'dv_driving_dynamics_1'
t, data = gather_data(message_of_interest)

# Plot the step response
plt.plot(t, data['steering_angle_actual'])
plt.xlabel('Time (s)')
plt.ylabel('Response')
#plt.title(f'Step Response with Overshoot={overshoot}, Step Time={step_time}, Oscillation={oscillation}')
plt.grid()
plt.show()






