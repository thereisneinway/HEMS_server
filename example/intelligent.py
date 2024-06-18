import json

import pandas as pd
import joblib
from datetime import datetime, timedelta
import time
import mysql.connector
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

def calculate_device_average_power(device: dict):
    if device["Device_type"] == "light":
        return 100
    elif device["Device_type"] == "plug":
        return 300
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