import tuya_instructions as ti
import schedule
import time
import socket
import json
import threading

# Tuya API Information
ACCESS_ID = "11860382c9802039h3ta"
ACCESS_KEY = "adc69aab797049bd9426c623e9cad681"
API_ENDPOINT = "https://openapi.tuyaus.com"

# Database Information
MySQL_HOST = 'localhost'
MySQL_USERNAME = 'root'
MySQL_PASSWORD = 'root'

# Socket Information
host = socket.gethostname()
port = 12345

# Device id
DEVICES = []


# Handling devices list: Not in use yet
def save_devices():
    with open('devices.txt', 'w') as devices_file:
        devices_file.write(json.dumps(DEVICES))


def load_devices():
    global DEVICES
    DEVICES = json.load(open("devices.txt"))


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
        else: return True
    else: return False


def add_device(device_name: str, device_id: str, args: dict):
    print("hello")


def command_to_api(device_name: str,new_settings: dict):  # identify device and send command to tuya (run by command_from_mobile)
    device = next((sub for sub in DEVICES if sub['Device_name'] == device_name), None)
    device['SET'] = new_settings
    ti.command(API_ENDPOINT, ACCESS_ID, ACCESS_KEY, device)


def fetch_devices_stat_old(
        device: dict):  # requesting device status from tuya (run by update_device_status_toMobile) TO BE REMOVE
    device_type = device.get("Device_type")
    device_id = device.get("Device_id")
    if device_type == "RGB_Light":
        power_status, light_mode, brightness_value, colour_value = ti.obtain_rgb_light_info(API_ENDPOINT, ACCESS_ID,ACCESS_KEY, device_id)
        new_status = {
            "Power": power_status,
            "Mode": light_mode,
            "Brightness": brightness_value,
            "Colour": colour_value
        }
        device.__setitem__("STATUS", new_status)
    elif device_type == "CCT_Light":
        power_status, light_mode, brightness_value, light_temp_value = ti.obtain_cct_light_info(API_ENDPOINT, ACCESS_ID,ACCESS_KEY, device_id)
        new_status = {
            "Power": power_status,
            "Mode": light_mode,
            "Brightness": brightness_value,
            "Light_temp": light_temp_value
        }
        device.__setitem__("STATUS", new_status)
    elif device_type == "plug":
        power_status = ti.obtain_plug_info(API_ENDPOINT, ACCESS_ID, ACCESS_KEY, device_id)
        new_status = {
            "Power": power_status
        }
        device.__setitem__("STATUS", new_status)
    return device

def fetch_devices_stat(device: dict):
    ti.request(API_ENDPOINT,ACCESS_ID,ACCESS_KEY,device)



def update_device_to_mobile(client_socket):  # Updating new value to mobile (when changes occur)
    #Update client first time
    for i in DEVICES:
        data = i.get("STATUS")
        data["Device_name"] = i["Device_name"]
        json_data = json.dumps(data)
        try:
            client_socket.send((json_data + "\n").encode())
            print("update_device_to_mobile send")
        except Exception as e:
            print("update_device_to_mobile error ", e)
            break
    while client_socket:
        for i in DEVICES:
            # request devices status from Tuya to dict
            fetch_devices_stat(i)
            # compare variable to file
            if diff_devices(i):
                # update new status to file
                save_devices()
                # update new status to phone
                data = i.get("STATUS")
                data["Device_name"] = i["Device_name"]
                json_data = json.dumps(data)
                try:
                    client_socket.send((json_data + "\n").encode())
                    print("update_device_to_mobile send")
                except Exception as e:
                    print("update_device_to_mobile error ", e)
                    break
            else:
                try:
                    client_socket.send(("no update" + "\n").encode())
                    print("update_device_to_mobile send")
                except Exception as e:
                    print("update_device_to_mobile error ", e)
                    break
        else: continue
        break
        #Schedule section


def handle_mobile_client(client_socket):  # Handling request from mobile (on demand)
    while True:
        try:
            # Receive data from the client and interpret type
            request = client_socket.recv(1024).decode()
            
            print(request)
            json_data = json.loads(request)
            msg_type = json_data["type"]
            # Handle command
            if msg_type == "command":
                print("Command valid================================")
                device_name = json_data["Device_name"]
                print(json_data)
                del json_data["Device_name"]
                arg = json_data["arg"]
                command_to_api(device_name, arg)
                # client_socket.send((json_data +"\n").encode()) send straight to client
            # Handle add_device (not implement yet)
            elif msg_type == "add_device":
                print("add device not implemented yet")
            elif msg_type == "set_schedule":
                print("Set schedule not implemented yet")
        except Exception as e:
            print("Handle_mobile_client error ", e)
            client_socket.close()
            break


def connect_to_mobile():  # Initialize function
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind((host, port))
    server_socket.listen(5)
    while True:
        # Accept a new connection
        client_socket, addr = server_socket.accept()
        print('Got connection from', addr)

        # Start a new threads to handle the client
        client_thread = threading.Thread(target=handle_mobile_client, args=(client_socket,))
        value_thread = threading.Thread(target=update_device_to_mobile, args=(client_socket,))
        client_thread.start()
        value_thread.start()
        client_thread.join()
        value_thread.join()


print("Initialized")
# schedule.every(3).seconds.do(api_to_database)
# while True:
#    schedule.run_pending()
#    time.sleep(1)
'''set = {
        "Power": True,
        "Brightness": 100,
        "Colour": "{\"h\":180,\"s\":1000,\"v\":1000}",
        "Mode": "white"
    }
command_to_api(DEVICES[0],set)'''
load_devices()
mobile_thread = threading.Thread(target=connect_to_mobile)
mobile_thread.start()
mobile_thread.join()

# DEVICES[0] = fetch_devices_stat(DEVICES[0])
# print(str(DEVICES[0].get("STATUS")))
# di.append_to_database_table(MySQL_HOST,MySQL_USERNAME,MySQL_PASSWORD,DEVICES[0],time.strftime('%Y-%m-%d %H:%M:%S'))
