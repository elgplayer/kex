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
    for signal in message.signals:
        min_value = float(signal.minimum) if signal.minimum is not None else 0
        max_value = float(signal.maximum) if signal.maximum is not None else 1

        if signal.is_signed:
            min_value = max(min_value, -2**(signal.length-1))
            max_value = min(max_value, 2**(signal.length-1) - 1)

        

        if signal.is_float:
            value = random.uniform(min_value, max_value)
        else:
            value = random.randint(int(min_value), int(max_value))
            
        print(min_value, " | ", max_value, "||", value)

        random_values[signal.name] = value

    # Ensure all signals in the message are included in the dictionary
    for signal in message.signals:
        if signal.name not in random_values:
            random_values[signal.name] = 0

  
    return random_values




dbc_file = 'can1.dbc'
db = cantools.database.load_file(dbc_file)
messages = db.messages

for k,message in enumerate(messages):
    try:
        data = random_data(message)
        encoded_data = message.encode(data)  # Encode the data
        message = can.Message(arbitration_id=message.frame_id, data=encoded_data, is_extended_id=False)
    except Exception as e:
        data = 0
        print(f"Error at: {k} - {message} | {e}")
        continue
    
    #print(message)

# %%



