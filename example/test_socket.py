import socket
import json
import threading

power = True
brightness = 3
operation = "white"
def update_value(new_value):
    # Update the value here with the received new_value
    global power, brightness, operation
    print(new_value)
    data = json.loads(new_value)
    if "power" in data: power = data["power"]
    if "brightness" in data: brightness = data["brightness"]
    if "operation" in data: operation = data["operation"]

def handle_client(client_socket):
    while True:
        try:
            # Receive data from the client
            request = client_socket.recv(1024).decode()

            # Handle the received data (update the value)
            if(("Hello") not in request):
                update_value(request)
            print("run")
            data = {
                'power': power,
                'brightness': brightness,
                'operation': operation
            }
            json_data = json.dumps(data)
            print(json_data)
            client_socket.send((json_data +"\n").encode())

        except Exception as e:
            print("Exception:", e)
            break

    client_socket.close()

server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

# Get local machine name and port
host = socket.gethostname()  # Replace with your server IP or 'localhost'
port = 12345        # Replace with your desired port

# Bind to the port
server_socket.bind((host, port))

# Listen for incoming connections
server_socket.listen(5)
print('Waiting for connections...')

def update_data():
    global brightness
    while True:
        brightness = input("Enter brightness value: ")
        data = {
            'power': power,
            'brightness': brightness,
            'operation': operation
        }
        json_data = json.dumps(data)
        client_socket.send((json_data + "\n").encode())
while True:
    # Accept a new connection
    client_socket, addr = server_socket.accept()
    print('Got connection from', addr)

    # Start a new thread to handle the client
    client_thread = threading.Thread(target=handle_client, args=(client_socket,))
    value_thread = threading.Thread(target=update_data)
    client_thread.start()
    value_thread.start()

