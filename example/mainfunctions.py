import tuya_instructions as ti
import database_instructions as da
import intelligent as ai
import json
import logging
from time import sleep
from socket import socket, AF_INET, SOCK_STREAM, gethostname, gethostbyname
from multiprocessing.pool import ThreadPool as Pool
from threading import Thread
from datetime import datetime
from sys import stdout

# ##############################Spec define###############################
# Tuya API Information
ACCESS_ID = ""
ACCESS_KEY = ""
API_ENDPOINT = "https://openapi.tuyaus.com"
# Database Information
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
# Socket Information
Sockets_hostname = gethostname()
Sockets_hostip = gethostbyname(Sockets_hostname)
Socket_mobile_port = 29562
Socket_plug_port = 12347
# Delay settings
delay_automation = 60
delay_ai = 60
delay_database = 60
delay_fetch = 10
# settings
ai_functionality = -1
fetch_thread_pool_size = 3
# Detect mobile connection state
mobile_is_connected = False
# Declare global variable
DEVICES = []
AUTOMATION = []
AI_PREDICTED_1 = []
AI_PREDICTED_2 = []
AI_PREDICTED_3 = []
AI_CHANGED = {}
# Debug log
logging.basicConfig(stream=stdout, level=logging.INFO)
logger = logging.getLogger('c')
logger.setLevel(logging.DEBUG)


# Sub functions
# Handling DEVICES file
def save_devices_to_file():
    with open('devices.txt', 'w') as devices_file:
        devices_file.write(json.dumps(DEVICES))


def load_devices_from_file():
    global DEVICES
    DEVICES = json.load(open("devices.txt"))
    for i in DEVICES:
        logger.info(str(datetime.now()) + " Device loaded: " + i.get("Device_name"))


def diff_devices(res1: dict):
    target = res1["Device_name"]
    obj = json.load(open("devices.txt"))
    res2 = None
    for sub in obj:
        if sub['Device_name'] == target:
            res2 = sub
            break
    dict1 = res1["STATUS"]
    dict2 = res2["STATUS"]
    for key in dict1.keys():
        if key in dict2.keys():
            if dict1[key] != dict2[key]:
                return True
        else:
            return True
    else:
        return False


# Handling AUTOMATION file
def save_automation_to_file():
    with open('automations.txt', 'w') as automation_file:
        automation_file.write(json.dumps(AUTOMATION))
    return True


def load_automation_from_file():
    global AUTOMATION
    AUTOMATION = json.load(open("automations.txt"))
    for i in AUTOMATION:
        logger.info(str(datetime.now()) + " Automation loaded: " + i.get("Name"))

# Handling ENERGY file
def save_energy_prediction_to_file(energy: dict):
    with open('energy_comparison_model.txt', 'w') as energy_file:
        energy_file.write(json.dumps(energy))
def load_energy_prediction_from_file():
    try:
        return json.load(open("energy_comparison_model.txt"))
    except Exception:
        logger.error(str(datetime.now()) + " Energy prediction file error")


# Identify device and send command to tuya (run by command_from_mobile)
def command_to_api(device_name: str, new_settings: dict):
    device = next((sub for sub in DEVICES if sub['Device_name'] == device_name), None)
    device['SET'] = new_settings
    ti.command(API_ENDPOINT, ACCESS_ID, ACCESS_KEY, device)
    logger.info(str(datetime.now()) + " Command passed to Tuya instruction: " + device_name)


# Automation handling
def add_automation(json_data):  # add an automation (run by handle_mobile_client)
    global AUTOMATION
    if json_data['If'] and json_data['Then']:
        AUTOMATION.append(json_data)
        return save_automation_to_file()
    else:
        return False


def remove_automation(name: str):  # remove an automation (run by handle_mobile_client)
    for i in AUTOMATION:
        if i.get("Name") == name:
            AUTOMATION.remove(i)
    return save_automation_to_file()

def remove_device(device_name: str):
    for i in DEVICES:
        if i.get("Device_name") == device_name:
            DEVICES.remove(i)

