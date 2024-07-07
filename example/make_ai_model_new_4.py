import numpy as np
import pandas as pd
from sklearn.tree import DecisionTreeClassifier
from sklearn.metrics import classification_report, accuracy_score
import joblib
from sklearn.model_selection import train_test_split
from tqdm import tqdm

pd.set_option('display.max_columns', 13)
#Predict as a schedule chunk

file_paths = ['processed_data_alive.csv', 'processed_data_away.csv', 'processed_data_sleep.csv']
df = [pd.read_csv(file_path) for file_path in file_paths]
data_frames = []
for i, file_path in enumerate(file_paths):
    df = pd.read_csv(file_path)
    df['file_indicator'] = i
    data_frames.append(df)
data = pd.concat(data_frames)
print("TRANING DATA:")
print(data)


devices = ['light_Shower', 'light_FR', 'light_FL', 'plug_AC', 'plug_Recirculation fan', 'plug_Floor lamp',
           'plug_Artificial fan']
sensors = ['temp_Bedroom temp', 'temp_Outdoor temp', 'motion_Motion living room', 'light_environment', 'door_Door',
           'weekday']


def create_aggregated_features_training(data, sensors, devices, target_device):
    aggregated_data = []
    target_data = []

    interval = 144  # Interval for 10-minute data points to cover 24 hours
    ''' NON MODIFIED CODE=
    for i in range(interval * 7, len(data)):
        # Collect data for the past 7 days (24 hours apart)
        past_week_data = []
        for j in range(7):
            if i - j * interval >= 0:
                try:
                    past_week_data.append(data.iloc[i - j * interval])
                except IndexError:
                    continue
    '''
    for i in range(0, int(len(data)/7)):
        # Collect data for the past 7 days (24 hours apart)
        past_week_data = []
        for j in range(7):
            if i * j * interval >= 0:
                try:
                    past_week_data.append(data.iloc[i - j * interval])
                except IndexError:
                    continue

        if len(past_week_data) < 7:
            continue  # Skip if we don't have full week data

        past_week_df = pd.DataFrame(past_week_data)
        aggregated_features = past_week_df[sensors + [d for d in devices if d != target_device]].mean().tolist()

        # Add device status for the next day as target
        target_device_status = data.iloc[i][target_device]

        aggregated_data.append(aggregated_features)
        target_data.append(target_device_status)

    feature_columns = [f'{sensor}' for sensor in sensors + [d for d in devices if d != target_device]]
    return pd.DataFrame(aggregated_data, columns=feature_columns), pd.Series(target_data, name=target_device)
def train_and_evaluate(target_device):
    X, y = create_aggregated_features_training(data, sensors, devices, target_device)
    train_data, test_data, train_targets, test_targets = train_test_split(X, y, test_size=0.2, random_state=42)

    clf = DecisionTreeClassifier()
    clf.fit(train_data, train_targets)

    y_pred = clf.predict(test_data)
    accuracy = accuracy_score(test_targets, y_pred)

    print(f'Accuracy for predicting {target_device}: {accuracy:.2f}')
    return clf

models = {}
for device in devices:
    models[device] = train_and_evaluate(device)
    joblib.dump(models[device], 'model_'+device+'.pkl')



"""
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
    "PASSWORD": "",
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
query = f"
SELECT * FROM main
WHERE timestamp >= '{seven_days_ago.strftime('%Y-%m-%d %H:%M:%S')}'
AND timestamp < '{current_day_midnight.strftime('%Y-%m-%d %H:%M:%S')}'
ORDER BY timestamp;
"
cursor.execute(query)
rows = cursor.fetchall()
column_names = cursor.column_names
df = pd.DataFrame(rows, columns=column_names)

df['timestamp'] = pd.to_datetime(df['timestamp'])
df.set_index('timestamp', inplace=True)


df_resampled = df.resample('10min').first()
print("QUERIED AND RESAMPLE TO 10min DATA:")
print(df_resampled)

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
print("ACTUAL PROCESSED DATA:")
print(df_resampled)

print(f'Processed data has been successfully saved to {csv_file_path}')

#Predict
def create_aggregated_features_for_actual(data, sensors, devices):
    aggregated_data = []
    interval = 144  # Interval for 10-minute data points to cover 24 hours

    for i in range(0, int(len(data)/7)):
        past_week_data = []
        for j in range(7):
            if i * j * interval >= 0:
                try:
                    past_week_data.append(data.iloc[i - j * interval])
                except IndexError:
                    continue

        if len(past_week_data) < 7:
            continue  # Skip if we don't have full week data


        past_week_df = pd.DataFrame(past_week_data)
        aggregated_features = past_week_df[sensors + devices].mean().tolist()
        aggregated_data.append(aggregated_features)
    feature_columns = [f'{sensor}' for sensor in sensors + devices]
    return pd.DataFrame(aggregated_data, columns=feature_columns)

actual_data = pd.read_csv('processed_actual_data_7days.csv')

X_actual = create_aggregated_features_for_actual(actual_data, sensors, devices)

print("AGGREGATED DATA:")
print(X_actual)
X_actual.to_csv("aggregated_actual_data.csv", index=False)

predictions = pd.DataFrame(index=X_actual.index)
for device, model in models.items():
    features = sensors + [d for d in devices if d != device]
    X_actual_filtered = X_actual[features]

    # Make predictions using the corresponding model
    predictions[device] = model.predict(X_actual_filtered)

correction = ['plug_AC']
for column in correction:
    predictions[column] = predictions[column].apply(lambda x: 1 if x == 0 else 0)

predictions = predictions.rename(columns={'light_Shower': 'Shower', 'light_FR': 'FR', 'light_FL': 'FL', 'plug_AC': 'AC', 'plug_Recirculation fan': 'Recirculation fan', 'plug_Floor lamp': 'Floor lamp', 'plug_Artificial fan': 'Artificial fan'})

print("PREDICTION:")
print(predictions)

today = datetime.today().strftime('%Y-%m-%d')
timestamps = pd.date_range(start=f'{today} 00:00:00', periods=144, freq='10min')
predictions['timestamp'] = timestamps

predictions.to_csv('predicted_results.csv', index=False)
print(f'Prediction has been successfully saved to predicted_results.csv')
"""