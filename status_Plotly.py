import os
import glob
import time
import datetime

import json # used to parse config.json
import time # timer functions
import paho.mqtt.client as mqtt


#MQTT Details
broker_address="iot.eclipse.org"
client_id="autobot"
sub_topic="greenhouse/temp"
pub_topic="greenhouse/temp"


os.system('modprobe w1-gpio')
os.system('modprobe w1-therm')

base_dir = '/sys/bus/w1/devices/'
device_file_list = [glob.glob(base_dir + '28*')[0] + '/w1_slave',glob.glob(base_dir + '28*')[1] + '/w1_slave']

script_path = "/home/pi/PiPonics/"
pump_file = script_path + "pump.txt"
drain_file = script_path + "drain.txt"

#Callback function on message receive
def on_message(client,userdata,message):
        print("message received",str(message.payload.decode("utf-8")))
        data = json.loads(str(message.payload.decode("utf-8","ignore")))
	print(data)
        print("message topic=",message.topic)
        print("message qos=",message.qos)
        print("message retain flag=", message.retain)


#callback function on log
def on_log(client, userdata, level,buf):
       print("log: ", buf)

#MQTT init
print("Initalizing MQTT Client instance: " + client_id)
client =  mqtt.Client(client_id)

#Bind function to callback
client.on_message = on_message
client.on_log = on_log

#Connect to broker
print("connecting to broker: " + broker_address)
client.connect(broker_address)

#temperatue raw
def read_temp_raw(device_file_no):
	device_file_current=device_file_list[device_file_no]
	f = open(device_file_current, 'r')
	lines = f.readlines()
	f.close()
	return lines

#temperature
def read_temp(device_file_no):
    lines = read_temp_raw(device_file_no)
    while lines[0].strip()[-3:] != 'YES':
        time.sleep(0.2)
        lines = read_temp_raw(device_file_no)
    equals_pos = lines[1].find('t=')
    if equals_pos != -1:
        temp_string = lines[1][equals_pos+2:]
        temp_c = float(temp_string) / 1000.0
        temp_f = temp_c * 9.0 / 5.0 + 32.0
        return round(temp_f,0)

try:
    client.loop_start()
#subscribe to topic
    print("subscribing to topic " + sub_topic)
    client.subscribe(sub_topic)
    while True:
	timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

	pump_status=0
	drain_status=0
	
	with open(pump_file, "r") as fo:
				fo.seek(0, 0)
				pump_status = fo.read(1)
	fo.closed
	
	with open(drain_file, "r") as fo:
				fo.seek(0, 0)
				drain_status = fo.read(1)
	fo.closed
	
	print ("checking temp and posting")
	print (timestamp + 'Temp 1:' + str(read_temp(0)) + ' Temp 2:' + str(read_temp(1)) + ' Pump:' + str(pump_status) + ' Drain:' + str(drain_status))
        temperature_1 = read_temp(0)
        temperature_2 = read_temp(1)
        list = [timestamp,str(temperature_1)]
	data = json.dumps(list)
        print (str(temperature_1) + str(temperature_2))
        print("Publish to Topic" + pub_topic)
#punblish to topic
        client.publish(pub_topic, data)
        
	print("Sleeping")
	time.sleep(10)

except:
       client.loop_stop()