def push_automation_info_to_mobile(client_socket):  # send list of automations (run by handle_mobile_client)
    load_automation_from_file()
    if len(AUTOMATION) != 0:
        for i in AUTOMATION:
            data = i
            data["msg_type"] = "Automation_update"
            json_data = json.dumps(data)
            try:
                client_socket.send((json_data + "\n").encode())
                logger.info(str(datetime.now()) + " Send text to mobile Automation: " + i["Name"])
            except Exception as e:
                logger.error(str(datetime.now()) + " Error sending text to mobile Automation: "+str(e))
                break
    else:
        data = {"msg_type": "Automation_update"}
        json_data = json.dumps(data)
        try:
            client_socket.send((json_data + "\n").encode())
            logger.info(str(datetime.now()) + " Automation text send to mobile: None" )
        except Exception as e:
            logger.error(str(datetime.now()) + " Automation error sending text to mobile: "+str(e))


def push_ai_stat_to_mobile(client_socket):
    try:
        data = {"msg_type": "AI_functionality_update", "status": ai_functionality}
        json_data = json.dumps(data)
        client_socket.send((json_data + "\n").encode())
        logger.info(str(datetime.now()) + " Send text to mobile AI set: " + str(ai_functionality))
    except Exception as e:
        logger.error(str(datetime.now()) + " Error sending text to mobile AI set: "+ str(e))


# Main functions
def manage_automation():  # check automation condition periodically and run (periodically)
    logger.info("Automation started")
    while True:
        sleep(delay_automation)
        for i in AUTOMATION:
            do = True
            for j in i["If"]:
                if j.get("Type") == "Condition":
                    device = next((sub for sub in DEVICES if sub['Device_name'] == j["Device_name"]), None)
                    # pull data from sensor Device_name = Device_name in If[]
                    target_value = device.get('STATUS').get(j["variable"])
                    if target_value != j["value"]:  # check condition value within value in If
                        do = False
                elif j.get("Type") == "Schedule":
                    tf = datetime.strptime(j.get("From"), '%H:%M:%S').strftime('%H:%M:%S')
                    tt = datetime.strptime(j.get("To"), '%H:%M:%S').strftime('%H:%M:%S')
                    tc = datetime.now().strftime('%H:%M:%S')
                    if not tf < tc < tt:
                        do = False
            # Then for j in i:
            if do:
                for j in i["Then"]:
                    # Obtain device status Device_name = Device_name in Then[]
                    device = next((sub for sub in DEVICES if sub['Device_name'] == j["Device_name"]), None)
                    current_value = device.get(j["variable"])
                    if current_value != j["value"]:  # check if device is already at that state in Then
                        logger.debug(str(datetime.now()) + " Automation task execute: " + i["Name"])
                        # Execute
                        execute: json
                        if type(j["value"]) is str:
                            execute = json.loads('{"' + j["variable"] + '": "' + j["value"] + '"}')
                        elif type(j["value"]) is bool:
                            execute = json.loads('{"' + j["variable"] + '": ' + str.lower(str(j["value"])) + '}')
                        else:
                            execute = json.loads('{"' + j["variable"] + '": ' + str(j["value"]) + '}')
                        command_to_api(j["Device_name"], execute)


# Pull device status from Tuya
def fetch_devices_stat():
    while True:
        if not mobile_is_connected:
            sleep(delay_fetch)
        try:
            pool = Pool(fetch_thread_pool_size)
            results = []
            for i in DEVICES:
                result = pool.apply_async(ti.request, (API_ENDPOINT, ACCESS_ID, ACCESS_KEY, i,))
                results.append(result)
            [result.wait() for result in results]
        except Exception as e:
            logger.error(str(datetime.now()) + "fetch_devices_stat  " + " error: " + str(e))


# Push message mobile application (when connected)
def update_device_to_mobile(client_socket):
    global mobile_is_connected
    for i in DEVICES:
        data = i.get("STATUS").copy()
        data["msg_type"] = "Device_update"
        data["Device_name"] = i["Device_name"]
        data["Device_type"] = i["Device_type"]
        json_data = json.dumps(data)
        try:
            client_socket.send((json_data + "\n").encode())
            logger.info(str(datetime.now()) + " Send initial text to mobile device: " + data["Device_name"])
        except Exception as e:
            logger.error(str(datetime.now()) + " Error sending initial text to mobile: "+str(e))
            break
    push_automation_info_to_mobile(client_socket)
    push_ai_stat_to_mobile(client_socket)
    while client_socket:
        for i in DEVICES:
            if "close" in str(client_socket):
                logger.warning(str(datetime.now()) + " update_device_to_mobile thread closing due to socket")
                mobile_is_connected = False
                break
            if diff_devices(i):
                save_devices_to_file()
                data = i.get("STATUS")
                data["msg_type"] = "Device_update"
                data["Device_name"] = i["Device_name"]
                data["Device_type"] = i["Device_type"]
                json_data = json.dumps(data)
                try:
                    client_socket.send((json_data + "\n").encode())
                    logger.info(str(datetime.now()) + " Send text to mobile device: " + data["Device_name"])
                except Exception as e:
                    logger.error(str(datetime.now()) + " Error sending text to mobile: "+str(e))
                    break
        else:
            continue
        break


