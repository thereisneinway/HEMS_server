import json
from datetime import datetime, timedelta
import time

import mysql

import intelligent as ai
#Function 1: Anti fight between AI and user

AI_CHANGED = [] #[{Device_name: FR, CMD: 0},{Device_name: FL, CMD: 45}...]

#0 -> Normal state                                  / AI can mess       /
#-1 -> AI just changed the device state             / AI can't mess     / Increased by 1 every minute
#1-60 -> When user make adjustment when value = -1  / AI can't mess     / Reduced by 1 every minute

#In function read_file -> append controlled device to AI_CHANGED

#In function Handle_mobile_client -> Add check condition if value = -1 then change to 60

#In funciton evaluate_device_status -> Add check condition if value = 1-60 then don't execute instruction

#In function evaluate_device_status -> if value>0 then reduce value by 1 ,elif value<0 then increase by 1
DEVICES = []
delay_ai = 60
AI_PREDICTED_1 = [] #New
AI_PREDICTED_2 = [] #New
AI_PREDICTED_3 = [] #New
ai_functionality = -1 #Replace - -1 for no AI, 0-2 for different models









#Function 9: Call power diff from file and send to mobile
#INPUT: File / OUTPUT: Mobile socket
#Execute by handle_mobile_client

#Function 10: Mark desired model by user from app
#Change global variable
#Execute by handle_mobile_client


#Task 1: Implement 3 models more













#Function 2: List evaluated result (Cancel, too advance)
'''

def summary_prediction(): # Execute at the end of the day
                          # Return List of dicts of changed status
    AI_PREDICTED.sort(key=lambda x: (x['device'], x['timestamp']))
    last_status = {}
    state_changes = []

    for i in AI_PREDICTED:
        device = i['Device_name']
        timestamp = i['timestamp']
        status = i['Power']

        # If the device is seen for the first time or status changes, record it
        if device not in last_status or last_status[device] != status:
            state_changes.append({
                "timestamp": timestamp,
                "Device_name": device,
                "Power": status
            })
            last_status[device] = status

    save_table_to_file(state_changes)

def flush_predictions(): # Execute after save_table_to_file()
    global AI_PREDICTED
    AI_PREDICTED.clear()

def save_table_to_file(state_changes: []): # Execute after summary_prediction()
    with open('predicted_table.txt', 'w') as devices_file:
        devices_file.write(json.dumps(state_changes))

def load_devices_from_file_and_send_to_mobile(): # Execute on demand from handle_mobile_client
    k = json.load(open("devices.txt"))
'''











'''import pandas as pd
from sklearn.tree import DecisionTreeClassifier
import joblib
from sklearn.model_selection import train_test_split

target = ['light_Shower','light_FR','light_FL','plug_Recirculation fan','plug_Floor lamp','plug_Artificial fan','plug_AC']
data = pd.read_csv('cleaned_Data.csv')
X = data.drop(columns=['light_Shower','light_FR','light_FL','plug_Recirculation fan','plug_Floor lamp','plug_Artificial fan','plug_AC','timestamp'])
y = data[target]
X_train, X_test, y_train, y_test = train_test_split(X,y,test_size=0.1,random_state=0)
clf = DecisionTreeClassifier()

clf.fit(X_train,y_train)
y_pred = clf.predict(X_test)

# VALIDATE MODEL:
from sklearn.metrics import classification_report
print(classification_report(y_test, y_pred))
#print(X_test.head(n=5))
#print(type(X_test))
#print(y_test.head(n=5))
#print(type(y_test))

# TEST MODEL ON ACTUAL DATA:

# Current device stats to proper format for prediction
import json
DEVICES = []
DEVICES = json.load(open("devices.txt"))
#Task: filter data to be in same format as database
def get_prefix(device: dict):
    device_type = device['Device_type']
    device_name = device['Device_name']
    if device_type == "light":
        column_name = "light_" + device_name
        value = device['STATUS'].get('Power')
        data_type = "bool"
        return column_name, value, data_type
    elif device_type == "plug":
        column_name = "plug_" + device_name
        value = device['STATUS'].get('Power')
        data_type = "bool"
        return column_name, value, data_type
    elif device_type == "custom_plug":
        column_name = "cplug_" + device_name
        value = float(device['STATUS'].get('Current'))
        print("appending = "+str(value))
        data_type = "float"
        return column_name, value, data_type
    elif device_type == "temp_sensor":
        column_name = "temp_" + device_name
        value = device['STATUS'].get('Temp')
        data_type = "int"
        return column_name, value, data_type
    elif device_type == "motion_sensor":
        column_name = "motion_" + device_name
        value = device['STATUS'].get('Motion')
        if (value == "pir"): value = 1
        else: value = 0
        data_type = "int"
        return column_name, value, data_type
    elif device_type == "light_sensor":
        column_name = "light_environment"
        value = device['STATUS'].get('brightness')
        if(value=="low"): value = 1
        elif (value == "middle"): value = 2
        elif (value == "high"): value = 3
        else: value = 0
        data_type = "int"
        return column_name, value, data_type
    elif device_type == "door_sensor":
        column_name = "door_" + device_name
        value = device['STATUS'].get('State')
        data_type = "int"
        return column_name, value, data_type
    elif device_type == "master_power_meter":
        column_name = "total_power"
        value = device['STATUS'].get('Power_consumption')
        data_type = "int"
        return column_name, value, data_type
df = pd.DataFrame()
for i in DEVICES:
    if i['Domain'] == "tuya" and i['Device_type'] != "light" and i['Device_type'] != "plug" and i['Device_type'] != 'master_power_meter':
        column_name, value, data_type = get_prefix(i)
        df[column_name] = [value]
print(df.head(n=5))
X_real = df
y_real = clf.predict(X_real)
print(type(y_real))
print(y_real[0][0])




# Export model
#joblib.dump(clf, 'model.pkl')

'''