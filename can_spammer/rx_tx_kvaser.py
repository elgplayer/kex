
import asyncio
import random
from datetime import datetime
import time

import cantools
from canlib import canlib, Frame



received_data = dict()
steering_angle_data = []
sent_data = []

####################################################################

def generate_random_signal_value(signal):
    if signal.minimum == None:
        return None
    value = random.uniform(signal.minimum, signal.maximum)
    if signal.is_float:
        return value
    else:
        return int(value)

def generate_random_data_for_all_signals(db):
    random_data = {}
    for message in db.messages:
        message_data = []
        for signal in message.signals:
            rand_value = generate_random_signal_value(signal)
            if rand_value == None:
                continue
            message_data.append(rand_value)
        if message_data == []:
            continue
        random_data[message.name] = {'data': message_data, 'frame_id': message.frame_id}
    return random_data


def send_virtual_can_message(ch, frame_id, data):
    ch.write(Frame(id_=frame_id, data=data, dlc=len(data)))

####################################################################

async def receive_can_messages(ch, db, steering_angle_queue):
    
    db_frame_ids = [message.frame_id for message in db.messages]

    while True:
        print(canlib.Stat.RX_PENDING, ch.readStatus())
        while canlib.Stat.RX_PENDING in ch.readStatus():
            rx = ch.read()
            rx_id = rx.id
            rx_data = bytes(rx.data)
            
            if rx_id in db_frame_ids:
                message = db.get_message_by_frame_id(rx_id)
                result = message.decode(rx_data)
                
                print(message.name)
                
                try:
                    received_data[message.name].update(result)
                except KeyError:
                    received_data[message.name] = result

                if message.name == "steering_angle_1":
                    print("RECIVED!")
                    timestamp = datetime.now()
                    await steering_angle_queue.put((timestamp, result))
            
        await asyncio.sleep(0.5)
            
            
            
# random_signal_data = generate_random_data_for_all_signals(db)
# for k, x in enumerate(random_signal_data):
#     selected_frame = random_signal_data[x]
#     frame_id = selected_frame['frame_id']
#     try:
#         data = [min(max(value, 0), 255) for value in selected_frame['data']]
#         print(f"Sent virtual CAN message with ID: {frame_id} and data: {data} | {x}")
#         send_virtual_can_message(ch, selected_frame['frame_id'], data)
#     except Exception as e:
#         pass
            


async def send_can_messages(ch, db, steering_angle_queue):
    
    db_frame_ids = [ message.frame_id for message in db.messages ]
    
    while True:
        
        random_signal_data = generate_random_data_for_all_signals(db)
        for k,x in enumerate(random_signal_data):
            selected_frame = random_signal_data[x]
            frame_id = selected_frame['frame_id']
            try:
                data = [min(max(value, 0), 255) for value in selected_frame['data']]
                print(f"Sent virtual CAN message with ID: {frame_id} and data: {data} | {x}")
                send_virtual_can_message(ch, selected_frame['frame_id'], data)
            except Exception as e:
                pass
                

        await asyncio.sleep(1)
        
async def main():
    channel = 0
    chd = canlib.ChannelData(channel)
    print("CANlib version: v{}".format(chd.dll_product_version))
    print("canlib dll version: v{}".format(chd.dll_file_version))
    print("Using channel: {ch}, EAN: {ean}".format(ch=chd.channel_name, ean=chd.card_upc_no))

    ch = canlib.openChannel(channel, canlib.canOPEN_ACCEPT_VIRTUAL)
    ch.setBusOutputControl(canlib.canDRIVER_NORMAL)
    ch.setBusParams(canlib.canBITRATE_500K)
    ch.busOn()

    db1 = cantools.database.load_file(r"can1.dbc")
    db1_frame_ids = [ message.frame_id for message in db1.messages ]
    
    steering_angle_queue = asyncio.Queue()

    send_task = asyncio.create_task(send_can_messages(ch, db1, steering_angle_queue))
    receive_task = asyncio.create_task(receive_can_messages(ch, db1, steering_angle_queue))

    await asyncio.gather(send_task, receive_task)

    ch.busOff()

if __name__ == "__main__":
    asyncio.run(main())
    
    #%%
    
    