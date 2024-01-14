import mysql.connector
import time

def database_create_table(MySQL_HOST:str, MySQL_USERNAME:str, MySQL_PASSWORD:str, device_type: str,device_name: str):  # This function is to create table in database representing log of one device (only run when no table found)
    print("create database table: "+ device_name)
    MySQL = mysql.connector.connect(host=MySQL_HOST, database='records', user=MySQL_USERNAME, password=MySQL_PASSWORD,connection_timeout=180000)
    cursor = MySQL.cursor()
    cursor.execute("select database();")
    cursor.fetchone()
    if device_type == "light":
        cursor.execute("SHOW TABLES LIKE '"+device_name+"'")
        result = cursor.fetchone()
        if not result:
            query = "CREATE TABLE "+device_name+" (id varchar(30) NOT NULL, timestamp datetime NOT NULL, power_state bool NOT NULL, light_mode varchar(10) NOT NULL, brightness_level int NOT NULL, color varchar(30) NOT NULL, PRIMARY KEY (timestamp))"
            cursor.execute(query)
            cursor.fetchone()
    elif device_type == "plug":
        cursor.execute("SHOW TABLES LIKE '" + device_name + "'")
        result = cursor.fetchone()
        if not result:
            query = "CREATE TABLE " + device_name + " (id varchar(30) NOT NULL, power_state bool NOT NULL, power_con int NOT NULL, PRIMARY KEY (id))"
            cursor.execute(query)
            cursor.fetchone()
    cursor.close()
    MySQL.close()


def append_to_database_table(MySQL_HOST:str, MySQL_USERNAME:str, MySQL_PASSWORD:str, device:dict, timestamp:time):
    device_name = device.get("Device_name")
    device_type = device.get("Device_type")
    device_id = device.get("Device_id")
    args = device.get("STATUS").values
    print("appending status to database " + device_name, end=' ')
    MySQL = mysql.connector.connect(host=MySQL_HOST, database='records', user=MySQL_USERNAME, password=MySQL_PASSWORD)
    cursor = MySQL.cursor()
    if device_type == "light":
        cursor.execute("SHOW TABLES LIKE '" + device_name + "'")
        result = cursor.fetchone()
        if result:
            query = "INSERT INTO "+device_name+" (id, timestamp, power_state, light_mode, brightness_level, color) VALUES (%s, %s, %s, %s, %s, %s)"
            val = (device_id, timestamp, args)
            cursor.execute(query,val)
            cursor.fetchone()
            print(": inserted at " + timestamp)
            MySQL.commit()
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
            MySQL.commit()
        else:
            database_create_table(device_type, device_name)
    cursor.close()
    MySQL.close()
