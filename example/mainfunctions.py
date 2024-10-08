import asyncio
import csv
import io

import tuya_instructions as ti
import database_instructions as da
import intelligent as ai
import json
import logging
import websockets
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
    "USERNAME": "",
    "PASSWORD": "",
    "CA_Path": "/ca-certificate.crt"
}
# Socket Information
Sockets_hostname = gethostname()
Sockets_hostip = gethostbyname(Sockets_hostname)
Socket_mobile_port = 29562
Socket_additional_mobile_port = 29563
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


# Automation handling (run by command_from_mobile)
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


# Device manager handling (run by command_from_mobile)
def remove_device(device_name: str):
    for i in DEVICES:
        if i.get("Device_name") == device_name:
            DEVICES.remove(i)


# Push information to mobile (run by command_from_mobile)
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
                logger.error(str(datetime.now()) + " Error sending text to mobile Automation: " + str(e))
                break
    else:
        data = {"msg_type": "Automation_update"}
        json_data = json.dumps(data)
        try:
            client_socket.send((json_data + "\n").encode())
            logger.info(str(datetime.now()) + " Automation text send to mobile: None")
        except Exception as e:
            logger.error(str(datetime.now()) + " Automation error sending text to mobile: " + str(e))


def push_ai_setting_to_mobile(client_socket):
    try:
        data = {"msg_type": "AI_functionality_update", "status": ai_functionality}
        json_data = json.dumps(data)
        client_socket.send((json_data + "\n").encode())
        logger.info(str(datetime.now()) + " Send text to mobile AI set: " + str(ai_functionality))
    except Exception as e:
        logger.error(str(datetime.now()) + " Error sending text to mobile AI set: " + str(e))


async def push_prediction_schedule(websocket):
    try:
        logger.info(str(datetime.now()) + "Additional socket got connection..")
        with open('predicted_results.csv', mode='r', newline='') as csvfile:
            reader = csv.reader(csvfile)
            csv_data = list(reader)

        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerows(csv_data)
        csv_string = output.getvalue()

        await websocket.send(csv_string)
        logger.info(str(datetime.now()) + "Additional socket sent CSV to client")
    except Exception as e:
        logger.error(str(datetime.now()) + f" Additional socket Error: {e}")


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


# AI handler
def evaluate_models():  # Run daily after midnight
    try:
        real_runtime_table = da.query_database_for_calculate_runtime(MySQL_connection_details, datetime.now())
        total_real_runtime = ai.calculate_runtime_real(real_runtime_table)

        da.query_database_for_schedule_prediction(MySQL_connection_details, datetime.now())
        ai.evaluate_schedule()
        total_predict1_runtime = ai.calculate_runtime(ai.convert_csv_to_json())

        total_real_consumption = ai.calculate_total_consumption(
            ai.calculate_each_devices_consumption(total_real_runtime, DEVICES.copy()))
        total_predict1_consumption = ai.calculate_total_consumption(
            ai.calculate_each_devices_consumption(total_predict1_runtime, DEVICES.copy()))
        total_avg7_consumption = da.query_energy(MySQL_connection_details, "week", datetime.now())[0] #New line
        total_thisdaylstweek_consumption = da.query_energy(MySQL_connection_details, "thisdaylstweek", datetime.now())[0]#New line
        logger.info(str(datetime.now()) + " Energy prediction of model: " + str(total_predict1_consumption))
        logger.info(str(datetime.now()) + " Energy calculation of real: " + str(total_real_consumption))
        energy = {"Prev day": total_real_consumption, "Model": total_predict1_consumption,"7avg":total_avg7_consumption,"This day": total_thisdaylstweek_consumption}
        save_energy_prediction_to_file(energy)
        # Flush prediction after evaluate
    except Exception as e:
        logger.error(str(datetime.now()) + " evaluate_models error: " + str(e))


def count_ai_preventer():
    for key, value in list(AI_CHANGED.items()):
        if value == 0:
            del (AI_CHANGED[key])
        elif value > 0:
            AI_CHANGED[key] -= 1


def execute_prediction():
    instruction = ai.query_specific_instruction(datetime.now())
    try:
        del instruction['timestamp']
        for key, value in instruction.items():
            device = next((sub for sub in DEVICES if sub['Device_name'] == key), None)
            current_value = device.get("STATUS").get("Power")
            executable = True
            try:
                if AI_CHANGED[key] > 0: executable = False
            except:
                pass
            if current_value != value and executable:
                command_to_api(key, {'Power': value})
                AI_CHANGED[key] = 1
                logger.info(str(datetime.now()) + " AI executed device: " + key)
    except Exception as e:
        logger.error(str(datetime.now()) + " AI execution error: " + str(e))


