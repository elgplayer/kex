#%%

import can
import time
import cantools
import random



# Vi bestämmer en frekvens för hur ofta vi brus vi skickar
# Sen skickar vi en request (typ ett enhetssteg) som regulatorn gå mot
# Läser av styrvinkeln från STM32 via CAN för att samla in data kring stegsvaret
# Uppreppa med en allt högre frekvens


def random_data(message):
    random_values = {}
    for k,signal in enumerate(message.signals):
        try:
            random_values[signal.name] = random.uniform(float(signal.minimum), float(signal.maximum))
        except Exception as e:
            #print(f"Error at: {k} - {signal}")
            random_values = 0 #random.randint(0, 1)
            pass

    return message.encode(random_values)
dbc_file = 'can1.dbc'
db = cantools.database.load_file(dbc_file)
messages = db.messages

for k,message in enumerate(messages):
    try:
        data = random_data(message)
        message = can.Message(arbitration_id=message.frame_id, data=data, is_extended_id=False)
        #send_message(bus, message)
        #time.sleep(0.1)
        print(message)
    except Exception as e:
        print(f"Error at: {k} - {message} | {e}")
        continue

# %%



