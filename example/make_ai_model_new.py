import numpy as np
import pandas as pd
from sklearn.tree import DecisionTreeClassifier
from sklearn.ensemble import RandomForestClassifier
from sklearn.neural_network import MLPClassifier
from sklearn.metrics import classification_report
import joblib
from sklearn.model_selection import train_test_split
from tqdm import tqdm


#Predict as a schedule chunk

df = pd.read_csv('processed_data.csv')
print(df)


input_columns = ['weekday', 'temp_Bedroom temp', 'temp_Outdoor temp', 'motion_Motion living room', 'light_environment', 'door_Door']
target_columns = ['light_Shower', 'light_FR', 'light_FL', 'plug_AC', 'plug_Recirculation fan', 'plug_Floor lamp', 'plug_Artificial fan']


for col in input_columns + target_columns:
    if col not in df.columns:
        print(f"Column {col} is not found in the DataFrame. Please check the column names.")

def create_sequences(data, seq_length):
    sequences = []
    targets = []
    for i in tqdm(range(len(data) - seq_length * 2), desc="Creating sequences"):
        seq_in = data.iloc[i:i + seq_length][input_columns].values
        seq_out = data.iloc[i + seq_length:i + seq_length * 2][target_columns].values
        sequences.append(seq_in)
        targets.append(seq_out)
    return np.array(sequences), np.array(targets)

seq_length = 60
X, y = create_sequences(df, seq_length)

X_train, X_test, y_train, y_test = train_test_split(X,y,test_size=0.2,random_state=0)
X_train_flat = X_train.reshape(X_train.shape[0], -1)
X_test_flat = X_test.reshape(X_test.shape[0], -1)
y_train_flat = y_train.reshape(y_train.shape[0], -1)
y_test_flat = y_test.reshape(y_test.shape[0], -1)


clf = DecisionTreeClassifier()
clf.fit(X_train_flat, y_train_flat)


def predict_parallel(model, data):
    return model.predict(data)


num_cores = -1  # Use all available cores
y_pred_flat = joblib.Parallel(n_jobs=num_cores)(
    joblib.delayed(predict_parallel)(clf, [X_test_flat[i]]) for i in tqdm(range(X_test_flat.shape[0]), desc="Predicting")
)
y_pred_flat = np.vstack(y_pred_flat)
y_pred = y_pred_flat.reshape(y_test.shape)

# VALIDATE MODEL:
print("Predictions shape:", y_pred.shape)
print("Test data shape:", y_test.shape)
for i in range(3):
    print(f"Predicted: {y_pred[i][0]}")
    print(f"Actual: {y_test[i][0]}")
    print()

for i, target in enumerate(target_columns):
    print(f"Confusion Matrix and Classification Report for {target}:")

    # Binarize the outputs for confusion matrix and classification report
    y_true = (y_test[:, i] > 0.5).astype(int)
    y_pred_binary = (y_pred[:, i] > 0.5).astype(int)

    # Print confusion matrix
    #cm = confusion_matrix(y_true, y_pred_binary)
    #print(f"Confusion Matrix for {target}:\n{cm}\n")

    # Print classification report
    cr = classification_report(y_true, y_pred_binary)
    print(f"Classification Report for {target}:\n{cr}\n")

# TEST MODEL ON ACTUAL DATA:

'''
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
'''



# Export model
#joblib.dump(clf, 'model_LTSM.pkl')