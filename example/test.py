import json
from datetime import datetime, timedelta
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

DEVICES = [] #Concate
AI_PREDICTED = [] #New
ai_functionality = 0 #Replace - 0 for no AI, 1-3 for different models
#Function 1: Predict schedule of operating time of devices
#INPUT: sensors from database table / OUTPUT: List of dict of predicted operating schedule (saved for later)
#Execute every n seconds (on separate thread)
def append_prediction():
    predicted_now = ai.evaluate_with_decision_tree(DEVICES)
    predicted_now['timestamp'] = datetime.now().strftime('%H:%M:%S')
    AI_PREDICTED.append(predicted_now)

#Function 2: Calculate mean power of each devices
#INPUT: fn5 / OUTPUT: power consumption of the device
#Execute by fn4
def calculate_device_average_power(device: dict):
    if device["Device_type"] == "light":
        return 100
    elif device["Device_type"] == "plug":
        return 300
    else: return 0

#Function 3: Find total runtime of each devices from fn1
#INPUT: Database table / OUTPUT: List of dict of runtime of each devices
#Execute by fn4
def calculate_predicted_runtime(MySQL_connection_details: dict): #function from chatGPT and reconstruction, not revise yet
    #TODO: query from database for today only
    MySQL = mysql.connector.connect(host=MySQL_connection_details.get("HOST"),
                                    port=MySQL_connection_details.get("PORT"),
                                    database=MySQL_connection_details.get("DATABASE_NAME"),
                                    user=MySQL_connection_details.get("USERNAME"),
                                    password=MySQL_connection_details.get("PASSWORD"),
                                    ssl_ca=MySQL_connection_details.get("CA_path"), connection_timeout=180000)
    table_name = MySQL_connection_details.get("TABLE_NAME")
    cursor = MySQL.cursor(dictionary=True)
    cursor.execute("select database();")
    cursor.fetchone()
    cursor.execute("SHOW TABLES LIKE '" + table_name + "'")
    result = cursor.fetchone()
    if not result:
        raise Exception("Table not found")

    query = """
        SELECT *
        FROM (
            SELECT *,
                   LAG(device1) OVER (ORDER BY timestamp) AS prev_device1,
                   LAG(device2) OVER (ORDER BY timestamp) AS prev_device2,
                   -- Add more devices as needed
                   LAG(deviceN) OVER (ORDER BY timestamp) AS prev_deviceN
            FROM devices
        ) subquery
        WHERE (device1 != prev_device1)
           OR (device2 != prev_device2)
           -- Add more devices as needed
           OR (deviceN != prev_deviceN);
        """

    # Execute the query
    cursor.execute(query)

    # Fetch all rows from the executed query
    data = cursor.fetchall()

    # Close the cursor and connection
    cursor.close()
    MySQL.close()

    data.sort(key=lambda x: (x['device'], x['timestamp']))
    runtime = {}
    last_status_time = {}
    for entry in data:
        device = entry['device']
        timestamp = datetime.strptime(entry['timestamp'], "%Y-%m-%d %H:%M:%S")
        status = entry['status']#unfamilar

        if device not in runtime:
            runtime[device] = timedelta()
            last_status_time[device] = {"status": status, "timestamp": timestamp}
        else:
            last_status = last_status_time[device]["status"]
            last_timestamp = last_status_time[device]["timestamp"]

            if last_status == 1:
                runtime[device] += timestamp - last_timestamp

            last_status_time[device] = {"status": status, "timestamp": timestamp}

    return runtime
    #[{"Device_name": -- , "hour": --},{"Device_name": -- , "hour": --}]

#Function 4: Find power of each devices for a day from fn2+fn3
#INPUT fn2,fn3 / OUTPUT: List of dict of power consumption of each devices if device operate at predicted time
#Execute when prediction performs
def calculate_predicted_consumption(devices_runtime: []):
    devices_consumption = []
    for entry in devices_runtime:
        device = next((sub for sub in DEVICES if sub['Device_name'] == entry["Devices_name"]), None)
        devices_consumption.append({"Devices_name": entry["Devices_name"], "Consumption": entry["hour"]*calculate_device_average_power(device)})

#Fucntion 5: Calculate total power of each devices in real scenario
#INPUT n/a data from database table / OUTPUT: List of dict of total power consumption of each device in that day
#Execute by fn3 , fn6
def calculate_each_device_consumption():
    print("A")

#Function 6: Calculate diff power in real scenario and predicted from fn5
#INPUT fn4, fn5 / OUTPUT: List of dict of difference in power consumption of each device
#Execute by fn7
def calculate_diff_average_power():
    print("A")

#Function 7: Append power diff to file, to handle different model
#INPUT: none / OUTPUT: File
#Execute at the end of the day x times (x = no. of model)

#Function 8: Call power diff from file and send to mobile
#INPUT: File / OUTPUT: Mobile socket
#Execute by handle_mobile_client

#Function 9: Mark desired model by user from app
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