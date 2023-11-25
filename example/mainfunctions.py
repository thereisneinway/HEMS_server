import maininstructions as mi
import schedule
import time
import mysql.connector

ACCESS_ID = ""
ACCESS_KEY = ""
API_ENDPOINT = "https://openapi.tuyaus.com"
# MQ_ENDPOINT = "wss://mqe.tuyaus.com:8285/"
DEVICES_ID = ["eb516998767c5669ebyyrl"]

MySQL_HOST = 'localhost'
MySQL_USERNAME = 'root'
MySQL_PASSWORD = 'root'


def database_create_table(device_type: str,device_name: str):  # This function is to create table in database representing log of one device (only run when no table found)
    MySQL = mysql.connector.connect(host=MySQL_HOST, database='records', user=MySQL_USERNAME, password=MySQL_PASSWORD,connection_timeout=180000)
    cursor = MySQL.cursor()
    cursor.execute("select database();")
    cursor.fetchone()
    if device_type == "light":
        cursor.execute("SHOW TABLES LIKE '"+device_name+"'")
        result = cursor.fetchone()
        if not result:
            query = "CREATE TABLE "+device_name+" (id varchar(30) NOT NULL, power_state int NOT NULL, brightness_level int NOT NULL, PRIMARY KEY (id))"
            cursor.execute(query)
            cursor.fetchone()
    elif device_type == "plug":
        cursor.execute("SHOW TABLES LIKE '" + device_name + "'")
        result = cursor.fetchone()
        if not result:
            query = "CREATE TABLE " + device_name + " (id varchar(30) NOT NULL, power_state int NOT NULL, power_con int NOT NULL, PRIMARY KEY (id))"
            cursor.execute(query)
            cursor.fetchone()
    cursor.close()
    MySQL.close()


def append_to_database_table(device_id: str, device_type: str, device_name: str, args: []):
    MySQL = mysql.connector.connect(host=MySQL_HOST, database='records', user=MySQL_USERNAME, password=MySQL_PASSWORD)
    cursor = MySQL.cursor()
    if device_type == "light":
        cursor.execute("SHOW TABLES LIKE '" + device_name + "'")
        result = cursor.fetchone()
        if result:
            query = "INSERT INTO "+device_name+" (id, power_state, brightness_level) VALUES (%s, %i, %i)"
            val = (device_id, args[0], args[1])
            cursor.execute(query,val)
            cursor.fetchone()
        else:
            database_create_table(device_type,device_name)
    elif device_type == "plug":
        cursor.execute("SHOW TABLES LIKE '" + device_name + "'")
        result = cursor.fetchone()
        if result:
            query = "INSERT INTO " + device_name + " (id, power_state, power_con) VALUES (%s, %s, %s)"
            val = (device_id, args[0], args[1])
            cursor.execute(query,val)
            MySQL.commit()
            cursor.fetchone()
        else:
            database_create_table(device_type, device_name)
    cursor.close()
    MySQL.close()


def connect_to_mobile():  # This function initialize connection between apps and server (run when mobile call)
    arg = "a"


def api_to_database():  # This function is to call any obtain_device_info instructions (run by schedule)
    arg = mi.obtain_light_info(API_ENDPOINT, ACCESS_ID, ACCESS_KEY, DEVICES_ID[0])
    # append args to database


def command_to_api(device_id: str):  # This function is to send command to tuya (run by command_from_mobile)
    arg = mi.set_light(API_ENDPOINT, ACCESS_ID, ACCESS_KEY, device_id, True, 100)


def current_to_mobile():  # This function is to send all devices status to mobile (run when mobile call)
    arg = "a"


def command_from_mobile():  # This function is to interpret command from mobile (run when mobiel call)
    command_to_api(DEVICES_ID[0])


def power_usage_database_to_mobile():  # This function is to send historical power usage data to mobile from database (run when mobile call)
    arg = "a"


append_to_database_table("afghhfosidj3doik934","plug", "akb",[1,20])
