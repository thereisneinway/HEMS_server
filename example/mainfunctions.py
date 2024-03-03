import tuya_instructions as ti
import socket
import json
import threading

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

# Device id
DEVICES = []

# Handling devices list
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
            print("SEND: update_device_to_mobile " + data["Device_name"])
        except Exception as e:
            print("SEND: error ", e)
            break
    while client_socket:
        for i in DEVICES:
            if "close" in str(client_socket):
                print("SEND: thread closing")
                break
            # request devices status from Tuya to dict
            fetch_devices_stat(i)
            # compare variable to file
            if diff_devices(i):
                # update new status to file
                save_devices()
                # update new status to phone
                data = i.get("STATUS")
                print("SEND: data:" + str(data))
                data["Device_name"] = i["Device_name"]
                json_data = json.dumps(data)
                try:
                    client_socket.send((json_data + "\n").encode())
                    print("SEND: update_device_to_mobile " + data["Device_name"])
                except Exception as e:
                    print("SEND: error ", e)
                    break
            else:
                print("SEND: no send")
        else: continue
        break


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
                print("RECE: " + str(json_data))
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
            print("RECE: error ", e)
            client_socket.close()
            break


def connect_to_mobile():  # Initialize function
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind((host, port))
    server_socket.listen(5)
    print("HOST NAME: " + host + " "+hostip)
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


load_devices()
print("mt: initialized")
mobile_thread = threading.Thread(target=connect_to_mobile)
mobile_thread.start()
mobile_thread.join()


'''old version of update_device functions

def update_device_to_mobile(client_socket):  # Updating new value to mobile (when changes occur)
    #Update client first time
    for i in DEVICES:
        data = i.get("STATUS")
        data["Device_name"] = i["Device_name"]
        json_data = json.dumps(data)
        try:
            client_socket.send((json_data + "\n").encode())
            print("SEND: update_device_to_mobile " + data["Device_name"])
        except Exception as e:
            print("SEND: error ", e)
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
                    print("SEND: update_device_to_mobile " + data["Device_name"])
                except Exception as e:
                    print("SEND: error ", e)
                    break
            else:
                try:
                    client_socket.send(("no update" + "\n").encode())
                    print("SEND: send no update")
                except Exception as e:
                    print("SEND: error ", e)
                    break
        else: continue
        break
        
        SSL version
        
def connect_to_mobile():  # Initialize function
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM, 0)
    server_socket.bind((host, port))
    server_socket.listen(5)
    contextSSL = ssl.SSLContext(protocol=ssl.PROTOCOL_TLS_SERVER)
    contextSSL.load_cert_chain('cert/selfsigned.pem','cert/private.key')
    server_socket_ssl = contextSSL.wrap_socket(server_socket, server_side=True)
    while True:
        # Accept a new connection
        client_socket, addr = server_socket_ssl.accept()
'''