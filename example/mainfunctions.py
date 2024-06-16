import tuya_instructions as ti
import database_instructions as da
import intelligent as ai
import json
import logging
from time import sleep
from socket import socket, AF_INET, SOCK_STREAM, gethostname, gethostbyname
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
    "HOST": "",
    "PORT": 25060,
    "DATABASE_NAME": "defaultdb",
    "TABLE_NAME": "test",
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
# AI settings
ai_functionality = False
# Declare global variable
DEVICES = []
AUTOMATION = []
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


# Identify device and send command to tuya (run by command_from_mobile)
def command_to_api(device_name: str, new_settings: dict):
    device = next((sub for sub in DEVICES if sub['Device_name'] == device_name), None)
    device['SET'] = new_settings
    ti.command(API_ENDPOINT, ACCESS_ID, ACCESS_KEY, device)
    logger.info(str(datetime.now()) + " Command passed to Tuya instruction: " + device_name)


# Automation handling
def add_automation(json_data):  # add an automation (run by handle_mobile_client) TESETED WORK!
    global AUTOMATION
    if json_data['If'] and json_data['Then']:
        AUTOMATION.append(json_data)
        return save_automation_to_file()
    else:
        return False


def remove_automation(name: str):  # remove an automation (run by handle_mobile_client) TESTED WORK!
    for i in AUTOMATION:
        if i.get("Name") == name:
            AUTOMATION.remove(i)
    return save_automation_to_file()


def push_automation_info_to_mobile(
        client_socket):  # send list of automations (run by handle_mobile_client) TESTED WORK!
    load_automation_from_file()
    for i in AUTOMATION:
        data = i
        data["msg_type"] = "Automation_update"
        json_data = json.dumps(data)
        try:
            client_socket.send((json_data + "\n").encode())
            logger.info(str(datetime.now()) + " Automation text send to mobile: " + i["Name"])
        except Exception as e:
            logger.error(str(datetime.now()) + " Automation error sending text to mobile: ", e)
            break


def push_ai_stat_to_mobile(client_socket):
    try:
        data = {"msg_type": "AI_functionality_update", "AI": ai_functionality}
        json_data = json.dumps(data)
        client_socket.send((json_data + "\n").encode())
        logger.info(str(datetime.now()) + " AI status sending to mobile: " + str(ai_functionality))
    except Exception as e:
        logger.error(str(datetime.now()) + " Device error sending initial text to mobile: ", e)


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
        try:
            for i in DEVICES:
                if i["Domain"] == "tuya":
                    ti.request(API_ENDPOINT, ACCESS_ID, ACCESS_KEY, i)  # can improve by call each device by each thread
        except Exception as e:
            logger.error(str(datetime.now()) + "fetch_devices_stat  " + " error: " + str(e))


# Push message mobile application (when connected)
def update_device_to_mobile(client_socket):
    for i in DEVICES:
        data = i.get("STATUS").copy()  # VER6 - not tested
        data["msg_type"] = "Device_update"
        data["Device_name"] = i["Device_name"]
        data["Device_type"] = i["Device_type"]
        json_data = json.dumps(data)
        try:
            client_socket.send((json_data + "\n").encode())
            logger.info(str(datetime.now()) + " Device initial text send to mobile: " + data["Device_name"])
        except Exception as e:
            logger.error(str(datetime.now()) + " Device error sending initial text to mobile: ", e)
            break
    push_automation_info_to_mobile(client_socket)
    push_ai_stat_to_mobile(client_socket)
    while client_socket:
        for i in DEVICES:
            if "close" in str(client_socket):
                logger.warning(str(datetime.now()) + " update_device_to_mobile thread closing due to socket")
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
                    logger.info(str(datetime.now()) + " Device text send to mobile: " + data["Device_name"])
                except Exception as e:
                    logger.error(str(datetime.now()) + " Device error sending text to mobile: ", e)
                    break
        else:
            continue
        break