# Handling command from mobile application (when connected)
def handle_mobile_client(client_socket):
    while True:
        try:
            request = client_socket.recv(1024).decode()
            logger.info(str(datetime.now()) + " Received from mobile: " + str(request))
            json_data_rece = json.loads(request)
            msg_type = ""
            try:
                msg_type = json_data_rece["type"]
            except KeyError:
                logger.error(str(datetime.now()) + " Received from mobile has no type argument: " + str(json_data_rece))
            if msg_type == "command":
                domain = json_data_rece["Domain"]
                if domain == "tuya":
                    device_name = json_data_rece["Device_name"]
                    del json_data_rece["Device_name"]
                    del json_data_rece["Domain"]
                    arg = json_data_rece["arg"]
                    command_to_api(device_name, arg)
                    try:
                        if AI_CHANGED[device_name] == 1:
                            AI_CHANGED[device_name] = 60
                    except Exception as e:
                        logger.error(str(datetime.now()) + "AI preventer can't change state to 60: " +str(e))
                elif domain == "custom":
                    print("TO BE IMPLEMENTED")
            elif msg_type == "remove_device":
                remove_device(json_data_rece["Device_name"])
            elif msg_type == "request_automation_list":
                push_automation_info_to_mobile(client_socket)
            elif msg_type == "set_automation":
                command_type = json_data_rece["set_type"]
                if command_type == "add":
                    del json_data_rece["set_type"]
                    del json_data_rece["type"]
                    do = True
                    for i in AUTOMATION:
                        if i.get("Name") == json_data_rece["Name"]:
                            do = False
                    if do:
                        if add_automation(json_data_rece):
                            client_socket.send(("{'msg_type': 'Automation_instruction_response', 'status': 'Add success'}" + "\n").encode())
                            logger.info(str(datetime.now()) + " Send text to mobile automation: Add success")
                        else:
                            client_socket.send(("{'msg_type': 'Automation_instruction_response', 'status': 'Add failed'}" + "\n").encode())
                            logger.info(str(datetime.now()) + " Send text to mobile automation: Add failed")
                    else:
                        client_socket.send(("{'msg_type': 'Automation_instruction_response', 'status': 'Add failed, Duplicated'}" + "\n").encode())
                        logger.info(str(datetime.now()) + " Send text to mobile automation: Add failed, Duplicated")
                elif command_type == "set":
                    del json_data_rece["set_type"]
                    del json_data_rece["type"]
                    exist = False
                    for i in AUTOMATION:
                        if i.get("Name") == json_data_rece["Name"]:
                            exist = True
                    if exist:
                        if remove_automation(json_data_rece["Name"]):
                            if add_automation(json_data_rece):
                                client_socket.send(("{'msg_type': 'Automation_instruction_response', 'status': 'Set success'}" + "\n").encode())
                                logger.info(str(datetime.now()) + " Send text to mobile automation: Set success")
                        else:
                            client_socket.send(("{'msg_type': 'Automation_instruction_response', 'status': 'Set failed'}" + "\n").encode())
                            logger.info(str(datetime.now()) + " Send text to mobile automation: Set failed")
                    else:
                        client_socket.send(("{'msg_type': 'Automation_instruction_response', 'status': 'Set failed, Does not exist'}" + "\n").encode())
                        logger.info(str(datetime.now()) + " Send text to mobile automation: Set failed, Does not exist")
                elif command_type == "remove":
                    if remove_automation(json_data_rece["Name"]):
                        client_socket.send(("{'msg_type': 'Automation_instruction_response', 'status': 'Remove success'}" + "\n").encode())
                        logger.info(str(datetime.now()) + " Send text to mobile automation: Remove success")
                    else:
                        client_socket.send(("{'msg_type': 'Automation_instruction_response', 'status': 'Remove failed'}" + "\n").encode())
                        logger.info(str(datetime.now()) + " Send text to mobile automation: Remove failed")
            elif msg_type == "set_ai_functionality":
                global ai_functionality
                ai_functionality = json_data_rece["set"]
                push_ai_stat_to_mobile(client_socket)
            elif msg_type == "request_energy_history_list":
                period = json_data_rece["period"]
                energy_history_dict = da.query_energy(MySQL_connection_details,period,datetime.now())
                energy_history_dict["msg_type"] = "Energy_history"
                json_data_rece = json.dumps(energy_history_dict)
                client_socket.send((json_data_rece + "\n").encode())
                logger.info(str(datetime.now()) + " Send text to mobile energy history")
            elif msg_type == "request_energy_prediction_list":
                push_energy_prediction_to_mobile(client_socket)
            elif msg_type == "request_ai_functionality":
                push_ai_stat_to_mobile(client_socket)
        except Exception as e:
            logger.error(str(datetime.now()) + " Handling mobile thread error: "+ str(e))
            client_socket.close()
            break


