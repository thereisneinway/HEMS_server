import numpy as np
import pandas as pd
from sklearn.tree import DecisionTreeClassifier
from sklearn.metrics import classification_report, accuracy_score
import joblib
from sklearn.model_selection import train_test_split
from tqdm import tqdm


#Predict as a schedule chunk

file_paths = ['processed_data_alive.csv', 'processed_data_away.csv', 'processed_data_sleep.csv']
df = [pd.read_csv(file_path) for file_path in file_paths]
data_frames = []
for i, file_path in enumerate(file_paths):
    df = pd.read_csv(file_path)
    df['file_indicator'] = i
    data_frames.append(df)
data = pd.concat(data_frames)
print(data)


devices = ['light_Shower', 'light_FR', 'light_FL', 'plug_AC', 'plug_Recirculation fan', 'plug_Floor lamp',
           'plug_Artificial fan']
sensors = ['temp_Bedroom temp', 'temp_Outdoor temp', 'motion_Motion living room', 'light_environment', 'door_Door',
           'weekday']


def train_and_evaluate(target_device):
    features = sensors + [device for device in devices if device != target_device]

    train_data, test_data = train_test_split(data, test_size=0.2, stratify=data['file_indicator'])

    X_train = train_data[features]
    y_train = train_data[target_device]
    X_test = test_data[features]
    y_test = test_data[target_device]

    clf = DecisionTreeClassifier()
    clf.fit(X_train, y_train)

    y_pred = clf.predict(X_test)
    accuracy = accuracy_score(y_test, y_pred)

    print(f'Accuracy for predicting {target_device}: {accuracy:.2f}')

    return clf

models = {}
for device in devices:
    models[device] = train_and_evaluate(device)

# TEST MODEL ON ACTUAL DATA:

# Import data
import mysql.connector
from datetime import datetime, timedelta
MySQL_connection_details = {
    "HOST": "db-mysql-sgp1-38053-do-user-15940348-0.c.db.ondigitalocean.com",
    "PORT": 25060,
    "DATABASE_NAME": "defaultdb",
    "TABLE_NAME": "main",
    "ENERGY_TABLE_NAME": "energy_test",
    "USERNAME": "doadmin",
    "PASSWORD": "AVNS_Ph0KRopLI4DcuwpAU6x",
    "CA_Path": "/ca-certificate.crt"
}
conn = mysql.connector.connect(host=MySQL_connection_details.get("HOST"),
                                    port=MySQL_connection_details.get("PORT"),
                                    database=MySQL_connection_details.get("DATABASE_NAME"),
                                    user=MySQL_connection_details.get("USERNAME"),
                                    password=MySQL_connection_details.get("PASSWORD"),
                                    ssl_ca=MySQL_connection_details.get("CA_path"), connection_timeout=180000)
cursor = conn.cursor()
seven_days_ago = (datetime.now() - timedelta(days=7)).replace(hour=0, minute=0, second=0, microsecond=0)
current_day_midnight = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
query = f"""
SELECT * FROM main
WHERE timestamp >= '{seven_days_ago.strftime('%Y-%m-%d %H:%M:%S')}'
AND timestamp < '{current_day_midnight.strftime('%Y-%m-%d %H:%M:%S')}'
ORDER BY timestamp;
"""
cursor.execute(query)
rows = cursor.fetchall()
column_names = cursor.column_names
df = pd.DataFrame(rows, columns=column_names)

df['timestamp'] = pd.to_datetime(df['timestamp'])
df.set_index('timestamp', inplace=True)


df_resampled = df.resample('10min').first()
print(df_resampled.head())
columns_to_drop = ['plug_book', 'total_power', 'cplug_peaky']
df_resampled.drop(columns=columns_to_drop, inplace=True)

df_resampled['weekday'] = df_resampled.index.to_series().apply(lambda x: 1 if x.weekday() < 5 else 0)
df_resampled.reset_index(inplace=True)

df_resampled.drop(columns=['timestamp'], inplace=True)

csv_file_path = 'actual_data_7days.csv'
df_resampled.to_csv(csv_file_path, index=False)

cursor.close()
conn.close()

print(f'Data has been successfully saved to {csv_file_path}')

#Processing actual data

df_resampled['temp_Bedroom temp'] = df_resampled['temp_Bedroom temp'].replace(0, np.nan)
df_resampled['temp_Outdoor temp'] = df_resampled['temp_Outdoor temp'].replace(0, np.nan)
df_resampled['light_environment'] = df_resampled['light_environment'].replace(0, np.nan)

max_temp = 438
min_temp = 206

df_resampled['light_environment']  = pd.to_numeric(df_resampled['light_environment'] , errors='coerce')

df_resampled['temp_Bedroom temp'] = (df_resampled['temp_Bedroom temp'] - min_temp)/(max_temp-min_temp)
df_resampled['temp_Outdoor temp'] = (df_resampled['temp_Outdoor temp'] - min_temp)/(max_temp-min_temp)
df_resampled['light_environment'] = (df_resampled['light_environment'] - 1)/(3-1)

csv_file_path = 'processed_actual_data_7days.csv'
df_resampled.to_csv(csv_file_path, index=False)

print(f'Processed data has been successfully saved to {csv_file_path}')

#Predict
actual_data = pd.read_csv('processed_actual_data_7days.csv')
predictions = pd.DataFrame(index=actual_data.index)
for device, model in models.items():
    # Extract the relevant features for the current device
    features = sensors + [d for d in devices if d != device]
    X_actual = actual_data[features]

    # Make predictions using the corresponding model
    predictions[device] = model.predict(X_actual)


predictions.to_csv('predicted_results.csv', index=False)
print(f'Prediction has been successfully saved to predicted_results.csv')

'''
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
'''