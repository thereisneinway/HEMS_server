import tuya_instructions as ti
import database_instructions as di
import schedule
import time
import mysql.connector
import socket
import json
import threading

#Tuya API Information
ACCESS_ID = ""
ACCESS_KEY = ""
API_ENDPOINT = "https://openapi.tuyaus.com"
# MQ_ENDPOINT = "wss://mqe.tuyaus.com:8285/"

#Database Information
MySQL_HOST = 'localhost'
MySQL_USERNAME = 'root'
MySQL_PASSWORD = 'root'

#Socket Information
host = socket.gethostname()
port = 12345

#Device id (Prototype)
DEVICES = [
    {
        "Device_id": "7268165584f3ebec8a6f",
        "Device_name" : "Shower",
        "Device_type": "RGB_Light",
        "CODE": {
            "Power": "switch_led",
            "Brightness": "bright_value_v2",
            "Colour": "colour_data_v2",
            "Mode": "work_mode"
        },
        "STATUS": {
            "Power": True,
            "Brightness": 1000,
            "Colour": "{\"h\":180,\"s\":1000,\"v\":1000}",
            "Mode": "white"
        }
    },{
        "Device_id": "2276015684f3ebbddd47",
        "Device_name" : "RR",
        "Device_type": "CCT_Light",
        "CODE": {
            "Power": "switch_led",
            "Brightness": "bright_value_v2",
            "Light_temp": "temp_value_v2",
            "Mode": "work_mode"
        },
        "STATUS": {
            "Power": True,
            "Brightness": 1000,
            "Light_temp": 470,
            "Mode": "white"
        }
    },{
        "Device_id": "2276015684f3eb66ee14",
        "Device_name" : "RL",
        "Device_type": "CCT_Light",
        "CODE": {
            "Power": "switch_led",
            "Brightness": "bright_value_v2",
            "Light_temp": "temp_value_v2",
            "Mode": "work_mode"
        },
        "STATUS": {
            "Power": True,
            "Brightness": 1000,
            "Light_temp": 470,
            "Mode": "white"
        }
    },{
        "Device_id": "2276015684f3eb66eb73",
        "Device_name" : "FR",
        "Device_type": "CCT_Light",
        "CODE": {
            "Power": "switch_led",
            "Brightness": "bright_value_v2",
            "Light_temp": "temp_value_v2",
            "Mode": "work_mode"
        },
        "STATUS": {
            "Power": True,
            "Brightness": 1000,
            "Light_temp": 470,
            "Mode": "white"
        }
    },{
        "Device_id": "46453170cc50e3eb112f",
        "Device_name" : "FL",
        "Device_type": "CCT_Light",
        "CODE": {
            "Power": "switch_led",
            "Brightness": "bright_value_v2",
            "Light_temp": "temp_value_v2",
            "Mode": "work_mode"
        },
        "STATUS": {
            "Power": True,
            "Brightness": 1000,
            "Light_temp": 470,
            "Mode": "white"
        }
    },{
        "Device_id": "ebb742d982de954ecc8icb",
        "Device_name" : "book",
        "Device_type": "plug",
        "CODE": {
            "Power": "switch_1"
        },
        "STATUS": {
            "Power": True
        }
    }
]

def command_to_api(device_name:str, new_settings:dict):  # identify device and send command to tuya (run by command_from_mobile)
    device = next((sub for sub in DEVICES if sub['Device_name'] == device_name), None)
    device['SET'] = new_settings
    ti.command(API_ENDPOINT, ACCESS_ID, ACCESS_KEY, device)

def fetch_devices_stat(device:dict): # requesting device status from tuya (run by update_device_status_toMobile)
    device_type = device.get("Device_type")
    device_id = device.get("Device_id")
    if device_type == "RGB_Light" :
        power_status, light_mode, brightness_value, colour_value = ti.obtain_rgb_light_info(API_ENDPOINT, ACCESS_ID, ACCESS_KEY, device_id)
        new_status = {
            "Power": power_status,
            "Mode": light_mode,
            "Brightness": brightness_value,
            "Colour": colour_value
        }
        device.__setitem__("STATUS",new_status)
    elif device_type == "CCT_Light" :
        power_status, light_mode, brightness_value, light_temp_value = ti.obtain_light_info(API_ENDPOINT, ACCESS_ID, ACCESS_KEY, device_id)
        new_status = {
            "Power": power_status,
            "Mode": light_mode,
            "Brightness": brightness_value,
            "Light_temp": light_temp_value
        }
        device.__setitem__("STATUS", new_status)
    elif device_type == "plug" :
        power_status = ti.obtain_plug_info(API_ENDPOINT, ACCESS_ID, ACCESS_KEY, device_id)
        new_status = {
            "Power": power_status
        }
        device.__setitem__("STATUS", new_status)
    return device

#Handling mobile clients: prototype

def update_device_status_toMobile(client_socket): #prototype
    while True:
        time.sleep(2)
        fetch_devices_stat(DEVICES[0])
        data = DEVICES[0].get("STATUS")
        json_data = json.dumps(data)
        print("Replying mobile:")
        print(json_data)
        try: client_socket.send((json_data + "\n").encode())
        except: print("No mobile")
def handle_mobile_client(client_socket): #Handling request from mobile (on demand)
    while True:
        try:
            # Receive data from the client
            request = client_socket.recv(1024).decode()

            # Handle the received data (update the value)
            if (("Hello") not in request):
                print("Command valid :")
                json_data = json.loads(request)
                device_name = json_data["Device_name"]
                del json_data["Device_name"]
                print(json_data)
                command_to_api(device_name, json_data)
                #client_socket.send((json_data +"\n").encode()) send straight to client
        except Exception as e:
            print("Exception:", e)
            break

    client_socket.close()

def connect_to_mobile():
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind((host, port))
    server_socket.listen(5)
    while True:
        # Accept a new connection
        client_socket, addr = server_socket.accept()
        print('Got connection from', addr)

        # Start a new thread to handle the client
        client_thread = threading.Thread(target=handle_mobile_client, args=(client_socket,))
        value_thread = threading.Thread(target=update_device_status_toMobile, args=(client_socket,))
        client_thread.start()
        value_thread.start()
        client_thread.join()
        value_thread.join()

print("Initialized")
#schedule.every(3).seconds.do(api_to_database)
#while True:
#    schedule.run_pending()
#    time.sleep(1)
'''set = {
        "Power": True,
        "Brightness": 100,
        "Colour": "{\"h\":180,\"s\":1000,\"v\":1000}",
        "Mode": "white"
    }
command_to_api(DEVICES[0],set)'''
mobile_thread = threading.Thread(target=connect_to_mobile)
mobile_thread.start()
mobile_thread.join()
#DEVICES[0] = fetch_devices_stat(DEVICES[0])
#print(str(DEVICES[0].get("STATUS")))
#di.append_to_database_table(MySQL_HOST,MySQL_USERNAME,MySQL_PASSWORD,DEVICES[0],time.strftime('%Y-%m-%d %H:%M:%S'))
