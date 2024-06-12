from datetime import timedelta, datetime
import mysql.connector
import time


# TASK IMPORTANT: CHANGE plug_book to plug_AC, MAP all string value to int (for database and intelligent)

# Log to database at once
def create_table(cursor, table_name: str):
    query = "CREATE TABLE " + table_name + " (timestamp datetime NOT NULL, PRIMARY KEY (timestamp))"
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
    elif device_type == "custom_plug":
        column_name = "cplug_" + device_name
        value = float(device['STATUS'].get('Current'))
        data_type = "float"
        return column_name, value, data_type
    elif device_type == "temp_sensor":
        column_name = "temp_" + device_name
        value = device['STATUS'].get('Temp')
        data_type = "int"
        return column_name, value, data_type
    elif device_type == "motion_sensor":
        column_name = "motion_" + device_name
        value = device['STATUS'].get('Motion')
        if value == "pir":
            value = 1
        else:
            value = 0
        data_type = "int"
        return column_name, value, data_type
    elif device_type == "light_sensor":
        column_name = "light_environment"
        value = device['STATUS'].get('brightness')
        if value == "low":
            value = 1
        elif value == "middle":
            value = 2
        elif value == "high":
            value = 3
        else:
            value = 0
        data_type = "int"
        return column_name, value, data_type
    elif device_type == "door_sensor":
        column_name = "door_" + device_name
        value = device['STATUS'].get('State')
        data_type = "varchar(10)"
        return column_name, value, data_type
    elif device_type == "master_power_meter":
        column_name = "total_power"
        value = device['STATUS'].get('Power_consumption')
        data_type = "int"
        return column_name, value, data_type


def check_column(cursor, device: dict, table_name: str):
    column_name, value, data_type = get_prefix(device)
    query = "SHOW COLUMNS FROM " + table_name + " LIKE '" + column_name + "'"
    cursor.execute(query)
    result = cursor.fetchone()
    if result:
        return True
    else:
        add_column(cursor, column_name, data_type, table_name)
        return True


def add_column(cursor, column_name: str, data_type: str, table_name: str):
    query = f"ALTER TABLE " + table_name + " ADD COLUMN `" + column_name + "` " + data_type + ";"
    cursor.execute(query)
    cursor.fetchone()


def append_to_database(MySQL_connection_details: dict, devices: list, current_timestamp: time):
    MySQL = mysql.connector.connect(host=MySQL_connection_details.get("HOST"),
                                    port=MySQL_connection_details.get("PORT"),
                                    database=MySQL_connection_details.get("DATABASE_NAME"),
                                    user=MySQL_connection_details.get("USERNAME"),
                                    password=MySQL_connection_details.get("PASSWORD"),
                                    ssl_ca=MySQL_connection_details.get("CA_path"), connection_timeout=180000)
    table_name = MySQL_connection_details.get("TABLE_NAME")
    cursor = MySQL.cursor()
    cursor.execute("select database();")
    cursor.fetchone()
    cursor.execute("SHOW TABLES LIKE '" + table_name + "'")
    result = cursor.fetchone()

    if not result:
        create_table(cursor, table_name)
    for i in devices:
        check_column(cursor, i, table_name)
        MySQL.commit()

    # Append to
    columns = []
    values = []
    for i in devices:
        column_name, value, data_type = get_prefix(i)
        columns.append("`" + column_name + "`")
        values.append(value)
    columns.append('timestamp')
    values.append(current_timestamp)

    columns_str = ', '.join(columns)
    placeholders = ', '.join(['%s'] * len(values))
    query = f"INSERT INTO {table_name} ({columns_str}) VALUES ({placeholders})"
    cursor.execute(query, values)

    MySQL.commit()
    cursor.close()
    MySQL.close()