# MAIN FUNCTIONS
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
            logger.error(str(datetime.now()) + " Error sending initial text to mobile: " + str(e))
            break
    push_automation_info_to_mobile(client_socket)
    push_ai_setting_to_mobile(client_socket)
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
                    logger.error(str(datetime.now()) + " Error sending text to mobile: " + str(e))
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
                        logger.error(str(datetime.now()) + "AI preventer can't change state to 60: " + str(e))
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
                            client_socket.send((
                                                       "{'msg_type': 'Automation_instruction_response', 'status': 'Add success'}" + "\n").encode())
                            logger.info(str(datetime.now()) + " Send text to mobile automation: Add success")
                        else:
                            client_socket.send((
                                                       "{'msg_type': 'Automation_instruction_response', 'status': 'Add failed'}" + "\n").encode())
                            logger.info(str(datetime.now()) + " Send text to mobile automation: Add failed")
                    else:
                        client_socket.send((
                                                   "{'msg_type': 'Automation_instruction_response', 'status': 'Add failed, Duplicated'}" + "\n").encode())
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
                                client_socket.send((
                                                           "{'msg_type': 'Automation_instruction_response', 'status': 'Set success'}" + "\n").encode())
                                logger.info(str(datetime.now()) + " Send text to mobile automation: Set success")
                        else:
                            client_socket.send((
                                                       "{'msg_type': 'Automation_instruction_response', 'status': 'Set failed'}" + "\n").encode())
                            logger.info(str(datetime.now()) + " Send text to mobile automation: Set failed")
                    else:
                        client_socket.send((
                                                   "{'msg_type': 'Automation_instruction_response', 'status': 'Set failed, Does not exist'}" + "\n").encode())
                        logger.info(str(datetime.now()) + " Send text to mobile automation: Set failed, Does not exist")
                elif command_type == "remove":
                    if remove_automation(json_data_rece["Name"]):
                        client_socket.send((
                                                   "{'msg_type': 'Automation_instruction_response', 'status': 'Remove success'}" + "\n").encode())
                        logger.info(str(datetime.now()) + " Send text to mobile automation: Remove success")
                    else:
                        client_socket.send((
                                                   "{'msg_type': 'Automation_instruction_response', 'status': 'Remove failed'}" + "\n").encode())
                        logger.info(str(datetime.now()) + " Send text to mobile automation: Remove failed")
            elif msg_type == "set_ai_functionality":
                global ai_functionality
                ai_functionality = json_data_rece["set"]
                push_ai_setting_to_mobile(client_socket)
            elif msg_type == "request_energy_history_list":
                period = json_data_rece["period"]
                energy_history_dict = da.query_energy(MySQL_connection_details, period, datetime.now())
                energy_history_dict["msg_type"] = "Energy_history"
                json_data_rece = json.dumps(energy_history_dict)
                client_socket.send((json_data_rece + "\n").encode())
                logger.info(str(datetime.now()) + " Send text to mobile energy history")
            elif msg_type == "request_energy_prediction_list":
                push_energy_prediction_to_mobile(client_socket)
            elif msg_type == "request_ai_functionality":
                push_ai_setting_to_mobile(client_socket)
        except Exception as e:
            logger.error(str(datetime.now()) + " Handling mobile thread error: " + str(e))
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


# Debug functionality
def handle_direct_command():
    while True:
        global mobile_is_connected
        command = input()
        if command == "stop_socket":
            mobile_is_connected = False
        elif command == "start_read_plug":
            try:
                plug_thread2 = Thread(target=read_plug)
                plug_thread2.start()
            except:
                logger.error("Could not start read plug thread")
        elif command == "cat_energy":
            print(load_energy_prediction_from_file())
        elif command == "force_evaluate":
            evaluate_models()
        elif command == "force_execution":
            execute_prediction()
        elif command == "cat_AI_CHANGED":
            print(str(AI_CHANGED))
        elif command == "cat_DEVICES":
            print(str(DEVICES))
        elif command == "cat_AUTOMATION":
            print(str(AUTOMATION))
        elif command == "cat_AI_PREDICTED_1":
            print(str(AI_PREDICTED_1))
        elif command == "cat_settings":
            print("Settings: \n     Delay for Automation:" + str(delay_automation) + "\n     AI functionality:" + str(
                ai_functionality) + "\n     Delay for AI:" + str(
                delay_ai) + "\n     Delay for Fetch:" + str(
                delay_fetch) + "\n     Delay for Database:" + str(
                delay_database) + "\n     Database site: " + MySQL_connection_details.get(
                "HOST") + "\n     Fetch thread pool no: " + str(fetch_thread_pool_size))
        elif command.startswith("set_"):
            variable_map = {
                "delay_automation": "delay_automation",
                "delay_ai": "delay_ai",
                "delay_fetch": "delay_fetch",
                "delay_database": "delay_database",
                "ai_functionality": "ai_functionality",
                "fetch_thread_pool_size": "fetch_thread_pool_size"
            }
            try:
                prefix, value = command.split("=")
                prefix = prefix[4:]
                if prefix in variable_map:
                    globals()[variable_map[prefix]] = int(value)
                    print(f"Set {variable_map[prefix]} to {value}")
                else:
                    print(f"Error: Unknown variable '{prefix}'")
            except ValueError:
                print("Error: Command format is incorrect.")


