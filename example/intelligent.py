
import pandas as pd
import joblib
from datetime import datetime
import database_instructions as da



def evaluate_with_model(model_file: str,DEVICES: list):
    model = joblib.load(model_file)
    df = pd.DataFrame()
    y_list = {}
    target = []
    for i in DEVICES:
        if i['Domain'] == "tuya" and i['Device_type'] != "light" and i['Device_type'] != "plug" and i['Device_type'] != 'master_power_meter':
            column_name, value, data_type = da.get_prefix(i)
            df[column_name] = [value]
        elif i['Domain'] == "tuya" and (i['Device_type'] == "light" or i['Device_type'] == "plug"):
            target.append(i['Device_name'])

    X_real = df
    y_real = model.predict(X_real)
    for i in range(len(y_real[0])):
        y_list[target[i]] = bool(y_real[0][i])
    return y_list




def calculate_runtime(runtime_table: []): #Hardcoded devices
    devices = ["Shower", "FR", "FL", "AC", "Recirculation fan", "Floor lamp",
               "Artificial fan"]
    device_runtime = {device: 0 for device in devices}
    for i in range(1, len(runtime_table)):
        current_entry = runtime_table[i]
        previous_entry = runtime_table[i - 1]

        time_diff = (datetime.strptime(current_entry['timestamp'],'%Y/%m/%d %H:%M:%S') - datetime.strptime(previous_entry['timestamp'],'%Y/%m/%d %H:%M:%S')).total_seconds() / 3600

        for device in devices:
            if previous_entry[device] == 1:
                device_runtime[device] += time_diff
    output = [{"Device_name": device, "runtime": runtime} for device, runtime in device_runtime.items()]

    return output  # [{"Device_name": -- , "runtime": --},...]

def calculate_runtime_real(runtime_table: []): #Hardcoded devices
    devices = ["Shower", "FR", "FL", "AC", "Recirculation fan", "Floor lamp",
               "Artificial fan"]
    devices_andType = ["light_Shower", "light_FR", "light_FL", "plug_AC", "plug_Recirculation fan", "plug_Floor lamp",
               "plug_Artificial fan"]
    device_runtime = {device: 0 for device in devices}
    for i in range(1, len(runtime_table)):
        current_entry = runtime_table[i]
        previous_entry = runtime_table[i - 1]
        time_diff = (current_entry['timestamp'] - previous_entry['timestamp']).total_seconds() / 3600
        for i in range(len(devices)):
            if previous_entry[devices_andType[i]] == 1:
                device_runtime[devices[i]] += time_diff
    output = [{"Device_name": device, "runtime": runtime} for device, runtime in device_runtime.items()]

    return output  # [{"Device_name": -- , "runtime": --},...]

def calculate_device_average_power(device: dict):
    if device["Device_type"] == "light":
        return 150
    elif device["Device_name"] == "AC":
        return 5000
    elif device["Device_name"] == "Recirculation fan":
        return 450
    elif device["Device_name"] == "Floor lamp":
        return 300
    elif device["Device_name"] == "Artificial fan":
        return 500
    else: return 0
def calculate_each_devices_consumption(devices_runtime: [], devices: []):
    devices_consumption = []
    for entry in devices_runtime:
        device = next((sub for sub in devices if sub['Device_name'] == entry["Device_name"]), None)
        devices_consumption.append({"Device_name": entry["Device_name"], "Consumption": entry["runtime"]*calculate_device_average_power(device)})
    return devices_consumption
def calculate_total_consumption(devices_consumption: []):
    sum = 0
    for i in devices_consumption:
        sum += i['Consumption']
    return sum


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

def evaluate_schedule():

    devices = ['light_Shower', 'light_FR', 'light_FL', 'plug_AC', 'plug_Recirculation fan', 'plug_Floor lamp',
               'plug_Artificial fan']
    sensors = ['temp_Bedroom temp', 'temp_Outdoor temp', 'motion_Motion living room', 'light_environment', 'door_Door',
               'weekday']
    actual_data = pd.read_csv('processed_actual_data_7days.csv')
    X_actual = create_aggregated_features_for_actual(actual_data, sensors, devices)
    predictions = pd.DataFrame(index=X_actual.index)

    #Import model
    models = {}
    for device in devices:
        models[device] = joblib.load('model_'+device+'.pkl')

    for device, model in models.items():
        features = sensors + [d for d in devices if d != device]
        X_actual_filtered = X_actual[features]

        predictions[device] = model.predict(X_actual_filtered)

    correction = ['plug_AC']
    for column in correction:
        predictions[column] = predictions[column].apply(lambda x: 1 if x == 0 else 0)

    predictions = predictions.rename(
        columns={'light_Shower': 'Shower', 'light_FR': 'FR', 'light_FL': 'FL', 'plug_AC': 'AC',
                 'plug_Recirculation fan': 'Recirculation fan', 'plug_Floor lamp': 'Floor lamp',
                 'plug_Artificial fan': 'Artificial fan'})
    today = datetime.today().strftime('%Y-%m-%d')
    timestamps = pd.date_range(start=f'{today} 00:00:00', periods=144, freq='10min')
    predictions['timestamp'] = timestamps
    predictions.to_csv('predicted_results.csv', index=False)

def convert_csv_to_json():
    df = pd.read_csv('predicted_results.csv')

    # Function to convert numeric values to boolean
    def convert_to_boolean(value):
        return value == 1

    # Apply the conversion function to the appropriate columns
    for column in df.columns[:-1]:  # Exclude the timestamp column
        df[column] = df[column].apply(convert_to_boolean)

    # Format the timestamp column as required
    df['timestamp'] = pd.to_datetime(df['timestamp']).dt.strftime('%Y/%m/%d %H:%M:%S')

    # Convert the DataFrame to a list of dictionaries
    result_dict = df.to_dict(orient='records')
    return result_dict

def query_specific_instruction(input_time: datetime):
    df = pd.read_csv('predicted_results.csv')

    # Function to convert numeric values to boolean
    def convert_to_boolean(value):
        return value == 1

    # Apply the conversion function to the appropriate columns
    for column in df.columns[:-1]:  # Exclude the timestamp column
        df[column] = df[column].apply(convert_to_boolean)

    # Format the timestamp column as required
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    df['time_only'] = df['timestamp'].dt.strftime('%H:%M')
    input_time_only = pd.to_datetime(input_time).strftime('%H:00')
    matched_row = df[df['time_only'] == input_time_only]

    # Convert the DataFrame to a list of dictionaries
    if not matched_row.empty:
        result_dict = matched_row.drop(columns='time_only').to_dict(orient='records')[0]
        return result_dict
    else:
        return None