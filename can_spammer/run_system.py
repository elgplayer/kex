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


received_data = []
received_data_timestamps = []
recived_data_dict = {}
shutdown_flag = False
global start_time
start_time = None

msg_stats = {
    'rx': 0, 
    'tx': 0
}



##########
# CONFIG #
##########
virtual = True
verbose = False
TX_sampletime = 0.01
TIMEOUT = 3
progress_bar_steps = 100

################################################################################


def generate_step_response(step_t, overshoot, oscillation, t):
    # Calculate the damped natural frequency and damping ratio
    wn = np.pi / (step_t * np.sqrt(1 - overshoot**2))
    zeta = -np.log(overshoot) / np.sqrt(np.pi**2 + np.log(overshoot)**2)

    # Calculate the step response
    response = 1 - np.exp(-zeta * wn * t) * (np.cos(wn * np.sqrt(1 - zeta**2) * t) + (zeta / np.sqrt(1 - zeta**2)) * np.sin(wn * np.sqrt(1 - zeta**2) * t))

    # TODO: something with oscillation....

    return response

# Input parameters
step_time = 1.0
overshoot = 0.2
oscillation = 0.1


def send_virtual_can_message(ch, frame_id, data):
    ch.write(Frame(id_=frame_id, data=data))

################################################################################

# Function to send messages according to calculated_messages data
def send_messages(ch, db, calculated_messages):
    iteration = 0
    global shutdown_flag
    global start_time
    # Keep sending messages until the shutdown_flag is set
    while not shutdown_flag:
        
        # If the end of the calculated_messages list is reached, stop sending messages
        if iteration > len(calculated_messages)-1:
            shutdown_flag = True
            print("Message list exhausted! Stopping...")
            return
        
        # Get the message data for the current iteration
        random_signal_data = calculated_messages[iteration]
        
        # Iterate through the messages and send them
        for k, x in enumerate(random_signal_data):
            
            if start_time == None:
                
                start_time = time.time()
            
            frame_id = random_signal_data[x]['frame_id']
            message_name = random_signal_data[x]['name']
            encoded_data = random_signal_data[x]['encoded_data']
        
            if verbose:
                print(f"Sending CAN message: {message_name} ID = {frame_id}")
            
            
            if message_name == 'dv_driving_dynamics_1':
                time_now = time.time() - start_time 
                random_signal_data[x]['data']['steering_angle_actual'] = generate_step_response(step_time, overshoot, oscillation, time_now) * 50
                random_signal_data[x]['data']['steering_angle_target'] = 57
                message = db.get_message_by_name('dv_driving_dynamics_1')
                # print("hej")
                encoded_data = message.encode(random_signal_data[x]['data'], scaling=False) 
                
            send_virtual_can_message(ch, frame_id, encoded_data)
            msg_stats['tx'] += 1

        # Sleep for the specified TX_sampletime between message bursts
        time.sleep(TX_sampletime)
        if verbose:
            print(f"Iteration: {iteration}")
       
        iteration += 1


# Function to receive messages and process them
def receive_messages(ch, db):
    db_frame_ids = [message.frame_id for message in db.messages]

    global shutdown_flag
    # Keep receiving messages until the shutdown_flag is set
    while not shutdown_flag:
        # Check for pending messages and read them
        while canlib.Stat.RX_PENDING in ch.readStatus():
            rx = ch.read()
            rx_id = rx.id
            rx_data = bytes(rx.data)
            
            # Process the message if it is part of the database
            if rx_id in db_frame_ids:
                
                time_recived = time.time()
                message = db.get_message_by_frame_id(rx_id)
                decoded_data = message.decode(rx_data)
                result = message.decode(rx_data)
                
                msg_stats['rx'] += 1

                # Store the received message data
                if message.name not in recived_data_dict:
                    recived_data_dict[str(message.name)] = {
                        'data': [decoded_data],
                        'time': [time_recived]
                    }
                else:
                    recived_data_dict[message.name]['data'].append(decoded_data)
                    recived_data_dict[message.name]['time'].append(time_recived)

                if verbose:
                    print(f"Received CAN message with ID: {rx_id} and data: {decoded_data} | {message.name}")
                
                received_data.append({'message_name': message.name, 'data': result})
                received_data_timestamps.append(time.time())
   

