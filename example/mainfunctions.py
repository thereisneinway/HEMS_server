from time import sleep
import tuya_instructions as ti
import database_instructions as da
import socket
import json
import threading
import logging
from datetime import datetime
from sys import stdout

###############################Spec define###############################
# Tuya API Information
ACCESS_ID = ""
ACCESS_KEY = ""
API_ENDPOINT = "https://openapi.tuyaus.com"
# Database Information
MySQL_HOST = 'localhost'
MySQL_USERNAME = 'root'
MySQL_PASSWORD = 'root'
# Socket Information
host = socket.gethostname()
hostip = socket.gethostbyname(host)
port = 12345

#########################Declare global variable#########################
DEVICES = []
AUTOMATION = []

################################Debug log################################
logging.basicConfig(stream=stdout, level=logging.INFO)
logger = logging.getLogger('c')
logger.setLevel(logging.DEBUG)

##############################Sub functions##############################
# Handling DEVICES file
def save_devices_to_file():
    with open('devices.txt', 'w') as devices_file:
        devices_file.write(json.dumps(DEVICES))
def load_devices_from_file():
    global DEVICES
    DEVICES = json.load(open("devices.txt"))
    for i in DEVICES:
        logger.info("Device loaded: "+i.get("Device_name"))
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
            if dict1[key] != dict2[key]: return True
        else:
            return True
    else:
        return False
#Handling AUTOMATION file
def save_automation_to_file():
    with open('automations.txt', 'w') as automation_file:
        automation_file.write(json.dumps(AUTOMATION))
def load_automation_from_file():
    global AUTOMATION
    AUTOMATION = json.load(open("automations.txt"))
    for i in AUTOMATION:
        logger.info("Automation loaded: " +i.get("Name"))

#Identify device and send command to tuya (run by command_from_mobile)
def command_to_api(device_name: str,new_settings: dict):
    device = next((sub for sub in DEVICES if sub['Device_name'] == device_name), None)
    device['SET'] = new_settings
    ti.command(API_ENDPOINT, ACCESS_ID, ACCESS_KEY, device)
    logger.info("Command passed to Tuya instruction: "+ device_name)

#Automation handling
def add_automation(json_data):  # add an automation (run by handle_mobile_client)
    global AUTOMATION
    # if (json_data has Name, If, Then) ->
    AUTOMATION.append(json_data)
    save_automation_to_file()
def remove_automation(name: str):  # remove an automation (run by handle_mobile_client)
    for i in AUTOMATION:
        if i.get("Name") == name:
            del AUTOMATION[i]
    save_automation_to_file()
def push_automation_info_to_mobile(client_socket):  # send list of automations (run by handle_mobile_client)
    load_automation_from_file()
    for i in AUTOMATION:
        data = i
        data["msg_type"] = "Automation_update"
        json_data = json.dumps(i)
        try:
            client_socket.send((json_data + "\n").encode())
            logger.info("Automation text send to mobile: " + i["Name"])
        except Exception as e:
            logger.error("Automation error sending text to mobile: ", e)
            break

#############################Main functions##############################
#Check and run automation
def manage_automation():  # check automation condition periodically and run (periodicially)
    logger.info("Automation started")
    while True:
        sleep(60) # Delay automation doubling
        for i in AUTOMATION:
            do = True
            # If for j in i:
            for j in i["If"]:
                if j.get("Type") == "Condition":
                    device = next((sub for sub in DEVICES if sub['Device_name'] == j["Device_name"]), None)
                    # pull data from sensor Device_name = Device_name in If[]
                    target_value = device.get('STATUS').get(j["variable"])
                    # check condition value within value in If
                    if target_value != j["value"]:
                        do = False
                elif j.get("Type") == "Schedule":
                    tf = datetime.strptime(j.get("From"), '%H:%M:%S').strftime('%H:%M:%S')
                    tt = datetime.strptime(j.get("To"), '%H:%M:%S').strftime('%H:%M:%S')
                    tc = datetime.now().strftime('%H:%M:%S')
                    if not tf < tc < tt:
                        do = False
            # Then for j in i:
            if do == True:
                for j in i["Then"]:
                    # Obtain device status Device_name = Device_name in Then[]
                    device = next((sub for sub in DEVICES if sub['Device_name'] == j["Device_name"]), None)
                    # check if device is already at that value in Then
                    current_value = device.get(j["variable"])
                    if current_value != j["value"]:
                        logger.debug("Automation task execute: "+i["Name"])
                        # Execute
                        execute: json
                        if type(j["value"]) == str:
                            execute = json.loads('{"' + j["variable"] + '": "' + j["value"] + '"}')
                        elif type(j["value"]) == bool:
                            execute = json.loads('{"' + j["variable"] + '": ' + str.lower(str(j["value"])) + '}')
                        else:
                            execute = json.loads('{"' + j["variable"] + '": ' + str(j["value"]) + '}')
                        command_to_api(j["Device_name"], execute)
                        # Suspected that might not work eg. 'True' and True
