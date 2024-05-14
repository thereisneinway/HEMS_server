import mysql.connector
import time

#Log to database at once (table: main)
def create_table(cursor):
    query = "CREATE TABLE main (timestamp datetime NOT NULL, PRIMARY KEY (timestamp))"
    cursor.execute(query)
    cursor.fetchone()

def get_prefix(device: dict):
    device_type = device['Device_type']
    device_name = device['Device_name']
    if device_type == "light":
        column_name = "light_" + device_name
        value = device['STATUS'].get('Power')
        data_type = "bool"
        return column_name, value, data_type
    elif device_type == "plug":
        column_name = "plug_" + device_name
        value = device['STATUS'].get('Power')
        data_type = "bool"
        return column_name, value, data_type
    elif device_type == "temp_sensor":
        column_name = "temp_" + device_name
        value = device['STATUS'].get('Temp')
        data_type = "int"
        return column_name, value, data_type
    elif device_type == "motion_sensor":
        column_name = "motion_" + device_name
        value = device['STATUS'].get('Motion')
        data_type = "varchar(10)"
        return column_name, value, data_type
    elif device_type == "light_sensor":
        column_name = "light_environment"
        value = device['STATUS'].get('brightness')
        data_type = "varchar(10)"
        return column_name, value, data_type
    elif device_type == "door_sensor":
        column_name = "door_" + device_name
        value = device['STATUS'].get('State')
        data_type = "varchar(10)"
        return column_name, value, data_type
    elif device_type == "master_power_meter":
        column_name = "total_power"
        value = device['STATUS'].get('Power')
        data_type = "int"
        return column_name, value, data_type
def check_column(cursor, device:dict):
    column_name, value, data_type = get_prefix(device)
    query = "SHOW COLUMNS FROM main LIKE '" + column_name + "'"
    cursor.execute(query)
    result = cursor.fetchone()
    if result:
        return True
    else:
        add_column(cursor, column_name,data_type)
        return True
def add_column(cursor, column_name: str, data_type: str):
    query = f"ALTER TABLE main ADD COLUMN `"+column_name+"` "+data_type+";"
    cursor.execute(query)
    cursor.fetchone()
def append_to_database(MySQL_HOST:str, MySQL_USERNAME:str, MySQL_PASSWORD:str, devices:dict, current_timestamp:time):
    MySQL = mysql.connector.connect(host=MySQL_HOST, database='records', user=MySQL_USERNAME, password=MySQL_PASSWORD,connection_timeout=180000)
    cursor = MySQL.cursor()
    cursor.execute("select database();")
    cursor.fetchone()
    cursor.execute("SHOW TABLES LIKE 'main'")
    result = cursor.fetchone()

    if not result :
        create_table(cursor)
    for i in devices:
        check_column(cursor,i)
        MySQL.commit()

    #Append to
    columns = []
    values = []
    for i in devices:
        column_name, value, data_type = get_prefix(i)
        columns.append("`"+column_name+"`")
        values.append(value)
    print(values)
    columns.append('timestamp')
    values.append(current_timestamp)

    columns_str = ', '.join(columns)
    placeholders = ', '.join(['%s'] * len(values))
    query = f"INSERT INTO main ({columns_str}) VALUES ({placeholders})"
    cursor.execute(query, values)

    MySQL.commit()
    cursor.close()
    MySQL.close()
