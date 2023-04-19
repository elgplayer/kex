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

db = cantools.database.load_file(r"src/can1.dbc")
random.seed(42)


mapping_list = {
'---RESEVEREDSTM---':13,
'---RESEVEREDVESC---':12,
'FSE_EnergyMeter_Data':48,
'SBG_ECAN_MSG_AUTO_SLIP_CURV':47,
'SBG_ECAN_MSG_EKF_EULER':37,
'SBG_ECAN_MSG_EKF_INFO':36,
'SBG_ECAN_MSG_EKF_ORIENTATION_ACC':38,
'SBG_ECAN_MSG_EKF_POS':39,
'SBG_ECAN_MSG_EKF_POS_ACC':40,
'SBG_ECAN_MSG_EKF_VEL_NED':41,
'SBG_ECAN_MSG_EKF_VEL_NED_ACC':42,
'SBG_ECAN_MSG_GPS1_HDT':45,
'SBG_ECAN_MSG_GPS1_HDT_INFO':44,
'SBG_ECAN_MSG_IMU_ACCEL':34,
'SBG_ECAN_MSG_IMU_GYRO':35,
'SBG_ECAN_MSG_IMU_INFO':33,
'SBG_ECAN_MSG_ODO_VEL':43,
'ams_cell_temperatures':8,
'ams_cell_voltages':7,
'ams_error':4,
'ams_state':5,
'ams_status_1':6,
'ams_temperatures':9,
'ccu_status_1':24,
'ccu_status_2':23,
'dbu_status_1':19,
'dbu_status_2':20,
'dcu_pps':1,
'dcu_status':2,
'dv_control_target':3,
'dv_driving_dynamics_2':49,
'dv_system_status':50,
'ebs_status':22,
'ecu_status':21,
'fault':32,
'lv_bms_data_a':27,
'lv_bms_data_b':29,
'lv_bms_status_a':28,
'lv_bms_status_b':30,
'lv_power_signal':26,
'mcu_set_ccu_cooling_points':25,
'mcu_set_dbu_indicator_points':52,
'mcu_set_ecu_indicator_points':51,
'res_initialization':53,
'res_ntm_node_control':0,
'res_status':46,
'set_mcu_inverter_points':31,
'swu_status':18,
'vehicle_status':10,
'vehicle_status_wheel_speed':11,
'vmu_fl':14,
'vmu_fr':15,
'vmu_rl':16,
'vmu_rr':17}

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
        frame_id = message.frame_id
        
        if message.name in mapping_list:
            frame_id = mapping_list[message.name]
        else:
            continue 

        random_data[message.name] = {
            'name': message.name,
            'frame_id': frame_id,
            'data': random_message,
            'encoded_data': encoded_msg,
            'decoded_data': decoded_msg
        }
    return random_data


if __name__ == '__main__':

    freeze_support() # Add this line to fix the RuntimeError

    data_list = []
    nr_of_messages = 1000
    my_list = range(nr_of_messages)

    # create a pool of worker processes
    with Pool(processes=8) as pool:
        # process the items in parallel
        results = list(tqdm(pool.imap(process_item, my_list), total=len(my_list), desc='Processing items'))

    # store the results in a list
    for result in results:
        data_list.append(result)
        
    pprint.pprint(data_list[0:10])

    # open a file for binary writing
    with open('output/messages_small.pkl', 'wb') as file:
        # dump the list into the file
        pickle.dump(data_list[0:1000], file)

    # with open('output/messages_medium.pkl', 'wb') as file:
    #     # dump the list into the file
    #     pickle.dump(data_list[0:10000], file)

    # with open('output/messages_large.pkl', 'wb') as file:
    #     # dump the list into the file
        pickle.dump(data_list, file)

    print("Files pickled!")
