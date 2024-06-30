import pandas as pd
from sklearn.metrics import classification_report
from sklearn.model_selection import train_test_split
import numpy as np
from tqdm import tqdm
from joblib import Parallel, delayed
import xgboost as xgb

# Define the mapping from weekday name to number
weekday_mapping = {
    'Monday': 1,
    'Tuesday': 2,
    'Wednesday': 3,
    'Thursday': 4,
    'Friday': 5,
    'Saturday': 6,
    'Sunday': 7
}

# Load the CSV file into a DataFrame
file_path = 'raw_data_stripped.csv'  # Replace with your file path
df = pd.read_csv(file_path)

# Print column names to verify
print("Columns in the DataFrame:", df.columns)

# Convert the datetime column to datetime format
df['timestamp'] = pd.to_datetime(df['timestamp'], format='%d-%m-%y %H:%M')

# Extract day, hour, and minute from the datetime column
df['day'] = df['timestamp'].dt.day_name().map(weekday_mapping)
df['hh'] = df['timestamp'].dt.hour
df['mm'] = df['timestamp'].dt.minute

# Specify input and target columns
input_columns = ['day', 'hh', 'mm', 'temp_Bedroom temp', 'temp_Outdoor temp', 'motion_Motion living room', 'light_environment', 'door_Door']
target_columns = ['light_Shower', 'light_FR', 'light_FL', 'plug_AC', 'plug_Recirculation fan', 'plug_Floor lamp', 'plug_Artificial fan']

# Check if columns exist in the DataFrame
for col in input_columns + target_columns:
    if col not in df.columns:
        print(f"Column {col} is not found in the DataFrame. Please check the column names.")
        exit()

# Define a function to create sequences
def create_sequences(data, seq_length):
    sequences = []
    targets = []
    for i in tqdm(range(len(data) - seq_length * 2), desc="Creating sequences"):
        seq_in = data.iloc[i:i + seq_length][input_columns].values
        seq_out = data.iloc[i + seq_length:i + seq_length * 2][target_columns].values
        sequences.append(seq_in)
        targets.append(seq_out)
    return np.array(sequences), np.array(targets)

# Create sequences of 3 days (3 days * 24 hours/day * 60 minutes/hour = 4320 minutes)
seq_length =  60
X, y = create_sequences(df, seq_length)

# Split the data into training and testing sets
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.1, random_state=0)

# Flatten the input data for the model
X_train_flat = X_train.reshape(X_train.shape[0], -1)
X_test_flat = X_test.reshape(X_test.shape[0], -1)

# Flatten the target data for the model
y_train_flat = y_train.reshape(y_train.shape[0], -1)
y_test_flat = y_test.reshape(y_test.shape[0], -1)

# Train the model using XGBoost with GPU support
params = {
    'objective': 'reg:squarederror',
    'tree_method': 'hist',  # Use GPU acceleration
    'verbosity': 1,  # Show progress
    'device': 'cuda'
}

dtrain = xgb.DMatrix(X_train_flat, label=y_train_flat)
dtest = xgb.DMatrix(X_test_flat, label=y_test_flat)

# Specify number of boosting rounds
num_boost_round = 45

# Train the model
print("Training the model...")
bst = xgb.train(params, dtrain, num_boost_round, evals=[(dtrain, 'train'), (dtest, 'eval')], verbose_eval=True)

# Define a function to predict in parallel
def predict_parallel(model, data):
    dmatrix = xgb.DMatrix(data)
    return model.predict(dmatrix)

# Use joblib to parallelize predictions with tqdm for progress
num_cores = -1  # Use all available cores
y_pred_flat = Parallel(n_jobs=num_cores)(
    delayed(predict_parallel)(bst, [X_test_flat[i]]) for i in tqdm(range(X_test_flat.shape[0]), desc="Predicting")
)

# Convert predictions list to a numpy array
y_pred_flat = np.vstack(y_pred_flat)

# Reshape predictions back to the original shape
y_pred = y_pred_flat.reshape(y_test.shape)

# Evaluate the model
print("Predictions shape:", y_pred.shape)
print("Test data shape:", y_test.shape)

# Compare a few predictions to the actual values
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