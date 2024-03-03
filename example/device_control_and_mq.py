
from tuya_connector import TuyaOpenAPI

def connect_to_tuya(access_endpoint: str, access_id: str, access_key: str):
    openapi = TuyaOpenAPI(access_endpoint, access_id, access_key)
    openapi.connect()
    return openapi

def obtain_deviceinfo(openapi: TuyaOpenAPI, device_id: str):
    response = openapi.get("/v1.0/iot-03/devices/{}/status".format(device_id))
    return response

def obtain_instruction(openapi: TuyaOpenAPI, device_id: str):
    response = openapi.get("/v1.0/iot-03/devices/{}/functions".format(device_id))
    return response

def send_command(openapi: TuyaOpenAPI, device_id: str, args: []):
    commands = {'commands': args}
    response = openapi.post('/v1.0/iot-03/devices/{}/commands'.format(device_id), commands)
    return response