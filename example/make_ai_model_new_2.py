import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.tree import DecisionTreeClassifier
from sklearn.metrics import accuracy_score

# Predict individual device real time


file_path = 'processed_data.csv'
df = pd.read_csv(file_path)


devices = ['light_Shower', 'light_FR', 'light_FL', 'plug_AC', 'plug_Recirculation fan', 'plug_Floor lamp',
           'plug_Artificial fan']
sensors = ['temp_Bedroom temp', 'temp_Outdoor temp', 'motion_Motion living room', 'light_environment', 'door_Door',
           'day']



def train_and_evaluate(df, target_device):
    features = sensors + [device for device in devices if device != target_device]

    X = df[features]
    y = df[target_device]

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.3, random_state=1)

    model = DecisionTreeClassifier(random_state=1)
    model.fit(X_train, y_train)

    y_pred = model.predict(X_test)
    accuracy = accuracy_score(y_test, y_pred)

    print(f'Accuracy for predicting {target_device}: {accuracy:.2f}')

    return model


models = {}
for device in devices:
    models[device] = train_and_evaluate(df, device)
