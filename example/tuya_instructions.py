import device_control_and_mq as dc

def command(access_endpoint: str, access_id: str, access_key: str, args: dict):
    try:
        device_id = args.get("Device_id")
        result = []
        code_dict = args.get("CODE")
        status_dict = args.get("SET")
        for key in code_dict:
            code_value = code_dict[key]
            status_value = status_dict.get(key)
            if status_value is not None:
                result.append({'code': code_value, 'value': status_value})
    except Exception as e:
        print("Error in args conversion: ",e)
    else:
        list(dc.send_command(dc.connect_to_tuya(access_endpoint, access_id, access_key), device_id, result).values())


def request(access_endpoint: str, access_id: str, access_key: str, args: dict):
    response = list(
        dc.obtain_deviceinfo(dc.connect_to_tuya(access_endpoint, access_id, access_key),
                             args.get("Device_id")).values())
    code_dict = args.get("CODE")
    status_dict = args.get("STATUS")
    for i in response[0]:
        for key1 in code_dict:
            if code_dict[key1] == i['code']:
                for key2 in status_dict:
                    if key1 == key2:
                        status_dict[key1] = i['value']


def verify_instruction(access_endpoint: str, access_id: str, access_key: str, device_id: str, args: dict):
    response = list(
        dc.obtain_instruction(dc.connect_to_tuya(access_endpoint, access_id, access_key), device_id).values())
    print(response[0]['functions'])
    code_dict = args.get("CODE")
    k = 0
    for i in response[0]['functions']:
        for key in code_dict:
            if code_dict[key] == i['code']:
                k += 1
    if len(code_dict) < k:
        return "Functions invalid"
    else:
        return "Functions valid"


def list_function(access_endpoint: str, access_id: str, access_key: str, device_id: str):
    response = \
        list(dc.obtain_instruction(dc.connect_to_tuya(access_endpoint, access_id, access_key), device_id).values())[0][
            'functions']
    return response

