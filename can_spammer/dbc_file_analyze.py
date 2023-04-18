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

db = cantools.database.load_file(r"src/can1.dbc")

#### CONFIG ###

normalize_frame_id = False

###############


ignored_messages = []
messages_frame_id = []
messages_name     = []

ignore_id = [1280, 17]

for k,message in enumerate(db.messages):
    # if message.is_multiplexed():
    
    #     print("Skip", k)
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


percentiles = np.arange(0, 100, 10)  # [90, 80, 70, ..., 0]
indices = []

for p in percentiles:
    value = np.percentile(messages_frame_id, p)
    index = np.searchsorted(messages_frame_id, value)
    indices.append(index)


if normalize_frame_id: 
    messages_frame_id = range(0,len(messages_frame_id))

plt.figure(figsize=(16, 8))
plt.plot(messages_frame_id, marker='x')
plt.xlabel("Index")
plt.ylabel("Frame ID")


for k, x in enumerate(indices):
    percentile = percentiles[k]
    frame_id = messages_frame_id[x]
    message_name = messages_name[x]
    
    plt.axvline(x=x, color='r', linestyle='--', alpha=0.7)
    plt.text(x, 0, f"{frame_id} ({message_name})", rotation=90, ha='right', va='bottom')


plt.title(f"Frame IDs with Percentile Lines | Normalized: {normalize_frame_id}")
plt.grid(True)
plt.show()

