import json
from datetime import datetime
import time
import intelligent as ai
import database_instructions as da

AI_PREDICTED_1 = []
AI_PREDICTED_2 = []
AI_PREDICTED_3 = []
DEVICES = []
ai_functionality = -1

def load_devices_from_file():
    global DEVICES,AI_PREDICTED_1,AI_PREDICTED_2,AI_PREDICTED_3
    DEVICES = json.load(open("devices.txt"))
    AI_PREDICTED_1 = json.load(open("test_prediction1.txt"))
    AI_PREDICTED_2 = json.load(open("test_prediction2.txt"))
    AI_PREDICTED_3 = json.load(open("test_prediction3.txt"))

def append_prediction():  # Ver 7 - Predict for user to choose later and execution
    count = 0
    #while True:
    predicted = []
    predicted.append(ai.evaluate_with_model("model_decisionTree.pkl", DEVICES))
    predicted[0]['timestamp'] = datetime.now().strftime('%Y/%m/%d %H:%M:00')
    predicted.append(ai.evaluate_with_model("model_randForest.pkl", DEVICES))
    predicted[1]['timestamp'] = datetime.now().strftime('%Y/%m/%d %H:%M:00')
    predicted.append(ai.evaluate_with_model("model_LTSM.pkl", DEVICES))
    predicted[2]['timestamp'] = datetime.now().strftime('%Y/%m/%d %H:%M:00')
    AI_PREDICTED_1.append(predicted[0])
    AI_PREDICTED_2.append(predicted[1])
    AI_PREDICTED_3.append(predicted[2])
#        if ai_functionality != -1:
#            evaluate_device_status(predicted[ai_functionality])
#        count += 1
#        if count > 59:
#            da.calculate_energy(MySQL_connection_details, datetime.now())
#            count = 0
    time.sleep(60)
    print("APPENDED PREDICT 1: ", predicted[0])
    print("APPENDED PREDICT 2: ", predicted[1])
    print("APPENDED PREDICT 3: ", predicted[2])


def evaluate_models():
    real_runtime_table = da.query_database_for_calculate_runtime(MySQL_connection_details, datetime.now())
    total_real_runtime = ai.calculate_runtime(real_runtime_table)
    total_predict1_runtime = ai.calculate_runtime(AI_PREDICTED_1)
    total_predict2_runtime = ai.calculate_runtime(AI_PREDICTED_2)
    total_predict3_runtime = ai.calculate_runtime(AI_PREDICTED_3)
    total_real_consumption = ai.calculate_total_consumption(
        ai.calculate_each_devices_consumption(total_real_runtime, DEVICES))
    total_predict1_consumption = ai.calculate_total_consumption(
        ai.calculate_each_devices_consumption(total_predict1_runtime, DEVICES))
    total_predict2_consumption = ai.calculate_total_consumption(
        ai.calculate_each_devices_consumption(total_predict2_runtime, DEVICES))
    total_predict3_consumption = ai.calculate_total_consumption(
        ai.calculate_each_devices_consumption(total_predict3_runtime, DEVICES))
    print("PREDICT1: " + str(total_predict1_consumption))
    print("PREDICT2: " + str(total_predict2_consumption))
    print("PREDICT3: " + str(total_predict3_consumption))
    print("REAL: " + str(total_real_consumption))

load_devices_from_file()

evaluate_models()