# Handle incoming socket from mobile application
def connect_to_mobile():
    global mobile_is_connected
    server_socket = socket(AF_INET, SOCK_STREAM)
    server_socket.bind((Sockets_hostname, Socket_mobile_port))
    server_socket.listen(5)
    logger.info(str(datetime.now()) + " System initialized: " + Sockets_hostname + " " + Sockets_hostip)
    while True:
        client_socket, addr = server_socket.accept()
        logger.info(str(datetime.now()) + ' Got app connection from ' + str(addr))
        mobile_is_connected = True
        client_thread = Thread(target=handle_mobile_client, args=(client_socket,))
        value_thread = Thread(target=update_device_to_mobile, args=(client_socket,))
        client_thread.start()
        value_thread.start()
        client_thread.join()
        value_thread.join()


# Append device status to Tuya
def database_manage():
    while True:
        try:
            da.append_to_database(MySQL_connection_details, DEVICES.copy(), datetime.now())
        except Exception as e:
            logger.error(str(datetime.now()) + " Database thread error: " + str(e))
        sleep(delay_database)


# AI function
def append_prediction():
    evaluated_flag = 0
    while True:
        predicted = []
        predicted.append(ai.evaluate_with_model("model_decisionTree.pkl", DEVICES.copy()))
        predicted[0]['timestamp'] = datetime.now().strftime('%Y/%m/%d %H:%M:00')
        predicted.append(ai.evaluate_with_model("model_randForest.pkl", DEVICES.copy()))
        predicted[1]['timestamp'] = datetime.now().strftime('%Y/%m/%d %H:%M:00')
        predicted.append(ai.evaluate_with_model("model_LTSM.pkl", DEVICES.copy()))
        predicted[2]['timestamp'] = datetime.now().strftime('%Y/%m/%d %H:%M:00')
        AI_PREDICTED_1.append(predicted[0])
        AI_PREDICTED_2.append(predicted[1])
        AI_PREDICTED_3.append(predicted[2])
        now = datetime.now()
        if ai_functionality != -1:
            logger.debug(str(datetime.now()) + " Executing evaluate_device_status")
            evaluate_device_status(predicted[ai_functionality])
        if now.minute == 0:
            try:
                da.calculate_energy(MySQL_connection_details, datetime.now())
                logger.info(str(datetime.now()) + " Calculated energy and append to table")
            except Exception as e:
                logger.error(str(datetime.now()) + " Calculated energy failed: " + str(e))
        if now.hour == 0 and now.minute == 0 and evaluated_flag == 0:
            logger.debug(str(datetime.now()) + " Executing evaluate_models")
            evaluate_models()
            evaluated_flag = 1
        if now.hour == 1 and now.minute == 0:
            logger.debug(str(datetime.now()) + " Executing flag reset for evaluate_models")
            evaluated_flag = 0
        count_ai_preventer()
        sleep(delay_ai)

