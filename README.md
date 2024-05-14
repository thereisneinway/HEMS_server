Verison 5.0

### Class level:

    -->  device_control_and_mq     : Command and interpret Tuya API replies
        -->  tuya_instructions     : Handle different type of device obtaining status , Interpret command
        -->  database_instructions : Handle request to database
            -->  mainfunctions.py  : Runtime 

### Function:
device_control_and_mq.py

	- connect_to_tuya : initialize connection
	- obtain_deviceinfo : obtain every parameters of device
	- obtain_instruction : obtain instruction for command of device
	- send_command : send command to device

tuya_instruction.py

	- command : handling command for sending to smart device
	- request : update a device stat to array DEVICES
	- verify_instruction : check if instruction is valid (to be used for adding device)
	- list_function : get list control functions from smart device (to be used of adding device)
	
database_instructions.py

	- create_table : Create table "main" (run by append_to_database)
	- get_prefix : Process device type and return column_name, value, data_type (run by check_column and append_to_database)
    - check_column : Check if column exist and add if not (run by append_to_database)
    - add_column : Add column according to column_name and data_type (run by check_column)
    - append_to_database : Check if table and column exist and append all devices stat to a row)

mainfunctions.py

	- save_devices_to_file : Save device stats from dict to file
	- load_devices_from_file : 	Load device stats from file to dict
    - diff_devices : Compare if devices stats in dict and file is same [True/False]
	- save_automation_to_file : Save automations from dict to file
	- load_automation_from_file : Load automations from file to dict
	- command_to_api : Pass command to be sent to device to tuya instruction (call from handle_mobile_client, manage_automation)
    - add_automation : Add automation (call from handle_mobile_client)
	- remove_automation : Remove automation (call from handle_mobile_client)
	- push_automation_info_to_mobile : Send automation list to mobile (call from handle_mobile_client)
    
    - manage_automation : Periodically check automation and run (Thread)
	- fetch_devices_stat : Fetch device stat one by one from tuya (Thread)
	- update_device_to_mobile : Push device stat one by one to mobile and save to file if diff(Thread-connect_to_mobile)
    - handle_mobile_client : Handle any commands from mobile (Thread-connect_to_mobile)
    - connect_to_mobile : Initiate socket connection from mobile (Thread)
	- database_manage : Append device stats to database (Thread)
    - AI : [To be implement]

Thread list in mainfunctions.py

	Thread 1 - Handling connection from mobile
    Thread 2 - Updating device stats to mobile, save device stats to file if changes found
    Thread 3 - Handling message command from mobile
    Thread 4 - Automation checking and run
    Thread 5 - Fetching device stats from tuya
    Thread 6 - Append device stats to database
    Thread main - Initialize and do no shit after that


### Flow of commands: 

device status change (pulling every 2s by Thread 5)
    
    devices -> Tuya API -> json msg -> variables dict 

automation flow (checking every 5s by Thread 4)

    file -> fn: manage_automation() -> json msg -> Tuya API -> devices

command from mobile (on demand by Thread 3)
    
    mobile app -> app API -> json msg -> Tuya API -> devices
        (or)   -> fn: push_automation_info_to_mobile() -> mobile app

updating devices stats mobile (on demand by Thread 2)
    
    variables dict -> app API -> mobile app
          (and)    -> file

appending devices stats to database (pushing every 2s by Thread 6)

    variables dict -> fn: append_to_database() -> MySQL server