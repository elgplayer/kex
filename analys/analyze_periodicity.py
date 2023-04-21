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

## Some CONFIG
DATA_FOLDER = "C:\\Users\\carlv\\Documents\\carl\projects\\kex\\resultat\\CAN_RESPONSES\\periodicity"
folders     = os.listdir(DATA_FOLDER)
full_data = {}
outer_loop = tqdm(range(len(folders)), desc="Outer loop", ncols=100)

for i in outer_loop:
    
    # Parse file names, folder
    folder = folders[i]
    split_folder  = folder.split("_")
    stm_period    = split_folder[0]
    dspace_period = split_folder[3]
    
    files_path = f'{DATA_FOLDER}\\{folder}'
    files = [file for file in os.listdir(files_path) if os.path.splitext(file)[1] == ".pkl"]

    response_char_list = []

    for file in files:
        
        file_path = f'{DATA_FOLDER}\\{folder}\\{file}'
        
        with open(file_path, 'rb') as f:
            file_data = pickle.load(f)
            error = False
            try:
                # Get invidual response
                response_char = helper.analyze_system_response(file_data, DATA_FOLDER, folder, file, generate_step_responses)
                response_char_list.append(response_char)
            except Exception as e:
                print(f'Error: {e} | folder: {folder} | file : {file}')
                error = True

        if error == True:
            continue
        
    # Add the response to a dicitonary where the avg value for all responses are calculated.
    if calc_avg:
        try:
            response_avg = helper.calculate_response_avg(response_char_list, DATA_FOLDER, folder)
            full_data[folder] = response_avg
        except Exception as e:
            print(f"error: {e} | folder: {folder}")


output_folder = 'C:\\Users\\carlv\\Documents\\carl\projects\\kex\\analys\\output\\periodicity\\matrix'
matrix = helper.generate_periodicity_matrix(full_data, output_folder, True, False)

#%%


# importlib.reload(helper)
#response_char = helper.analyze_system_response(file_data, DATA_FOLDER, 'stm_500_dspace_500', 'CAN_RX_2023_04_19__15_23_46.pkl', True)



# #%%
# importlib.reload(helper)
# DATA_FOLDER = 'C:\\Users\\carlv\\Documents\\carl\projects\\kex\\resultat\\CAN_RESPONSES\\prioritity'
# folder  = 'stm_44_vesc_5'
# file = 'CAN_RX_2023_04_20__15_00_51.pkl'
# file_path = f'{DATA_FOLDER}\\{folder}\\{file}'

# with open(file_path, 'rb') as f:
#     file_data = pickle.load(f)
# response_char = helper.analyze_system_response(file_data, DATA_FOLDER, folder, file, True)
