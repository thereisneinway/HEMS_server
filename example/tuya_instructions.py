import device_control_and_mq as dc


#Obtain device info instructions
def obtain_light_info(access_endpoint:str, access_id:str, access_key:str, device_id:str):
    response = list(dc.obtain_deviceinfo(dc.connect_to_tuya(access_endpoint,access_id,access_key),device_id).values())
    power_status = response[0][0]['value']
    light_mode = response[0][1]['value']
    brightness_value = response[0][2]['value']
    colour_value = response[0][3]['value']
    return power_status, light_mode, brightness_value, colour_value
def obtain_plug_info(access_endpoint:str, access_id:str, access_key:str, device_id:str):
    response = list(dc.obtain_deviceinfo(dc.connect_to_tuya(access_endpoint,access_id,access_key),device_id).values())
    power_status = response[0][0]['value']
    power_usage = response[0][1]['value']
    return power_status, power_usage
def obtain_temp_info(access_endpoint:str, access_id:str, access_key:str, device_id:str):
    response = list(dc.obtain_deviceinfo(dc.connect_to_tuya(access_endpoint, access_id, access_key), device_id).values())
    temp = response[0][1]['value']
    return temp
def obtain_lightIntensity_info(access_endpoint:str, access_id:str, access_key:str, device_id:str):
    response = list(dc.obtain_deviceinfo(dc.connect_to_tuya(access_endpoint, access_id, access_key), device_id).values())
    intensity = response[0][1]['value']
    return intensity

#Send device command insturctions
#args example:
'''"CODE": {
        "Power": "switch_led",
        "Mode": "work_mode",
        "Brightness": "bright_value_v2",
        "Colour": "colour_data_v2"
    },
    "STATUS": {
        "Power": True,
        "Mode": "white",
        "Brightness": 1000,
        "Colour": "{\"h\":180,\"s\":1000,\"v\":1000}"
    }'''
def command(access_endpoint:str, access_id:str, access_key:str, args:dict):
    try:
        device_id = args.get("Device_id")
        #Convert to lower level [] that accept by Tuya API
        result = []
        code_dict = args.get("CODE")
        status_dict = args.get("SET")
        for key in code_dict:
            code_value = code_dict[key]
            status_value = status_dict.get(key)
            if status_value is not None:
                result.append({'code': code_value, 'value': status_value})
    except: print("Error in args conversion")
    else:
        response = list(dc.send_command(dc.connect_to_tuya(access_endpoint, access_id, access_key), device_id, result).values())
        print(response)