#Pull device status from Tuya
def fetch_devices_stat():
    while True:
        for i in DEVICES:
            ti.request(API_ENDPOINT, ACCESS_ID, ACCESS_KEY, i) #can improve by call each device by each thread
#Push message mobile application (when connected)
def update_device_to_mobile(client_socket):  # Updating new value to mobile (periodicially, when changes occur)
    # Update client first time
    for i in DEVICES:
        data = i.get("STATUS")
        data["msg_type"] = "Device_update"  # new line added here, haven't implement in mobile app yet
        data["Device_name"] = i["Device_name"]
        json_data = json.dumps(data)
        try:
            client_socket.send((json_data + "\n").encode())
            logger.info("Device initial text send to mobile: " + data["Device_name"])
        except Exception as e:
            logger.error("Device error sending initial text to mobile: ", e)
            break
    while client_socket:
        for i in DEVICES:
            if "close" in str(client_socket):
                logger.warning("update_device_to_mobile thread closing due to socket")
                break
            # compare variable to file
            if diff_devices(i):
                # update new status to file
                save_devices_to_file()
                # update new status to phone
                data = i.get("STATUS")
                data["Device_name"] = i["Device_name"]
                json_data = json.dumps(data)
                try:
                    client_socket.send((json_data + "\n").encode())
                    logger.info("Device text send to mobile: " + data["Device_name"])
                except Exception as e:
                    logger.error("Device error sending text to mobile: ", e)
                    break
            else:
                logger.info("Device text no send")
        else:
            continue
        break
#Handling command from mobile application (when connected)
def handle_mobile_client(client_socket):  # Handling request from mobile (on demand)
    while True:
        try:
            # Receive data from the client and interpret type
            request = client_socket.recv(1024).decode()
            json_data = json.loads(request)
            msg_type = json_data["type"]
            # Handle command
            if msg_type == "command":
                device_name = json_data["Device_name"]
                logger.info("Received device command from mobile: " + str(json_data))
                del json_data["Device_name"]
                arg = json_data["arg"]
                command_to_api(device_name, arg)
            elif msg_type == "request_automation_list":
                push_automation_info_to_mobile(client_socket)
            elif msg_type == "set_automation":
                automation_name = json_data["automation_name"]
                type = json_data["type"]
                logger.info("Received request automation list from mobile: " + str(json_data))
                del json_data["automation_name"]
                if (type == "add"):
                    add_automation(json_data)
                elif (type == "set"):
                    remove_automation(json_data["Name"])
                    add_automation(json_data)
                elif (type == "remove"):
                    remove_automation(json_data["Name"])
        except Exception as e:
            logger.error("Handling mobile thread error: ", e)
            client_socket.close()
            break
#Handle incoming socket from mobile application
def connect_to_mobile():  # Initialize function
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind((host, port))
    server_socket.listen(5)
    logger.info("System initialized: " + host + " " + hostip)
    while True:
        # Accept a new connection
        client_socket, addr = server_socket.accept()
        logger.info('Got connection from', addr)

        # Start a new threads to handle the client
        client_thread = threading.Thread(target=handle_mobile_client, args=(client_socket,))
        value_thread = threading.Thread(target=update_device_to_mobile, args=(client_socket,))
        client_thread.start()
        value_thread.start()
        client_thread.join()
        value_thread.join()
#Append device status to Tuya
def database_manage():
    while True:
        da.append_to_database(MySQL_HOST, MySQL_USERNAME, MySQL_PASSWORD, DEVICES, datetime.now())
        sleep(2)


load_devices_from_file()
load_automation_from_file()
mobile_thread = threading.Thread(target=connect_to_mobile)
automation_thread = threading.Thread(target=manage_automation)
fetch_devices_thread = threading.Thread(target=fetch_devices_stat)
database_thread = threading.Thread(target=database_manage)
mobile_thread.start()
automation_thread.start()
fetch_devices_thread.start()
database_thread.start()
mobile_thread.join()
automation_thread.join()
fetch_devices_thread.join()
database_thread.join()