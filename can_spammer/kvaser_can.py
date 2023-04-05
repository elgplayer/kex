#%%

import time
import random


import cantools
from canlib import canlib, Frame


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

def main():
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

    while True:
        
        random_signal_data = generate_random_data_for_all_signals(db1)
        
        for k,x in enumerate(random_signal_data):
            
            selected_frame = random_signal_data[x]
            frame_id = selected_frame['frame_id']
            
            try:
                data = [min(max(value, 0), 255) for value in selected_frame['data']]
                print(f"Sent virtual CAN message with ID: {frame_id} and data: {data} | {x}")
                send_virtual_can_message(ch, selected_frame['frame_id'], data)
            except Exception as e:
                pass
                
        time.sleep(0.1)

    ch.busOff()

if __name__ == "__main__":
    main()