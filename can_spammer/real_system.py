#%%
import time
import random
import asyncio
import pprint
import json
from io import StringIO
import decimal

import cantools
from canlib import canlib, Frame



received_data = []
received_data_timestamps = []
recived_data_dict = {}
shutdown_flag = False

##########
# CONFIG #
##########
virtual = True
verbose = False

# Add a new flag variable here

def generate_random_data_for_all_signals(db):
    random_data = {}
    for message in db.messages:
        message_data = {}
        # TODO: Don't skip
        if message.is_multiplexed():
            print(f"SKIP | {message.name}")
            continue
        for signal in message.signals:
            rand_value = generate_random_signal_value(signal)
            if rand_value is None:
                print(f"RAND VALUE = 0 | {signal.name}")
                #continue
                #rand_value = 0
            message_data[signal.name] = rand_value
        if not message_data:
            continue
        random_data[message.name] = {'data': message_data, 'frame_id': message.frame_id}
    return random_data


def generate_random_signal_value(signal):
    if signal.length == 1:
        return random.choice([0, 1])

    min_value = signal.minimum
    max_value = signal.maximum

    if min_value is not None and max_value is not None:
        random_value = random.uniform(min_value, max_value)

        if signal.scale is not None and signal.scale > 0:
            decimal_places = abs(decimal.Decimal(signal.scale).as_tuple().exponent)
            rounded_value = round(random_value, decimal_places)
        else:
            rounded_value = round(random_value)

        return rounded_value
    else:
        return None


def send_virtual_can_message(ch, frame_id, data, dlc):
    data += b'\x00' * (dlc - len(data))
    ch.write(Frame(id_=frame_id, data=data, dlc=len(data)))

################################################################################

async def send_messages(ch, db):
    iteration = 0
    global shutdown_flag
    while not shutdown_flag:
        random_signal_data = generate_random_data_for_all_signals(db)
        
        for k, x in enumerate(random_signal_data):
            selected_frame = random_signal_data[x]
            frame_id = selected_frame['frame_id']
            message = db.get_message_by_frame_id(frame_id)
            
            if verbose:
                print(f"Sent virtual CAN message with ID: {frame_id} and data: {selected_frame['data']} | {x}")
            # try:
            #data = [min(max(value, 0), 255) for value in selected_frame['data']]
            
            message = db.get_message_by_frame_id(frame_id)
            data =  message.encode(selected_frame['data'])

            #print(f"Sent virtual CAN message with ID: {frame_id} and data: {data} | {x}")
            send_virtual_can_message(ch, frame_id, data, message.length)
            # except Exception as e:
            #     print(f"Error: {e}")
            #     pass
        await asyncio.sleep(1)
        if verbose:
            print(f"Iteration: {iteration}")
        iteration += 1


async def receive_messages(ch, db):
    db_frame_ids = [message.frame_id for message in db.messages]

    global shutdown_flag
    while not shutdown_flag:
        if canlib.Stat.RX_PENDING in ch.readStatus():
            rx = ch.read()
            rx_id = rx.id
            rx_data = bytes(rx.data)
            
            if rx_id in db_frame_ids:
                time_recived = time.time()
                message = db.get_message_by_frame_id(rx_id)
                decoded_data = message.decode(rx_data)
                result = message.decode(rx_data)
                
                if message.name not in recived_data_dict:
                    recived_data_dict[str(message.name)] = {
                        'data': [decoded_data],
                        'time': [time_recived]
                    }
                else:
                    recived_data_dict[message.name]['data'].append(decoded_data)
                    recived_data_dict[message.name]['time'].append(time_recived)

                #print(f"Received CAN message with ID: {rx_id} and data: {decoded_data} | {message.name}")
                received_data.append({'message_name': message.name, 'data': result})
                received_data_timestamps.append(time.time())     
        
        await asyncio.sleep(0.01)

# Add this new coroutine
async def shutdown_after_time(timeout=10):
    global shutdown_flag
    await asyncio.sleep(timeout)
    shutdown_flag = True
    
    


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

    send_task = asyncio.create_task(send_messages(ch_send, db1))
    receive_task = asyncio.create_task(receive_messages(ch_receive, db1))
    shutdown_task = asyncio.create_task(shutdown_after_time(3))

    await asyncio.gather(send_task, receive_task)

    ch_send.busOff()
    ch_receive.busOff()

if __name__ == "__main__":
    asyncio.run(main())


#%%