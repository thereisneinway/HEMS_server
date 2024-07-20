import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import classification_report, accuracy_score
from sklearn import metrics
from keras.models import Sequential
from keras.layers import LSTM, Dense
from keras.callbacks import EarlyStopping
import warnings
warnings.filterwarnings("ignore")

file_paths = ['processed_data_alive.csv', 'processed_data_away.csv', 'processed_data_sleep.csv']
data_frames = []
for i, file_path in enumerate(file_paths):
    df = pd.read_csv(file_path)
    df['file_indicator'] = i
    data_frames.append(df)
data = pd.concat(data_frames)



devices = ['light_Shower', 'light_FR', 'light_FL', 'plug_AC', 'plug_Recirculation fan', 'plug_Floor lamp',
           'plug_Artificial fan']
sensors = ['temp_Bedroom temp', 'temp_Outdoor temp', 'motion_Motion living room', 'light_environment', 'door_Door',
           'weekday']


def create_aggregated_features_training(data, sensors, devices, target_device):
    aggregated_data = []
    target_data = []

    interval = 144
    for i in range(0, int(len(data)/7)):
        past_week_data = []
        for j in range(7):
            if i * j * interval >= 0:
                try:
                    past_week_data.append(data.iloc[i - j * interval])
                except IndexError:
                    continue

        if len(past_week_data) < 7:
            continue

        past_week_df = pd.DataFrame(past_week_data)
        aggregated_features = past_week_df[sensors + [d for d in devices if d != target_device]].mean().tolist()

        target_device_status = data.iloc[i][target_device]

        aggregated_data.append(aggregated_features)
        target_data.append(target_device_status)

    feature_columns = [f'{sensor}' for sensor in sensors + [d for d in devices if d != target_device]]
    return pd.DataFrame(aggregated_data, columns=feature_columns), pd.Series(target_data, name=target_device)


def train_and_evaluate_lstm(target_device):
    X, y = create_aggregated_features_training(data, sensors, devices, target_device)
    train_data, test_data, train_targets, test_targets = train_test_split(X, y, test_size=0.2, random_state=42)

    scaler = StandardScaler()
    train_data = scaler.fit_transform(train_data)
    test_data = scaler.transform(test_data)

    train_data = train_data.reshape(train_data.shape[0], 1, train_data.shape[1])
    test_data = test_data.reshape(test_data.shape[0], 1, test_data.shape[1])

    model = Sequential()
    model.add(LSTM(50, input_shape=(train_data.shape[1], train_data.shape[2])))
    model.add(Dense(1, activation='sigmoid'))

    model.compile(optimizer='adam', loss='binary_crossentropy', metrics=['accuracy'])

    early_stopping = EarlyStopping(monitor='val_loss', patience=10, restore_best_weights=True)

    model.fit(train_data, train_targets, epochs=100, batch_size=32, validation_split=0.2, callbacks=[early_stopping],verbose=0)

    y_pred = (model.predict(test_data) > 0.5).astype("int32")

    accuracy = accuracy_score(test_targets, y_pred)
    confusion_matrix = metrics.confusion_matrix(test_targets, y_pred)

    print(f'Accuracy for predicting {target_device}: {accuracy:.2f}')
    print(confusion_matrix)

    return model

models = {}
for device in devices:
    models[device] = train_and_evaluate_lstm(device)