def evaluate_models(): #Run daily after midnight
    real_runtime_table = da.query_database_for_calculate_runtime(MySQL_connection_details, datetime.now())
    total_real_runtime = ai.calculate_runtime_real(real_runtime_table)
    total_predict1_runtime = ai.calculate_runtime(AI_PREDICTED_1)
    total_predict2_runtime = ai.calculate_runtime(AI_PREDICTED_2)
    total_predict3_runtime = ai.calculate_runtime(AI_PREDICTED_3)
    total_real_consumption = ai.calculate_total_consumption(
        ai.calculate_each_devices_consumption(total_real_runtime, DEVICES.copy()))
    total_predict1_consumption = ai.calculate_total_consumption(
        ai.calculate_each_devices_consumption(total_predict1_runtime, DEVICES.copy()))
    total_predict2_consumption = ai.calculate_total_consumption(
        ai.calculate_each_devices_consumption(total_predict2_runtime, DEVICES.copy()))
    total_predict3_consumption = ai.calculate_total_consumption(
        ai.calculate_each_devices_consumption(total_predict3_runtime, DEVICES.copy()))
    logger.info(str(datetime.now()) +" Energy prediction of model 1: " + str(total_predict1_consumption))
    logger.info(str(datetime.now()) +" Energy prediction of model 2: " + str(total_predict2_consumption))
    logger.info(str(datetime.now()) +" Energy prediction of model 3: " + str(total_predict3_consumption))
    logger.info(str(datetime.now()) +" Energy calculation of real s: " + str(total_real_consumption))
    energy = {"Actual": total_real_consumption,"Model 1": total_predict1_consumption,"Model 2": total_predict2_consumption,"Model 3": total_predict3_consumption}
    save_energy_prediction_to_file(energy)
    #Flush prediction after evaluate
    AI_PREDICTED_1.clear()
    AI_PREDICTED_2.clear()
    AI_PREDICTED_3.clear()

def push_energy_prediction_to_mobile(client_socket):
    energy_list = load_energy_prediction_from_file()
    if len(energy_list) != 0:
        energy_list["msg_type"] = "Energy_prediction"
        json_data = json.dumps(energy_list)
        try:
            client_socket.send((json_data + "\n").encode())
            logger.info(str(datetime.now()) + " Send text to mobile Energy: " + str(energy_list))
        except Exception as e:
            logger.error(str(datetime.now()) + " Error sending text to mobile Energy: " + str(e))

def evaluate_device_status(predicted):
    try:
        del predicted['timestamp']
        for key, value in predicted.items():
            device = next((sub for sub in DEVICES if sub['Device_name'] == key), None)
            current_value = device.get("STATUS").get("Power")
            executable = True
            try:
                if AI_CHANGED[key] > 0: executable = False
            except:
                pass
            if current_value != value and value == False and executable:
                command_to_api(key, {'Power': value})
                AI_CHANGED[key] = 1
                logger.info(str(datetime.now()) + " AI executed device " + key)
    except Exception as e:
        logger.error(str(datetime.now()) + " AI thread error: "+str(e))

def count_ai_preventer():
    for key, value in list(AI_CHANGED.items()):
        if value == 0:
            del(AI_CHANGED[key])
        elif value > 0:
            AI_CHANGED[key] -= 1

# Receiving data from customize plug
def read_plug():
    while True:
        plug_server_socket = socket(AF_INET, SOCK_STREAM)
        plug_server_socket.bind((Sockets_hostname, Socket_plug_port))
        plug_server_socket.listen(5)
        while True:
            plug_client_socket, addr = plug_server_socket.accept()
            logger.info(str(datetime.now()) + ' Got plug connection from ' + str(addr))
            request = plug_client_socket.recv(1024).decode()
            if not request:
                break
            plug_client_socket.close()
            json_data = json.loads(request)
            for i in DEVICES:
                if json_data.get("Domain") == "custom":
                    try:
                        status_dict = i.get("STATUS")
                        current = json_data.get("STATUS")["Current"]
                        status_dict["Current"] = current
                        logger.info(str(datetime.now()) + " Current = " + str(i.get("STATUS")["Current"]))
                    except Exception as e:
                        logger.error(str(datetime.now()) + ' custom plug reading error: ' + str(e))
                    break


logger.info("Settings: \n     Delay for Automation:" + str(delay_automation) + "\n     AI functionality:" + str(
    ai_functionality) + "\n     Delay for AI:" + str(
    delay_ai) + "\n     Delay for Database:" + str(
    delay_database) + "\n     Database site: " + MySQL_connection_details.get("HOST"))
load_devices_from_file()
load_automation_from_file()
mobile_thread = Thread(target=connect_to_mobile)
automation_thread = Thread(target=manage_automation)
fetch_devices_thread = Thread(target=fetch_devices_stat)
database_thread = Thread(target=database_manage)
plug_thread = Thread(target=read_plug)
ai_thread = Thread(target=append_prediction)
mobile_thread.start()
automation_thread.start()
fetch_devices_thread.start()
database_thread.start()
plug_thread.start()
ai_thread.start()
mobile_thread.join()
automation_thread.join()
fetch_devices_thread.join()
database_thread.join()
plug_thread.join()
ai_thread.join()
