import time
import random
import asyncio
import pprint

import cantools
from canlib import canlib, Frame

received_data = []
received_data_timestamps = []

# Add a new flag variable here
shutdown_flag = False

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
        
        # TODO: Dont skip
        if message.is_multiplexed():
            continue

        for signal in message.signals:
            rand_value = generate_random_signal_value(signal)
            if rand_value == None:
                continue
            message_data.append(rand_value)
        if message_data == []:
            continue
        random_data[message.name] = {'data': message_data, 'frame_id': message.frame_id}
    return random_data

def send_virtual_can_message(ch, frame_id, data, dlc):
    data += b'\x00' * (dlc - len(data))
    ch.write(Frame(id_=frame_id, data=data, dlc=len(data)))

################################################################################

async def send_messages(ch, db):
    global shutdown_flag
    while not shutdown_flag:
        random_signal_data = generate_random_data_for_all_signals(db)
        for k, x in enumerate(random_signal_data):
            selected_frame = random_signal_data[x]
            frame_id = selected_frame['frame_id']
            try:
                data = [min(max(value, 0), 255) for value in selected_frame['data']]
                message = db.get_message_by_frame_id(frame_id)

                #print(f"Sent virtual CAN message with ID: {frame_id} and data: {data} | {x}")
                send_virtual_can_message(ch, frame_id, data, message.length)
            except Exception as e:
                pass
        await asyncio.sleep(0.1)


async def receive_messages(ch, db):
    db_frame_ids = [message.frame_id for message in db.messages]

    global shutdown_flag
    while not shutdown_flag:
        if canlib.Stat.RX_PENDING in ch.readStatus():
            rx = ch.read()
            rx_id = rx.id
            rx_data = bytes(rx.data)
            
            if rx_id in db_frame_ids:
                message = db.get_message_by_frame_id(rx_id)
                decoded_data = message.decode(rx_data)
                
                result = message.decode(rx_data)
                print(f"Received virtual CAN message with ID: {rx_id} and data: {decoded_data} | {message.name}")
                received_data.append({'message_name': message.name, 'data': result})
                received_data_timestamps.append(time.time())     
                
        await asyncio.sleep(0.1)

# Add this new coroutine
async def shutdown_after_time(timeout=10):
    global shutdown_flag
    await asyncio.sleep(timeout)
    shutdown_flag = True
    
    pprint.pprint(received_data)


async def main():
    channel = 0
    chd = canlib.ChannelData(channel)
    print("CANlib version: v{}".format(chd.dll_product_version))
    print("canlib dll version: v{}".format(chd.dll_file_version))
    print("Using channel: {ch}, EAN: {ean}".format(ch=chd.channel_name, ean=chd.card_upc_no))

    ch_send = canlib.openChannel(channel, canlib.canOPEN_ACCEPT_VIRTUAL)
    ch_send.setBusOutputControl(canlib.canDRIVER_NORMAL)
    ch_send.setBusParams(canlib.canBITRATE_500K)
    ch_send.busOn()

    ch_receive = canlib.openChannel(channel + 1, canlib.canOPEN_ACCEPT_VIRTUAL)
    ch_receive.setBusOutputControl(canlib.canDRIVER_NORMAL)
    ch_receive.setBusParams(canlib.canBITRATE_500K)
    ch_receive.busOn()

    db1 = cantools.database.load_file(r"can1.dbc")

    send_task = asyncio.create_task(send_messages(ch_send, db1))
    receive_task = asyncio.create_task(receive_messages(ch_receive, db1))
    shutdown_task = asyncio.create_task(shutdown_after_time(10))

    await asyncio.gather(send_task, receive_task)

    ch_send.busOff()
    ch_receive.busOff()

if __name__ == "__main__":
    asyncio.run(main())