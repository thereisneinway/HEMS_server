import pandas as pd
import joblib
import database_instructions as da


def evaluate_with_decision_tree(DEVICES: list):
    model = joblib.load("model.pkl")
    df = pd.DataFrame()
    y_list = []
    target = []
    for i in DEVICES:
        if i['Domain'] == "tuya" and i['Device_type'] != "light" and i['Device_type'] != "plug" and i[
            'Device_type'] != 'master_power_meter':
            column_name, value, data_type = da.get_prefix(i)
            df[column_name] = [value]
        elif i['Domain'] == "tuya" and (i['Device_type'] == "light" or i['Device_type'] == "plug"):
            target.append(i['Device_name'])

    X_real = df
    y_real = model.predict(X_real)
    for i in range(len(y_real[0])):
        y_list.append({"Device_name": target[i], "Power": bool(y_real[0][i])})
    return y_list
