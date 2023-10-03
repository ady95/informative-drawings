import os
import json
import paho.mqtt.client as mqtt
from portrait_helper import PortraitHelper

import config
# MQTT_TOPIC = "drawgpt"


helper = PortraitHelper()

# subscriber callback
def on_message(client, userdata, message):
    print("message received ", str(message.payload.decode("utf-8")))
    # print("message topic= ", message.topic)
    # print("message qos=", message.qos)
    # print("message retain flag= ", message.retain)
    
    try:
        json_string = str(message.payload.decode("utf-8"))
        json_value = json.loads(json_string)

        ts = json_value["ts"]
        channel = json_value["channel"]
        phone_number = json_value["text"]
        download_url = json_value["download_url"]

        
        helper.run(download_url, phone_number, channel, ts)
    except Exception as ex:
        print(ex)


client1 = mqtt.Client("client1")
client1.connect(config.MQTT.HOST)
client1.subscribe(config.MQTT.TOPIC)
client1.on_message = on_message
client1.loop_forever()