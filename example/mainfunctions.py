from time import sleep
import tuya_instructions as ti
import database_instructions as da
from socket import socket, AF_INET, SOCK_STREAM, gethostname, gethostbyname
import json
from threading import Thread
import logging
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
    "TABLE_NAME": "main",
    "USERNAME": "doadmin",
    "PASSWORD": "",
    "CA_Path": "/ca-certificate.crt"
}
# Socket Information
Socket_hostname = gethostname()
Socket_hostip = gethostbyname(Socket_hostname)
Socket_port = 12345
# Delay settings
delay_automation = 60
delay_database = 60
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
            logger.info(str(datetime.now()) + " Automation text send to mobile: " + i["Name"])
        except Exception as e:
            logger.error(str(datetime.now()) + " Automation error sending text to mobile: ", e)
            break


#############################Main functions##############################
# Check and run automation
def manage_automation():  # check automation condition periodically and run (periodically)
    logger.info("Automation started")
    while True:
        sleep(delay_automation)  # Delay automation doubling
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
            if do:
                for j in i["Then"]:
                    # Obtain device status Device_name = Device_name in Then[]
                    device = next((sub for sub in DEVICES if sub['Device_name'] == j["Device_name"]), None)
                    # check if device is already at that value in Then
                    current_value = device.get(j["variable"])
                    if current_value != j["value"]:
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
                        # Suspected that might not work e.g. 'True' and True


# Pull device status from Tuya
def fetch_devices_stat():
    while True:
        try:
            for i in DEVICES:
                ti.request(API_ENDPOINT, ACCESS_ID, ACCESS_KEY, i)  # can improve by call each device by each thread
        except Exception as e:
            logger.error(str(datetime.now()) + "fetch_devices_stat  " + " error: "+ str(e))


# Push message mobile application (when connected)
def update_device_to_mobile(client_socket):  # Updating new value to mobile (periodically, when changes occur)
    # Update client first time
    for i in DEVICES:
        data = i.get("STATUS")
        data["msg_type"] = "Device_update"  # new line added here, haven't implemented in mobile app yet
        data["Device_name"] = i["Device_name"]
        json_data = json.dumps(data)
        try:
            client_socket.send((json_data + "\n").encode())
            logger.info(str(datetime.now()) + " Device initial text send to mobile: " + data["Device_name"])
        except Exception as e:
            logger.error(str(datetime.now()) + " Device error sending initial text to mobile: ", e)
            break
    while client_socket:
        for i in DEVICES:
            if "close" in str(client_socket):
                logger.warning(str(datetime.now()) + " update_device_to_mobile thread closing due to socket")
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
                    logger.info(str(datetime.now()) + " Device text send to mobile: " + data["Device_name"])
                except Exception as e:
                    logger.error(str(datetime.now())+ " Device error sending text to mobile: ", e)
                    break
        else:
            continue
        break


# Handling command from mobile application (when connected)
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
                logger.info(str(datetime.now()) + " Received device command from mobile: " + str(json_data))
                del json_data["Device_name"]
                arg = json_data["arg"]
                command_to_api(device_name, arg)
            elif msg_type == "request_automation_list":
                push_automation_info_to_mobile(client_socket)
            elif msg_type == "set_automation":
                command_type = json_data["type"]
                logger.info(str(datetime.now()) + " Received request automation list from mobile: " + str(json_data))
                if command_type == "add":
                    add_automation(json_data)
                elif command_type == "set":
                    remove_automation(json_data["Name"])
                    add_automation(json_data)
                elif command_type == "remove":
                    remove_automation(json_data["Name"])
        except Exception as e:
            logger.error(str(datetime.now()) + " Handling mobile thread error: ", e)
            client_socket.close()
            break


# Handle incoming socket from mobile application
def connect_to_mobile():  # Initialize function
    server_socket = socket(AF_INET, SOCK_STREAM)
    server_socket.bind((Socket_hostname, Socket_port))
    server_socket.listen(5)
    logger.info(str(datetime.now()) + " System initialized: " + Socket_hostname + " " + Socket_hostip)
    while True:
        # Accept a new connection
        client_socket, addr = server_socket.accept()
        logger.info(str(datetime.now())+ ' Got connection from', addr)

        # Start a new threads to handle the client
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

logger.info("Settings: \n     Delay for Automation:" + str(delay_automation) + "\n     Delay for Database:" + str(
    delay_database) + "\n     Database site: " + MySQL_connection_details.get("HOST"))
load_devices_from_file()
load_automation_from_file()
mobile_thread = Thread(target=connect_to_mobile)
automation_thread = Thread(target=manage_automation)
fetch_devices_thread = Thread(target=fetch_devices_stat)
database_thread = Thread(target=database_manage)
mobile_thread.start()
automation_thread.start()
fetch_devices_thread.start()
database_thread.start()
mobile_thread.join()
automation_thread.join()
fetch_devices_thread.join()
database_thread.join()
