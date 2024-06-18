import pandas as pd
from sklearn.tree import DecisionTreeClassifier
from sklearn.ensemble import RandomForestClassifier
from sklearn.neural_network import MLPClassifier
import joblib
from sklearn.model_selection import train_test_split

target = ['light_Shower','light_FR','light_FL','plug_Recirculation fan','plug_Floor lamp','plug_Artificial fan','plug_AC']
data = pd.read_csv('cleaned_Data.csv')
X = data.drop(columns=['light_Shower','light_FR','light_FL','plug_Recirculation fan','plug_Floor lamp','plug_Artificial fan','plug_AC','timestamp'])
y = data[target]
X_train, X_test, y_train, y_test = train_test_split(X,y,test_size=0.1,random_state=0)
clf = MLPClassifier()

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
joblib.dump(clf, 'model_LTSM.pkl')