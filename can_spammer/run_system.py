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
import math


import cantools
from tqdm import tqdm
from canlib import canlib, Frame
import numpy as np
from scipy.signal import lti, step


received_data = []
received_data_timestamps = []
recived_data_dict = {}
shutdown_flag = False
global start_time
global step_target
global total_bits_transmitted
start_time = None
state = np.zeros((2, 1))
response = []
msg_stats = {
    'rx': 0, 
    'tx': 0
}
total_bits_transmitted = 0

################################################################################

##########
# CONFIG #
##########

virtual = True
verbose = False
progress_bar_steps = 100
read_steering_from_file = True
steering_file = 'src/time_steer_out.txt'


timeout = 5

TX_sampletime = 0.1
step_sample_time = 0.01


step_time = 2       # seconds  
step_target = 40    # Degrees
damping_ratio = 0.3
natural_frequency = 5


RX_ignore_id = [1280]

################################################################################

def generate_step_response(final_value, damping_ratio, natural_frequency, state, dt):
    """
    Generates a step response with customizable overshoot and oscillations using a second-order system model.

    Parameters:
    final_value (float): The final value after the step.
    damping_ratio (float): The damping ratio of the system (0 to 1).
    natural_frequency (float): The natural frequency of the system.
    state (array): The current state of the system.
    dt (float): The time step.

    Returns:
    tuple: A tuple containing the updated state and the response at the current time step.
    """
    # Calculate the second-order system coefficients
    wn_square = natural_frequency ** 2
    two_zeta_wn = 2 * damping_ratio * natural_frequency

    # Create the continuous state-space matrices
    Ac = np.array([[0, 1], [-wn_square, -two_zeta_wn]])
    Bc = np.array([[0], [1]])
    C = np.array([wn_square * final_value, 0])
    D = 0

    # Backward Euler method
    I = np.eye(2)
    A_inv = np.linalg.inv(I - dt * Ac)
    state = A_inv @ (state + dt * Bc)

    # Calculate the output
    output = C @ state + D

    return state, output.item()


def process_file(file_path):
    with open(file_path, 'r') as file:
        lines = file.readlines()

    # Parse the first timestamp
    first_timestamp, _ = lines[0].strip().split(',')
    first_timestamp = float(first_timestamp)

    # Process the lines
    processed_lines = {
        'time': [],
        'data': []
    }
    for line in lines:
        timestamp, radians = line.strip().split(',')
        timestamp = float(timestamp)
        radians = float(radians)

        # Make the timestamp relative to the first timestamp
        relative_timestamp = timestamp - first_timestamp

        # Convert radians to degrees
        degrees = radians * (180 / math.pi)
        if abs(degrees) > 180:
            continue   
        
        processed_lines['time'].append(relative_timestamp)
        processed_lines['data'].append(degrees)
        

    return processed_lines


def send_virtual_can_message(ch, frame_id, data):
    ch.write(Frame(id_=frame_id, data=data))
    
if step_time > timeout:
    print("Error! Step is outside of the timeout period!")

################################################################################

def calculate_bus_load(bit_rate=1e6):
    global total_bits_transmitted
    global start_time_RX
    
    total_time = time.time() - start_time_RX

    # Calculate the bus load as a percentage
    bus_load = (total_bits_transmitted / (bit_rate * total_time)) * 100

    return bus_load


