#%%
import time
import random
import pprint
import math
from multiprocessing import Pool, freeze_support
import time
import pickle

import cantools
from canlib import canlib, Frame
from tqdm import tqdm

channel = 0
chd = canlib.ChannelData(channel)
print("CANlib version: v{}".format(chd.dll_product_version))
print("canlib dll version: v{}".format(chd.dll_file_version))
print("Using channel: {ch}, EAN: {ean}".format(ch=chd.channel_name, ean=chd.card_upc_no))


ch_send = canlib.openChannel(channel, canlib.canOPEN_ACCEPT_VIRTUAL)
ch_send.setBusOutputControl(canlib.canDRIVER_NORMAL)
ch_send.setBusParams(canlib.canBITRATE_500K)
ch_send.busOn()

db = cantools.database.load_file(r"can1.dbc")
random.seed(42)

def generate_random_value_for_signal(signal):
    
    scaling_factor = signal.scale if signal.is_float else 1
    decimal_places = abs(math.floor(math.log10(scaling_factor)))
            
    if signal.is_signed:
        min_value = signal.minimum if signal.minimum is not None else -(2**(signal.length-1)) * scaling_factor
        max_value = signal.maximum if signal.maximum is not None else ((2**(signal.length-1)) - 1) * scaling_factor
    else:
        min_value = signal.minimum if signal.minimum is not None else 0
        max_value = signal.maximum if signal.maximum is not None else (2**signal.length - 1) * scaling_factor

    if signal.length == 1:  # If it's a single bit, only allow 0 or 1
        random_value = random.choice([0, 1])
    else:
        random_value = random.uniform(min_value, max_value)
        random_value = round(random_value, decimal_places)  # Change to decimal_places
    
    # Ensure the random value is within the allowed range
    if signal.minimum is not None and random_value < signal.minimum:
        random_value = signal.minimum
    if signal.maximum is not None and random_value > signal.maximum:
        random_value = signal.maximum
    
    # Store unscaled values for non-float signals, and scale float signals
    if signal.is_float:
        random_value /= scaling_factor
    else:
        random_value = int(random_value)   
        
    return random_value


def generate_random_signals_for_message(message):
    
    random_values = {}
    
    for signal in message.signals:

        iter = 0
        scaling_factor = signal.scale if signal.is_float else 1
        random_value = generate_random_value_for_signal(signal)

        if signal.minimum is not None:
            min_effective = (signal.minimum - signal.offset) / signal.scale
        else:
            min_effective = -(2 ** (signal.length - 1)) * scaling_factor if signal.is_signed else 0

        if signal.maximum is not None:
            max_effective = (signal.maximum - signal.offset) / signal.scale
        else:
            max_effective = ((2 ** (signal.length - 1)) - 1) * scaling_factor if signal.is_signed else (2 ** signal.length - 1) * scaling_factor

        while (random_value < min_effective or random_value > max_effective) and iter < 10000:
            random_value = generate_random_value_for_signal(signal)
            iter+=1
        
        
        random_values[signal.name] = random_value
    
    return random_values


def process_item(i):
    random_data = {}
    for k, message in enumerate(db.messages):
        if message.is_multiplexed():
            continue
        random_message = generate_random_signals_for_message(message)
        # Wipe
        for key, value in random_message.items():
            if value < 0:
                random_message[key] = 0
        encoded_msg = message.encode(random_message, scaling=False)
        decoded_msg = message.decode(encoded_msg, scaling=False)

        random_data[message.name] = {
            'name': message.name,
            'frame_id': message.frame_id,
            'data': random_message,
            'encoded_data': encoded_msg,
            'decoded_data': decoded_msg
        }
    return random_data


if __name__ == '__main__':


    freeze_support() # Add this line to fix the RuntimeError

    data_list = []
    nr_of_messages = 100000
    my_list = range(nr_of_messages)

    def process_item(i):
        random_data = {}
        for k, message in enumerate(db.messages):
            if message.is_multiplexed():
                continue
            random_message = generate_random_signals_for_message(message)
            # Wipe
            for key, value in random_message.items():
                if value < 0:
                    random_message[key] = 0
            encoded_msg = message.encode(random_message, scaling=False)
            decoded_msg = message.decode(encoded_msg, scaling=False)

            random_data[message.name] = {
                'name': message.name,
                'frame_id': message.frame_id,
                'data': random_message,
                'encoded_data': encoded_msg,
                'decoded_data': decoded_msg
            }
        return random_data

    # create a pool of worker processes
    with Pool(processes=8) as pool:
        # process the items in parallel
        results = list(tqdm(pool.imap(process_item, my_list), total=len(my_list), desc='Processing items'))

    # store the results in a list
    for result in results:
        data_list.append(result)

    # open a file for binary writing
    with open('output/messages_small.pkl', 'wb') as file:
        # dump the list into the file
        pickle.dump(data_list[0:1000], file)

    with open('output/messages_medium.pkl', 'wb') as file:
        # dump the list into the file
        pickle.dump(data_list[0:10000], file)

    with open('output/messages_large.pkl', 'wb') as file:
        # dump the list into the file
        pickle.dump(data_list, file)

    print("Files pickled!")