def calculate_energy(MySQL_connection_details: dict, current_timestamp: time):
    MySQL = mysql.connector.connect(host=MySQL_connection_details.get("HOST"),
                                    port=MySQL_connection_details.get("PORT"),
                                    database=MySQL_connection_details.get("DATABASE_NAME"),
                                    user=MySQL_connection_details.get("USERNAME"),
                                    password=MySQL_connection_details.get("PASSWORD"),
                                    ssl_ca=MySQL_connection_details.get("CA_path"), connection_timeout=180000)
    table_name = MySQL_connection_details.get("TABLE_NAME")
    energy_table_name = MySQL_connection_details.get("ENERGY_TABLE_NAME")
    cursor = MySQL.cursor()
    cursor.execute("select database();")
    cursor.fetchone()
    cursor.execute("SHOW TABLES LIKE '" + table_name + "'")
    result = cursor.fetchone()
    if not result:
        raise Exception("Table not found")
    cursor.execute("SHOW TABLES LIKE '" + energy_table_name + "'")
    result = cursor.fetchone()
    if not result:
        create_table(cursor, energy_table_name)

    one_hour_ago = current_timestamp - timedelta(hours=1)
    query = """
    SELECT timestamp, total_power
    FROM {table_name}
    WHERE timestamp BETWEEN %s AND %s
    """
    cursor.execute(query, (one_hour_ago, current_timestamp))
    results = cursor.fetchall()
    total_energy_usage = sum(row[1] for row in results) / 60.0
    insert_query = f"""
    INSERT INTO {energy_table_name} (timestamp, energy)
    VALUES (%s, %s)
    """
    cursor.execute(insert_query, (current_timestamp, total_energy_usage))
    MySQL.commit()
    cursor.close()
    MySQL.close()


def query_energy(MySQL_connection_details: dict, period: str, current_timestamp: time):
    MySQL = mysql.connector.connect(host=MySQL_connection_details.get("HOST"),
                                    port=MySQL_connection_details.get("PORT"),
                                    database=MySQL_connection_details.get("DATABASE_NAME"),
                                    user=MySQL_connection_details.get("USERNAME"),
                                    password=MySQL_connection_details.get("PASSWORD"),
                                    ssl_ca=MySQL_connection_details.get("CA_path"), connection_timeout=180000)
    energy_table_name = MySQL_connection_details.get("ENERGY_TABLE_NAME")
    cursor = MySQL.cursor()
    cursor.execute("select database();")
    cursor.fetchone()
    cursor.execute("SHOW TABLES LIKE '" + energy_table_name + "'")
    result = cursor.fetchone()

    if not result:
        raise Exception("energy table not found")
    value = {}
    if period == 'hour':
        start_time = current_timestamp - timedelta(hours=1)
        end_time = current_timestamp
        for i in range(5):
            query = f"""
                    SELECT SUM(energy)
                    FROM {energy_table_name}
                    WHERE timestamp BETWEEN %s AND %s
                    """
            cursor.execute(query, (start_time, end_time))
            value[datetime.strptime(start_time, '%H:%M').strftime('%H:%M')] = cursor.fetchone()[0]
            end_time = start_time
            start_time = start_time - timedelta(hours=1)
    elif period == 'day':
        start_time = datetime(current_timestamp.year, current_timestamp.month, current_timestamp.day)
        end_time = current_timestamp
        for i in range(5):
            query = f"""
                    SELECT SUM(energy)
                    FROM {energy_table_name}
                    WHERE timestamp BETWEEN %s AND %s
                    """
            cursor.execute(query, (start_time, end_time))
            value[datetime.strptime(start_time, '%d/%m/%Y').strftime('%d/%m/%Y')] = cursor.fetchone()[0]
            end_time = start_time
            start_time = start_time - timedelta(days=1)
    elif period == 'week':
        start_of_week = current_timestamp - timedelta(days=current_timestamp.weekday() + 1)
        start_time = datetime(start_of_week.year, start_of_week.month, start_of_week.day)
        end_time = current_timestamp
        for i in range(5):
            query = f"""
                    SELECT SUM(energy)
                    FROM {energy_table_name}
                    WHERE timestamp BETWEEN %s AND %s
                    """
            cursor.execute(query, (start_time, end_time))
            value[datetime.strptime(start_time, '%d/%m/%Y').strftime('%d/%m/%Y')] = cursor.fetchone()[0]
            end_time = start_time
            start_time = start_time - timedelta(weeks=1)
    else:
        raise ValueError("Invalid period. Choose 'hour', 'day', or 'week'.")

    cursor.close()
    MySQL.close()

    return value

# TODO: test function query_energy, calculate_energy
