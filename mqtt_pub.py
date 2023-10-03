import json
import paho.mqtt.client as mqtt

MQTT_TOPIC = "drawgpt"
# FILE_PATH = r"E:\GIT_AI\informative-drawings\examples\1\ady95_1.jpg"
FILE_URL = "https://files.slack.com/files-pri/T05TH4T3WMD-F05TN9F0C07/download/_________2.png"

json_value = json.dumps({
        "ts": "1695832761.355159",
        "text": "01090014461",
        "channel": "C05TRJEUPF0",
        "download_url": "https://files.slack.com/files-pri/T05TH4T3WMD-F05TS025GHM/download/_______crop.jpg",
    }, ensure_ascii=False)

mqttc = mqtt.Client("python_pub") # puclisher 이름
mqttc.connect("192.168.10.36", 1883)
mqttc.publish(MQTT_TOPIC, json_value) # topic, message