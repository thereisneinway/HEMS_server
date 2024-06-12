import threading
from socket import socket, AF_INET, SOCK_STREAM, gethostname, gethostbyname
import json
from threading import Thread
DEVICES = []

#incoming message format {'Domain': 'custom', 'Device_name': 'custom_plug, 'STATUS': {'Power': <boolean>, 'Power_usage': <int>}
Socket_hostname = gethostname()
Socket_hostip = gethostbyname(Socket_hostname)
Socket_port = 12347
plug_server_socket = socket(AF_INET, SOCK_STREAM)
plug_server_socket.bind((Socket_hostname, Socket_port))
plug_server_socket.listen(5)
print("SOCKET AVAILABLE AT {}".format(Socket_hostip))
while True:
    client_socket, addr = plug_server_socket.accept()
    print('Got connection from ' + str(addr))
    request = client_socket.recv(1024).decode()
    if not request:
        break
    client_socket.close()
    #print(request)
    json_data = json.loads(request)
    print(json_data)
    for i in DEVICES:
        if json_data.get("Domain") == "custom":
            if json_data.get("Device_name") == i.get("Device_name"):
                try:
                    i.set("STATUS", json_data.get("STATUS"))
                except Exception as e:
                    #logger.error(str(datetime.now()) + " Append custom device to List not work: ", e)
                    print("a")
                break

#NEXT VER CODE

"""
def connect_plug():
    Socket_hostname = gethostname()
    Socket_port = 12347
    plug_server_socket = socket(AF_INET, SOCK_STREAM)
    plug_server_socket.bind((Socket_hostname, Socket_port))
    plug_server_socket.listen(5)
    while True:
        global plug_client_socket
        plug_client_socket, addr = plug_server_socket.accept()
        print('Got connection from ' + str(addr))
        request = plug_client_socket.recv(1024).decode()
        json_data = json.loads(request)
        print(json_data)
        for i in DEVICES:
            if json_data.get("Domain") == "custom":
                if json_data.get("Device_name") == i.get("Device_name"):
                    try:
                        i.set("STATUS", json_data.get("STATUS"))
                    except Exception as e:
                        print("a")
                    break
        

plug_client_socket: socket
plug_thread = Thread(target=connect_plug)
plug_thread.start()
plug_thread.join()

"""