# Function to send messages according to calculated_messages data
def send_messages(ch, db, calculated_messages):
    iteration = 0
    global shutdown_flag
    global start_time
    global step_target
    
    global total_bits_transmitted
    

    state = np.zeros((2, 1))
    response = []
    bus_load = []
    
    if start_time == None:
        start_time = time.time()
        time_now = start_time
            
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
            
            time_now = time.time() - start_time
            frame_id = random_signal_data[x]['frame_id']
            message_name = random_signal_data[x]['name']
            encoded_data = random_signal_data[x]['encoded_data']

            # Read from file and generate new steering targets!
            if message_name == 'dv_driving_dynamics_1' and read_steering_from_file == True:
                data = random_signal_data[x]['data']
                step_target_2 = data['steering_angle_target']

            # Skip!
            if frame_id in RX_ignore_id:
                continue
            
             # Calculate message size in bits
            message_size_bits = 44 + (8 * len(encoded_data))
            total_bits_transmitted += message_size_bits
    
            # Generate a fake step response
            # TODO: Still a bit broken!
            if message_name == 'dcu_status_steering_brake' and virtual == True:
                if time_now < step_time:
                    steering_angle = 0
                else:
                    if read_steering_from_file:
                        step_target = step_target_2
  
                    # Generate the step response
                    dt = time_now - last_time
                    state, output = generate_step_response(step_target, damping_ratio, natural_frequency, state, dt)
                    steering_angle = int((output / 90) * 2024)
                    
                    # Clip output
                    if steering_angle > 2024:
                        steering_angle = 2024
                    elif steering_angle < -2024:
                        steering_angle = -2024
                    
                response.append(steering_angle)
                data = random_signal_data[x]['data']
                data['steering_angle_2'] = steering_angle
                message = db.get_message_by_name(message_name)
                try:
                    encoded_data = message.encode(data, scaling=False)
                except Exception as e:
                    tqdm.write(f"Error: {e} | {data}")

            if verbose:
                print(f"Sending CAN message: {message_name} ID = {frame_id}")

            send_virtual_can_message(ch, frame_id, encoded_data)
            
            msg_stats['tx'] += 1

        # Sleep for the specified TX_sampletime between message bursts
        time.sleep(TX_sampletime)
        last_time = time_now
        bus_load.append(calculate_bus_load())
        if verbose:
            print(f"Iteration: {iteration}")
       
        iteration += 1

    pprint.pprint(bus_load)

def send_step(ch, db):
    global shutdown_flag
    global start_time
    global step_target
    
    message = db.get_message_by_name('dv_driving_dynamics_1')
    step_data = {}
    has_stepped = False
    for signal in db.get_message_by_name('dv_driving_dynamics_1').signals:
        step_data[signal.name] = 0
        
        
    if read_steering_from_file == True:
        steering_requests = process_file(steering_file)
        steering_index = 0
        
        steering_requests['data'] = steering_requests['data'][0:20]
        steering_requests['time'] = steering_requests['time'][0:20]
        
    # Keep sending messages until the shutdown_flag is set
    while not shutdown_flag:
        
        if start_time == None:
            start_time = time.time()

        # We want to trigger the step!
        time_diff = time.time() - start_time
        if time_diff > step_time:
            if read_steering_from_file == True:
                step_target = steering_requests['data'][steering_index]
                steering_index += 1
            
            step_data['steering_angle_target'] = step_target
            
        # Encode the message
        encoded_data = message.encode(step_data, scaling=False)
        send_virtual_can_message(ch, message.frame_id, encoded_data)
        msg_stats['tx'] += 1

        # Sleep for the specified TX_sampletime between message bursts
        if time_diff > step_time and read_steering_from_file == True:
            time.sleep(steering_requests['time'][steering_index])
        # Normal sleep
        else:
            time.sleep(step_sample_time)


# Function to receive messages and process them
def receive_messages(ch, db):
    db_frame_ids = [message.frame_id for message in db.messages]
    
    global shutdown_flag
    global total_bits_transmitted
    global start_time_RX
    
    start_time_RX = time.time()
    
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
                decoded_data = message.decode(rx_data, scaling=False)
                msg_stats['rx'] += 1

                # Calculate message size in bits
                message_size_bits = 44 + (8 * len(rx_data))
                total_bits_transmitted += message_size_bits

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
        
    print(f"Starting CAN DDOS for {timeout} seconds")
    if TX_sampletime != 0:
        print(f"TX sample frequency: {1/TX_sampletime}")
    else:
        print("TX DDOS disbled!")
    
    # Use threads
    if TX_sampletime != 0:
        send_thread = threading.Thread(target=send_messages, args=(ch_send, db1, calculated_messages))
    receive_thread = threading.Thread(target=receive_messages, args=(ch_receive, db1))
    step_thread = threading.Thread(target=send_step, args=(ch_send, db1))

    # Start the threads
    if TX_sampletime != 0:
        send_thread.start()
    receive_thread.start()
    step_thread.start()

    # Wait for timeout before setting the shutdown_flag
    sleep_time = timeout/progress_bar_steps
    for _ in tqdm(range(progress_bar_steps), desc="Waiting", ncols=75, unit="sec"):
        time.sleep(sleep_time)

    global shutdown_flag
    shutdown_flag = True

    # Join the threads
    send_thread.join()
    receive_thread.join()
    step_thread.join()

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
        'timeout': timeout,
        'step_time': step_time,
        'step_target': step_target,
        'natural_frequency': natural_frequency,
        'damping_ratio': damping_ratio,
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