# Append device status to Tuya
def database_manage():
    while True:
        try:
            da.append_to_database(MySQL_connection_details, DEVICES.copy(), datetime.now())
        except Exception as e:
            logger.error(str(datetime.now()) + " Database thread error: " + str(e))
        sleep(delay_database)


# AI function
def evaluation():
    evaluated_flag = 0
    while True:
        now = datetime.now()
        if now.minute % 10 == 0 and ai_functionality == 0:
            execute_prediction()
        if now.minute == 0:  # Run every hour
            try:
                da.calculate_energy(MySQL_connection_details, datetime.now())
                logger.info(str(datetime.now()) + " Calculated energy and append to table")
            except Exception as e:
                logger.error(str(datetime.now()) + " Calculated energy failed: " + str(e))
        if now.hour == 0 and now.minute == 0 and evaluated_flag == 0:  # Run once every midnight
            logger.debug(str(datetime.now()) + " Executing evaluate_models")
            evaluate_models()
            evaluated_flag = 1
        if now.hour == 1 and now.minute == 0:  # Run once after mdnight
            logger.debug(str(datetime.now()) + " Executing flag reset for evaluate_models")
            evaluated_flag = 0
        count_ai_preventer()
        sleep(delay_ai)


# Additional socket
def read_plug():
    logger.info(str(datetime.now()) + " Plug socket at: " + Sockets_hostname + ":" + str(Socket_plug_port))
    while True:
        plug_server_socket = socket(AF_INET, SOCK_STREAM)
        plug_server_socket.bind((Sockets_hostname, Socket_plug_port))
        plug_server_socket.listen(5)
        while True:
            try:
                plug_client_socket, addr = plug_server_socket.accept()
                logger.info(str(datetime.now()) + ' Got plug connection from ' + str(addr))
                request = plug_client_socket.recv(1024).decode()
                plug_client_socket.settimeout(7)
                if not request:
                    break
                plug_client_socket.close()
                print(request)
                json_data = json.loads(str(request))
                for i in DEVICES:
                    if json_data.get("Domain") == "custom" and i.get("Device_name") == json_data.get("Device_name"):
                        try:
                            status_dict = i.get("STATUS")
                            current = json_data.get("Current")
                            status_dict["Current"] = current
                            logger.info(str(datetime.now()) + " Current = " + str(i.get("STATUS")["Current"]))
                        except Exception as e:
                            logger.error(str(datetime.now()) + ' custom plug reading error: ' + str(e))
                        break
            except Exception as e:
                logger.error(str(datetime.now()) + ' custom plug reading error: ' + str(e))


def start_websocket_server():
    asyncio.set_event_loop(asyncio.new_event_loop())
    start_server = websockets.serve(push_prediction_schedule, Sockets_hostname, Socket_additional_mobile_port)
    logger.info(str(datetime.now()) + " Additional socket run at: " + " " + Sockets_hostip + ":" + str(
        Socket_additional_mobile_port))
    asyncio.get_event_loop().run_until_complete(start_server)
    asyncio.get_event_loop().run_forever()


logger.info("Settings: \n     Delay for Automation:" + str(delay_automation) + "\n     AI functionality:" + str(
    ai_functionality) + "\n     Delay for AI:" + str(
    delay_ai) + "\n     Delay for Fetch:" + str(
    delay_fetch) + "\n     Delay for Database:" + str(
    delay_database) + "\n     Database site: " + MySQL_connection_details.get(
    "HOST") + "\n     Fetch thread pool no: " + str(fetch_thread_pool_size))
load_devices_from_file()
load_automation_from_file()
mobile_thread = Thread(target=connect_to_mobile)
automation_thread = Thread(target=manage_automation)
fetch_devices_thread = Thread(target=fetch_devices_stat)
database_thread = Thread(target=database_manage)
plug_thread = Thread(target=read_plug)
ai_thread = Thread(target=evaluation)
direct_command_thread = Thread(target=handle_direct_command)
additional_websocket_thread = Thread(target=start_websocket_server)
mobile_thread.start()
# automation_thread.start()
fetch_devices_thread.start()
# database_thread.start()
# plug_thread.start()
ai_thread.start()
additional_websocket_thread.start()
direct_command_thread.daemon = True
direct_command_thread.start()
mobile_thread.join()
# automation_thread.join()
fetch_devices_thread.join()
# database_thread.join()
# plug_thread.join()
ai_thread.join()
# additional_websocket_thread.join()
