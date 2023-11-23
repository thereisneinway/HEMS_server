import device_control_and_mq as dc
import schedule
import time

ACCESS_ID = ""
ACCESS_KEY = ""
API_ENDPOINT = "https://openapi.tuyaus.com"
#MQ_ENDPOINT = "wss://mqe.tuyaus.com:8285/"
DEVICE_ID = "eb516998767c5669ebyyrl"
def obtain_light_info(access_endpoint:str, access_id:str, access_key:str, device_id:str):
    response = list(dc.obtain_deviceinfo(dc.connect_to_tuya(access_endpoint,access_id,access_key),device_id).values())
    power_status = response[0][0]['value']
    light_mode = response[0][1]['value']
    brightness_value = response[0][2]['value']
    return power_status, light_mode, brightness_value

def api_to_database():
    arg = obtain_light_info(API_ENDPOINT,ACCESS_ID,ACCESS_KEY,DEVICE_ID)
    #Save arg some how