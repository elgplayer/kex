#%%
import os 
import json
import pprint
import pickle
import importlib
from tqdm import tqdm

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

import helper
importlib.reload(helper)
plt.rcParams['figure.max_open_warning'] = 50

## Parameters ##
generate_step_responses = False
calc_avg                = True
overwrite               = False

# Select the columns to sum
topics_to_sum = ['rise_time', 'overshoot', 'settling_time', 'steering_variance']
bar_labels    = ['Rise time [s]', 'Overshoot [%]', 'Settling time [s]', 'Steering Variance']

## Some CONFIG
DATA_FOLDER = "C:\\Users\\carlv\\Documents\\carl\projects\\kex\\resultat\\CAN_RESPONSES\\prioritity"
folders     = os.listdir(DATA_FOLDER)
raw_data = {}
avg_data = {}
jitter_data = {}
outer_loop = tqdm(range(len(folders)), desc="Outer loop", ncols=100)


key_mapping = {
    'x': {
        5: 10,
        6: 10,
        25: 50,
        44: 90
    },
    'y': {
        5: 10,
        24: 50, 
        25: 50,
        43: 90,
        44: 90
    }
}


output_folder = 'C:\\Users\\carlv\\Documents\\carl\projects\\kex\\analys\\output\\prioritity\\matrix'
matrix_config = {
    'test_type'       : 'Prioritity',
    'x_axis'          : 'VESC',
    'y_axis'          : 'STM32',
    'metrics'         : topics_to_sum,
    'bar_labels'      : bar_labels,
    'output_folder'   : output_folder,
    'save_image'      : True,
    'visual_mode'     : True,
    'key_mapping'     : key_mapping
}


for i in outer_loop:
    
    # Parse file names, folder
    folder = folders[i]
    split_folder  = folder.split("_")
    stm_period    = split_folder[0]
    dspace_period = split_folder[3]
    
    files_path = f'{DATA_FOLDER}\\{folder}'
    files = [file for file in os.listdir(files_path) if os.path.splitext(file)[1] == ".pkl"]
    if files == []:
        print(f"Empty folder: {folder}")
        continue

    response_char_list = []
    for file in files:
        file_path = f'{DATA_FOLDER}\\{folder}\\{file}'
        with open(file_path, 'rb') as f:
            file_data = pickle.load(f)
            # Get invidual response
            response_char = helper.analyze_system_response(file_data, DATA_FOLDER, folder, file, generate_step_responses, overwrite)
            response_char_list.append(response_char)
            jitter = helper.calc_jitter(file_data, folder)
            if not stm_period in jitter_data:
                jitter_data[folder] = jitter
            else:
                jitter_data[folder] = np.concatenate((jitter_data[folder], jitter))
                    
                
    # Add the data to a dictionary
    raw_data[folder] = response_char_list

importlib.reload(helper)
if calc_avg:
    response_char_dict = {}
    for k,x in enumerate(raw_data):
        y__idx, x__idx = [int(val) for val in x.split('_')[1::2]]
        
        if 'key_mapping' in matrix_config:
            key_mapping = matrix_config['key_mapping']
            
        x_idx_new = key_mapping['x'][x__idx]
        y_idx_new = key_mapping['y'][y__idx]
        folder = f'stm_{y_idx_new}_vesc_{x_idx_new}'
        
        # Save to folder
        if folder not in response_char_dict:
            response_char_dict[folder] = raw_data[x]
        else:
            response_char_dict[folder].append(raw_data[x])
            
    for k,folder in enumerate(response_char_dict):
        response_char_list = response_char_dict[folder]    
        response_avg = helper.calculate_response_avg(response_char_list, topics_to_sum, DATA_FOLDER, folder)
        avg_data[folder] = response_avg
        

            
#%%

importlib.reload(helper)
#matrix = helper.generate_matrix(avg_data, matrix_config)

helper.plot_jitter(jitter_data, matrix_config)

