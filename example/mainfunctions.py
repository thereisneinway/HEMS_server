import maininstructions as mi
import schedule
import time
import mysql.connector

ACCESS_ID = ""
ACCESS_KEY = ""
API_ENDPOINT = "https://openapi.tuyaus.com"
#MQ_ENDPOINT = "wss://mqe.tuyaus.com:8285/"
DEVICE_ID = ["eb516998767c5669ebyyrl"]

def initialize_database(): #This function is to initialize database (run once)
    arg = "a"

def connect_to_mobile(): #This function initialize connection between apps and server (run when mobile call)
    arg = "a"

def api_to_database(): #This function is to call any obtain_device_info instructions (run by schedule)
    arg = mi.obtain_light_info(API_ENDPOINT,ACCESS_ID,ACCESS_KEY,DEVICE_ID[0])
    #append args to database
def command_to_api(device_id : str): #This function is to send command to tuya (run by command_from_mobile)
    arg = mi.set_light(API_ENDPOINT, ACCESS_ID, ACCESS_KEY, device_id, True, 100)

def current_to_mobile(): #This function is to send all devices status to mobile (run when mobile call)
    arg = "a"

def command_from_mobile(): #This function is to interpret command from mobile (run when mobiel call)
    command_to_api(DEVICE_ID[0])

def power_usage_database_to_mobile(): #This function is to send historical power usage data to mobile from database (run when mobile call)
    arg = "a"