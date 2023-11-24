import maininstructions as mi
import schedule
import time
import mysql.connector

ACCESS_ID = ""
ACCESS_KEY = ""
API_ENDPOINT = "https://openapi.tuyaus.com"
#MQ_ENDPOINT = "wss://mqe.tuyaus.com:8285/"
DEVICES_ID = ["eb516998767c5669ebyyrl"]

MySQL_HOST = 'localhost'
MySQL_USERNAME = "root"
MySQL_PASSWORD = "root"
def initialize_database(): #This function is to initialize database (run once)
    MySQL = mysql.connector.connect(host=MySQL_HOST,database='records',user=MySQL_USERNAME,password=MySQL_PASSWORD)
    if MySQL.is_connected():
        db_Info = MySQL.get_server_info()
        print("Connected to MySQL Server version ", db_Info)
        cursor = MySQL.cursor()
        cursor.execute("select database();")
        #record = cursor.fetchone()
        #cursor.execute("SET GLOBAL max_allowed_packet=67108864;")
        print("You're connected to database: ", record)
    return MySQL
def database_create_table(MySQL:mysql.connector,device_id:str,device_type:str,device_name:str): #This function is to create table in database representing log of one device (only run when no table found)
    mySql_Create_Table_Query = """" """
    if device_type == "light":
        mySql_Create_Table_Query = "CREATE TABLE ",device_name," (",device_id," string(20) NOT NULL,power_state int NOT NULL,brightness_level int NOT NULL,PRIMARY KEY (Id)) "
    cursor = MySQL.cursor()
    result = cursor.execute(mySql_Create_Table_Query)
    print(" Table created successfully ")
def connect_to_mobile(): #This function initialize connection between apps and server (run when mobile call)
    arg = "a"

def api_to_database(): #This function is to call any obtain_device_info instructions (run by schedule)
    arg = mi.obtain_light_info(API_ENDPOINT,ACCESS_ID,ACCESS_KEY,DEVICES_ID[0])
    #append args to database
def command_to_api(device_id : str): #This function is to send command to tuya (run by command_from_mobile)
    arg = mi.set_light(API_ENDPOINT, ACCESS_ID, ACCESS_KEY, device_id, True, 100)

def current_to_mobile(): #This function is to send all devices status to mobile (run when mobile call)
    arg = "a"

def command_from_mobile(): #This function is to interpret command from mobile (run when mobiel call)
    command_to_api(DEVICES_ID[0])

def power_usage_database_to_mobile(): #This function is to send historical power usage data to mobile from database (run when mobile call)
    arg = "a"

database_create_table(initialize_database(),DEVICES_ID[0],"light","yeah")