# Handling command from mobile application (when connected)
def handle_mobile_client(client_socket):
    while True:
        try:
            request = client_socket.recv(1024).decode()
            json_data = json.loads(request)
            msg_type = json_data["type"]
            if msg_type == "command":
                domain = json_data["Domain"]
                if domain == "tuya":
                    device_name = json_data["Device_name"]
                    logger.info(str(datetime.now()) + " Received device command from mobile: " + str(json_data))
                    del json_data["Device_name"]
                    del json_data["Domain"]
                    arg = json_data["arg"]
                    command_to_api(device_name, arg)
                elif domain == "custom":
                    print("TO BE IMPLEMENTED")
            elif msg_type == "request_automation_list":
                push_automation_info_to_mobile(client_socket)
            elif msg_type == "set_automation":
                command_type = json_data["set_type"]
                logger.info(str(datetime.now()) + " Received request automation list from mobile: " + str(json_data))
                if command_type == "add":
                    del json_data["set_type"]
                    del json_data["type"]
                    do = True
                    for i in AUTOMATION:
                        if i.get("Name") == json_data["Name"]:
                            do = False
                    if do:
                        if add_automation(json_data):
                            client_socket.send((
                                                       "{'msg_type': 'Automation_instruction_response', 'status': 'Add success'}" + "\n").encode())
                        else:
                            client_socket.send((
                                                       "{'msg_type': 'Automation_instruction_response', 'status': 'Add failed'}" + "\n").encode())
                    else:
                        client_socket.send((
                                                   "{'msg_type': 'Automation_instruction_response', 'status': 'Add failed, Duplicated'}" + "\n").encode())
                elif command_type == "set":
                    del json_data["set_type"]
                    del json_data["type"]
                    exist = True
                    for i in AUTOMATION:
                        if i.get("Name") == json_data["Name"]:
                            exist = False
                    if exist:
                        if remove_automation(json_data["Name"]):
                            if add_automation(json_data):
                                client_socket.send((
                                                           "{'msg_type': 'Automation_instruction_response', 'status': 'Set success'}" + "\n").encode())
                        else:
                            client_socket.send((
                                                       "{'msg_type': 'Automation_instruction_response', 'status': 'Set failed'}" + "\n").encode())
                    else:
                        client_socket.send((
                                                   "{'msg_type': 'Automation_instruction_response', 'status': 'Set failed, Does not exist'}" + "\n").encode())
                elif command_type == "remove":
                    if remove_automation(json_data["Name"]):
                        client_socket.send((
                                                   "{'msg_type': 'Automation_instruction_response', 'status': 'Remove success'}" + "\n").encode())
                    else:
                        client_socket.send((
                                                   "{'msg_type': 'Automation_instruction_response', 'status': 'Remove failed'}" + "\n").encode())
            elif msg_type == "set_ai_functionality":
                global ai_functionality
                ai_functionality = json_data["set"]
                push_ai_stat_to_mobile(client_socket)
            elif msg_type == "request_energy_history_list": #TODO: TEST
                period = json_data["period"]
                energy_history_dict = da.query_energy(MySQL_connection_details,period,datetime.now())
                energy_history_dict["msg_type"] = "Energy_history"
                json_data = json.dumps(energy_history_dict)
                client_socket.send((json_data + "\n").encode())
        except Exception as e:
            logger.error(str(datetime.now()) + " Handling mobile thread error: ", e)
            client_socket.close()
            break


# Handle incoming socket from mobile application
def connect_to_mobile():
    server_socket = socket(AF_INET, SOCK_STREAM)
    server_socket.bind((Sockets_hostname, Socket_mobile_port))
    server_socket.listen(5)
    logger.info(str(datetime.now()) + " System initialized: " + Sockets_hostname + " " + Sockets_hostip)
    while True:
        client_socket, addr = server_socket.accept()
        logger.info(str(datetime.now()) + ' Got app connection from ' + str(addr))
        client_thread = Thread(target=handle_mobile_client, args=(client_socket,))
        value_thread = Thread(target=update_device_to_mobile, args=(client_socket,))
        client_thread.start()
        value_thread.start()
        client_thread.join()
        value_thread.join()


# Append device status to Tuya
def database_manage():
    while True:
        da.append_to_database(MySQL_connection_details, DEVICES, datetime.now())
        sleep(delay_database)


# AI function
def evaluate_device_status(): #Depreciated
    COMMAND_AI = []
    count = 0
    while True:
        if ai_functionality:
            try:
                COMMAND_AI = ai.evaluate_with_decision_tree(DEVICES)
                for i in COMMAND_AI:
                    device_name = i["Device_name"]
                    device = next((sub for sub in DEVICES if sub['Device_name'] == i["Device_name"]), None)
                    current_value = device.get("Power")
                    if current_value != i["Power"] and i["Power"] == 0: #ONLY TURN OFF, not turn on
                        del i["Device_name"]
                        command_to_api(device_name, i)
            except Exception as e:
                logger.error(str(datetime.now()) + " AI thread error: ", e)

        count += 1
        if count > 59:
            da.calculate_energy(MySQL_connection_details, datetime.now())
            logger.info(str(datetime.now()) + " Calculated energy and append to table")
            count = 0
        sleep(delay_ai)
        COMMAND_AI.clear()


# Receiving data from customize plug
def read_plug():  # VER 6 - need to be implemented
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
ai_thread = Thread(target=evaluate_device_status)
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
