from datetime import timedelta, datetime
import mysql.connector
import time

import numpy as np
import pandas as pd


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


def check_column_main_table(cursor, device: dict, table_name: str):
    column_name, value, data_type = get_prefix(device)
    query = "SHOW COLUMNS FROM " + table_name + " LIKE '" + column_name + "'"
    cursor.execute(query)
    result = cursor.fetchone()
    if result:
        return True
    else:
        add_column(cursor, column_name, data_type, table_name)
        return True


def check_column_energy_table(cursor, energy_table_name: str):
    cursor.execute("SHOW TABLES LIKE '" + energy_table_name + "'")
    result = cursor.fetchone()
    if not result:
        create_table(cursor, energy_table_name)
    query = "SHOW COLUMNS FROM " + energy_table_name + " LIKE '" + "energy" + "'"
    cursor.execute(query)
    result = cursor.fetchone()
    if result:
        return True
    else:
        add_column(cursor, "energy", "int", energy_table_name)
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
        check_column_main_table(cursor, i, table_name)
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
    check_column_energy_table(cursor, energy_table_name)

    one_hour_ago = current_timestamp - timedelta(hours=1)
    query = f"""
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
    cursor.execute(insert_query, (current_timestamp.strftime('%Y-%m-%d %H:00:00'), total_energy_usage))
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
            result = cursor.fetchone()[0]
            if result:
                value[start_time.strftime('%Y-%m-%d %H:00:00')] = int(result)
            else:
                value[start_time.strftime('%Y-%m-%d %H:00:00')] = 0
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
            result = cursor.fetchone()[0]
            if result:
                value[start_time.strftime('%Y-%m-%d')] = int(result)
            else:
                value[start_time.strftime('%Y-%m-%d')] = 0
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
            result = cursor.fetchone()[0]
            if result:
                value[start_time.strftime('%Y-%m-%d')] = int(result)
            else:
                value[start_time.strftime('%Y-%m-%d')] = 0
            end_time = start_time
            start_time = start_time - timedelta(weeks=1)
    elif period == 'thisdaylstweek':
        start_time = current_timestamp - timedelta(days=current_timestamp.weekday() )
        end_time = current_timestamp - timedelta(days=current_timestamp.weekday() + 1)
        query = f"""
                            SELECT SUM(energy)
                            FROM {energy_table_name}
                            WHERE timestamp BETWEEN %s AND %s
                            """
        cursor.execute(query, (start_time, end_time))
        result = cursor.fetchone()[0]
        if result:
            value[start_time.strftime('%Y-%m-%d')] = int(result)
        else:
            value[start_time.strftime('%Y-%m-%d')] = 0
    else:
        raise ValueError("Invalid period. Choose 'hour', 'day', or 'week'.")

    cursor.close()
    MySQL.close()

    return value


# NEW FUNCTION
def query_database_for_calculate_runtime(MySQL_connection_details: dict, current_timestamp: time):
    MySQL = mysql.connector.connect(host=MySQL_connection_details.get("HOST"),
                                    port=MySQL_connection_details.get("PORT"),
                                    database=MySQL_connection_details.get("DATABASE_NAME"),
                                    user=MySQL_connection_details.get("USERNAME"),
                                    password=MySQL_connection_details.get("PASSWORD"),
                                    ssl_ca=MySQL_connection_details.get("CA_path"), connection_timeout=180000)
    table_name = MySQL_connection_details.get("TABLE_NAME")
    cursor = MySQL.cursor(dictionary=True)
    cursor.execute("select database();")
    cursor.fetchone()
    cursor.execute("SHOW TABLES LIKE '" + table_name + "'")
    result = cursor.fetchone()
    if not result:
        raise Exception("Table not found")

    start_time = datetime(current_timestamp.year, current_timestamp.month, current_timestamp.day) - timedelta(days=1)
    end_time = datetime(current_timestamp.year, current_timestamp.month,
                        current_timestamp.day)  # MUST Run after midnight
    # Hard code specific device TESTED WORK!
    query = f"""
            SELECT *
            FROM (
                SELECT *,
                       LAG(light_Shower) OVER (ORDER BY timestamp) AS prev_light_Shower,
                       LAG(light_FR) OVER (ORDER BY timestamp) AS prev_light_FR,
                       LAG(light_FL) OVER (ORDER BY timestamp) AS prev_light_FL,
                       LAG(plug_AC) OVER (ORDER BY timestamp) AS prev_plug_AC,
                       LAG("plug_Recirculation fan") OVER (ORDER BY timestamp) AS "prev_plug_Recirculation fan",
                       LAG("plug_Floor lamp") OVER (ORDER BY timestamp) AS "prev_plug_Floor lamp",
                       LAG("plug_Artificial fan") OVER (ORDER BY timestamp) AS "prev_plug_Artificial fan"

                FROM {table_name}
            ) subquery
            WHERE timestamp BETWEEN '{start_time}' AND '{end_time}'
               AND ((light_Shower != prev_light_Shower)
               OR (light_FR != prev_light_FR)
               OR (light_FL != prev_light_FL)
               OR (plug_AC != prev_plug_AC)
               OR ("plug_Recirculation fan" != "prev_plug_Recirculation fan")
               OR ("plug_Floor lamp" != "prev_plug_Floor lamp")
               OR ("plug_Artificial fan" != "prev_plug_Artificial fan"));
            """
    cursor.execute(query)
    real_runtime_table = cursor.fetchall()
    cursor.close()
    MySQL.close()
    return real_runtime_table

def query_database_for_schedule_prediction(MySQL_connection_details: dict, current_timestamp: time):
    conn = mysql.connector.connect(host=MySQL_connection_details.get("HOST"),
                                   port=MySQL_connection_details.get("PORT"),
                                   database=MySQL_connection_details.get("DATABASE_NAME"),
                                   user=MySQL_connection_details.get("USERNAME"),
                                   password=MySQL_connection_details.get("PASSWORD"),
                                   ssl_ca=MySQL_connection_details.get("CA_path"), connection_timeout=180000)
    cursor = conn.cursor()
    seven_days_ago = (current_timestamp - timedelta(days=7)).replace(hour=0, minute=0, second=0, microsecond=0)
    current_day_midnight = current_timestamp.replace(hour=0, minute=0, second=0, microsecond=0)
    query = f"""
    SELECT * FROM main
    WHERE timestamp >= '{seven_days_ago.strftime('%Y-%m-%d %H:%M:%S')}'
    AND timestamp < '{current_day_midnight.strftime('%Y-%m-%d %H:%M:%S')}'
    ORDER BY timestamp;
    """
    cursor.execute(query)
    rows = cursor.fetchall()
    column_names = cursor.column_names
    df = pd.DataFrame(rows, columns=column_names)

    df['timestamp'] = pd.to_datetime(df['timestamp'])
    df.set_index('timestamp', inplace=True)

    df_resampled = df.resample('10min').first()

    columns_to_drop = ['plug_book', 'total_power', 'cplug_peaky']
    df_resampled.drop(columns=columns_to_drop, inplace=True)

    df_resampled['weekday'] = df_resampled.index.to_series().apply(lambda x: 1 if x.weekday() < 5 else 0)
    df_resampled.reset_index(inplace=True)

    df_resampled.drop(columns=['timestamp'], inplace=True)

    cursor.close()
    conn.close()


    # Processing actual data

    df_resampled['temp_Bedroom temp'] = df_resampled['temp_Bedroom temp'].replace(0, np.nan)
    df_resampled['temp_Outdoor temp'] = df_resampled['temp_Outdoor temp'].replace(0, np.nan)
    df_resampled['light_environment'] = df_resampled['light_environment'].replace(0, np.nan)

    max_temp = 438
    min_temp = 206

    df_resampled['light_environment'] = pd.to_numeric(df_resampled['light_environment'], errors='coerce')

    df_resampled['temp_Bedroom temp'] = (df_resampled['temp_Bedroom temp'] - min_temp) / (max_temp - min_temp)
    df_resampled['temp_Outdoor temp'] = (df_resampled['temp_Outdoor temp'] - min_temp) / (max_temp - min_temp)
    df_resampled['light_environment'] = (df_resampled['light_environment'] - 1) / (3 - 1)

    csv_file_path = 'processed_actual_data_7days.csv'
    df_resampled.to_csv(csv_file_path, index=False)