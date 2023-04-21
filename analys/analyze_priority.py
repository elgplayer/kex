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
overwrtie               = False


## Some CONFIG
DATA_FOLDER = "C:\\Users\\carlv\\Documents\\carl\projects\\kex\\resultat\\CAN_RESPONSES\\periodicity"
folders     = os.listdir(DATA_FOLDER)
full_data = {}
outer_loop = tqdm(range(len(folders)), desc="Outer loop", ncols=100)

for i in outer_loop:
    
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
                response_char = helper.analyze_system_response(file_data, DATA_FOLDER, folder, file, generate_step_responses)
                response_char_list.append(response_char)
            except Exception as e:
                print(f'Error: {e} | folder: {folder} | file : {file}')
                error = True

        if error == True:
            continue
        
    if calc_avg:
        try:
            response_avg = helper.calculate_response_avg(response_char_list, DATA_FOLDER, folder)
            full_data[folder] = response_avg
        except Exception as e:
            print(f"error: {e} | folder: {folder}")

#%%


%importlib.reload(helper)
%response_char = helper.analyze_system_response(file_data, DATA_FOLDER, 'stm_500_dspace_500', 'CAN_RX_2023_04_19__15_23_46.pkl', True)

