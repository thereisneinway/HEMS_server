import device_control_and_mq as dc


#Obtain device info instructions
def obtain_light_info(access_endpoint:str, access_id:str, access_key:str, device_id:str):
    response = list(dc.obtain_deviceinfo(dc.connect_to_tuya(access_endpoint,access_id,access_key),device_id).values())
    power_status = response[0][0]['value']
    light_mode = response[0][1]['value']
    brightness_value = response[0][2]['value']
    return power_status, light_mode, brightness_value
def obtain_plug_info(access_endpoint:str, access_id:str, access_key:str, device_id:str):
    response = list(dc.obtain_deviceinfo(dc.connect_to_tuya(access_endpoint,access_id,access_key),device_id).values())
    power_status = response[0][0]['value']
    power_usage = response[0][1]['value']
    return power_status, power_usage


#Send device command insturctions
def set_light(access_endpoint:str, access_id:str, access_key:str, device_id:str, power:bool, brightness:int):
    k = dc.connect_to_tuya(access_endpoint,access_id,access_key)
    response1 = list(dc.power_device(k,device_id,power).values())
    response2 = list(dc.setBrightness_device(k, device_id,brightness).values())
    print(response1)
    print(response2)