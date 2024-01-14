Verison 1 

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

	- obtain_light_info
	- obtain_plug_info
	- obtain_temp_info
	- obtain_lightintensity_info
	- command: send command to device_control_and_mq
	
database_instructions.py

	- database_create_table : Create database if not existing for the device
	- append_to_database_table : Saving status of device to database

mainfunctions.py

	- command_to_api : send command to tuya_instruction
	- fetch_devices_stat : pulling data of single device from Tuya then save to [Devices]  and call update_device_status_toMobile if change were made (loop)
	- set_device : receiving request from mobile then forward to command_to_api and save to [Devices]
	- update_device_status_toMobile : push devices stat to mobile
	- handle_mobile_client : handling request from mobile (loop)
	- connect_to_mobile : run time
	Thread 1 - Fetching device stat + saving to database + updating mobile
	Thread 2 - Handling mobile request + sending command to Tuya


### Flow of commands: 

device status change (pulling every 2s)
    
    devices -> Tuya API -> json msg -> variables dict -> file
                                                      -> database 
								                      -> app API -> mobile app

command from mobile (on demand)
    
    mobile app -> app API -> json msg -> Tuya API -> devices

request stat from mobile (on demand)
    
    mobile app -> app API ; 
    reply: file -> variables dict -> app API -> mobile app