def main():
    channel = 0
    chd = canlib.ChannelData(channel)
    print("CANlib version: v{}".format(chd.dll_product_version))
    print("canlib dll version: v{}".format(chd.dll_file_version))
    print("Using channel: {ch}, EAN: {ean}".format(ch=chd.channel_name, ean=chd.card_upc_no))
    

    ch_send = canlib.openChannel(channel, canlib.canOPEN_ACCEPT_VIRTUAL)
    ch_send.setBusOutputControl(canlib.canDRIVER_NORMAL)
    ch_send.setBusParams(canlib.canBITRATE_1M)
    ch_send.busOn()

    ch_receive = canlib.openChannel(channel, canlib.canOPEN_ACCEPT_VIRTUAL)
    ch_receive.setBusOutputControl(canlib.canDRIVER_NORMAL)
    ch_receive.setBusParams(canlib.canBITRATE_1M)
    ch_receive.busOn()

    db1 = cantools.database.load_file(r"src/can1.dbc")
    
    # load the list from the file
    CAN_messages = 'output/messages_medium.pkl'
    with open(CAN_messages, 'rb') as file:
        calculated_messages = pickle.load(file)
        
    print(f"Starting CAN DDOS for {TIMEOUT} seconds")
    print(f"TX sample frequency: {1/TX_sampletime}")

    # Use threads
    send_thread = threading.Thread(target=send_messages, args=(ch_send, db1, calculated_messages))
    receive_thread = threading.Thread(target=receive_messages, args=(ch_receive, db1))

    # Start the threads
    send_thread.start()
    receive_thread.start()

    # Wait for TIMEOUT before setting the shutdown_flag
    sleep_time = TIMEOUT/progress_bar_steps
    for _ in tqdm(range(progress_bar_steps), desc="Waiting", ncols=75, unit="sec"):
        time.sleep(sleep_time)

    global shutdown_flag
    shutdown_flag = True

    # Join the threads
    send_thread.join()
    receive_thread.join()

    # nice printout
    pprint.pprint(msg_stats)
    
    CAN_RESPONSES_path = 'output/CAN_RESPONSES'
    if not os.path.exists(CAN_RESPONSES_path):
        os.makedirs(CAN_RESPONSES_path, exist_ok=True)
        print(f"Creating diretory: {CAN_RESPONSES_path}")

    # Saving data!
    CAN_RESPONSES_info = []
    CAN_RESPONSES_info_path = 'output/CAN_response_info.json'
    if not os.path.exists(CAN_RESPONSES_info_path):
        CAN_RESPONSES_info = []
        print("Creating new CAN response file!")
    else:
        with open(CAN_RESPONSES_info_path, 'r') as f:
            try:
                CAN_RESPONSES_info = json.load(f)
            except Exception as e:
                print(f"error: {e}")
                CAN_RESPONSES_info = []
            
            print("Reading exisitng CAN response file!")
    
    datetime_now = datetime.now()
    formatted_date = datetime_now.strftime("%Y_%m_%d__%H_%M_%S")
    CAN_response = f'{CAN_RESPONSES_path}/CAN_RX_{formatted_date}.pkl'
    
    CAN_RESPONSES_info.append({
        'date': datetime_now.strftime("%Y:%m:%d %H:%M:%S"),
        'formatted_date': formatted_date,
        'rx_msg': msg_stats['rx'],
        'tx_msg': msg_stats['tx'],
        'priority': 0.69, # placeholder,
        'TX_sampletime': TX_sampletime,
        'TIMEOUT': TIMEOUT,
        'step_time': step_time,
        'overshoot': overshoot,
        'oscillation': oscillation,
        'CAN_filename': f'CAN_RX_{formatted_date}.pkl'
    })
    
    
    with open(CAN_RESPONSES_info_path, 'w', encoding='utf-8') as f:
        f.write(json.dumps(CAN_RESPONSES_info, indent=4))
    
    
    with open(CAN_response, 'wb') as f:
        pickle.dump(recived_data_dict, f)
    
    ch_send.busOff()
    ch_receive.busOff()

if __name__ == "__main__":
    main()


#%%