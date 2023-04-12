#%%
import time
import random
import asyncio
import pprint
import json
from io import StringIO
import decimal
import pickle
from ctypes import c_long

import cantools
from canlib import canlib, Frame



received_data = []
received_data_timestamps = []
recived_data_dict = {}
shutdown_flag = False

msg_stats = {'rx': 0, 'tx': 0}
##########
# CONFIG #
##########
virtual = True
verbose = False
RX_sleep = 0.0000001
TX_sample = 0.01
TIMEOUT = 10



def send_virtual_can_message(ch, frame_id, data):
    ch.write(Frame(id_=frame_id, data=data))

################################################################################

async def send_messages(ch, db, calculated_messages):
    iteration = 0
    global shutdown_flag
    while not shutdown_flag:
        
        if iteration > len(calculated_messages)-1:
            shutdown_flag = True
            return
        
        random_signal_data = calculated_messages[iteration]
        
        for k, x in enumerate(random_signal_data):
            
            frame_id = random_signal_data[x]['frame_id']
            message_name = random_signal_data[x]['name']
            encoded_data = random_signal_data[x]['encoded_data']
        
            if verbose:
                print(f"Sending CAN message: {message_name} ID = {frame_id}")
            send_virtual_can_message(ch, frame_id, encoded_data)
            msg_stats['tx'] += 1

        await asyncio.sleep(TX_sample)
        if verbose:
            print(f"Iteration: {iteration}")
        iteration += 1


async def receive_messages(ch, db):
    db_frame_ids = [message.frame_id for message in db.messages]

    global shutdown_flag
    #while not shutdown_flag:
    while not shutdown_flag:
        while canlib.Stat.RX_PENDING in ch.readStatus():
            rx = ch.read()
            rx_id = rx.id
            rx_data = bytes(rx.data)
            
            if rx_id in db_frame_ids:
                
                time_recived = time.time()
                message = db.get_message_by_frame_id(rx_id)
                decoded_data = message.decode(rx_data)
                result = message.decode(rx_data)
                
                msg_stats['rx'] += 1

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

        await asyncio.sleep(RX_sleep)

# Add this new coroutine
async def shutdown_after_time(timeout=10):
    global shutdown_flag
    await asyncio.sleep(timeout)
    shutdown_flag = True

    # pprint.pprint(received_data)
    # save the dictionary as JSON
    CAN_messages_output = 'output/CAN_RX.pkl'
    with open(CAN_messages_output, 'wb') as file:
        # load the list from the file
        pickle.dump(recived_data_dict, file)
        print("CAN messages saved to disk!")
    
    pprint.pprint(msg_stats)
    if verbose:
        # pprint.pprint(msg_stats)
        print("-------------")
        # pprint.pprint(recived_data_dict, indent=4)

async def main():
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

    send_task = asyncio.create_task(send_messages(ch_send, db1, calculated_messages))
    receive_task = asyncio.create_task(receive_messages(ch_receive, db1))
    shutdown_task = asyncio.create_task(shutdown_after_time(TIMEOUT))

    await asyncio.gather(send_task, receive_task)

    ch_send.busOff()
    ch_receive.busOff()

if __name__ == "__main__":
    asyncio.run(main())


#%%