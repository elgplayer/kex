#%%
import time
import random
import asyncio
import pprint
import json
from io import StringIO
import decimal
import pickle
import threading
import os
from datetime import datetime


import cantools
from tqdm import tqdm
from canlib import canlib, Frame
import numpy as np
import matplotlib.pyplot as plt
import math

db = cantools.database.load_file(r"src/can1.dbc")

#### CONFIG ###

normalize_frame_id = True

###############

global messages_name
global messages_frame_id

ignored_messages = []
messages_frame_id = []
messages_name     = []

ignore_id = [1280, 17]

for k,message in enumerate(db.messages):
    # if message.is_multiplexed():
    #     continue
    
    frame_id = message.frame_id
    
    if frame_id in ignore_id:
        continue
    
    messages_frame_id.append(message.frame_id)
    messages_name.append(message.name)


# Zip the two lists together
zipped_lists = zip(messages_frame_id, messages_name)

# Sort the zipped lists based on the order of list1
sorted_zipped_lists = sorted(zipped_lists, key=lambda x: x[0])

# Unzip the sorted lists back into individual lists
messages_frame_id, messages_name = zip(*sorted_zipped_lists)

if normalize_frame_id: 
    messages_frame_id = range(0,len(messages_frame_id))
    
messages_name = list(messages_name)
messages_frame_id = np.array(messages_frame_id)

def insert_at_percentage(perc, how='under', print_messages=True):
    global messages_name
    global messages_frame_id
    
    mapping_list = {}
    len_list = len(messages_name) + 2

    if how == 'under':
        idx = math.floor(len_list * perc / 100) - 1
    else:
        idx =  math.floor(len_list * perc / 100) + 1

    messages_name.insert(idx, '--- RESEVERED STM ---')
    messages_name.insert(idx, '--- RESEVERED VESC ---')

    messages_frame_id = np.insert(messages_frame_id, idx, idx)
    messages_frame_id = np.insert(messages_frame_id, idx+1, idx+1)
    messages_frame_id = messages_frame_id[idx+2:] + 2

    if print_messages:
        for k in range(len_list):
            message = messages_name[k].ljust(35)
            percentage = round(k / len(messages_name) * 100, 1)
            print(f"{message} - {k} / {len(messages_name)-1} ({percentage}) %")
            mapping_list[message] = k
          
    if print_messages:
        pprint.pprint(mapping_list)
            
            
insert_at_percentage(22, 'over')



#%%
# for k,x in enumerate(messages_frame_id):
#     print(messages_frame_id[k], messages_name[k])

percentiles = np.arange(0, 100, 10)  # [90, 80, 70, ..., 0]
indices = []

for p in percentiles:
    value = np.percentile(messages_frame_id, p)
    index = np.searchsorted(messages_frame_id, value)
    indices.append(index)
    

plt.figure(figsize=(10, 8))
plt.plot(messages_frame_id, marker='x')
plt.xlabel("Index")
plt.ylabel("Frame ID")

for k, x in enumerate(indices):
    percentile = percentiles[k]
    frame_id = messages_frame_id[x]
    _message_name = messages_name[x]
    
    plt.axvline(x=x, color='r', linestyle='--', alpha=0.7)
    plt.text(x, 0, f"{frame_id} ({_message_name})", rotation=90, ha='right', va='bottom')
    
plt.title(f"Frame IDs with Percentile Lines | Normalized: {normalize_frame_id}")
plt.grid(True)
plt.show()

before_percentile = 10
idx = np.argmax(percentiles == before_percentile+10)
print(messages_frame_id[:idx])

