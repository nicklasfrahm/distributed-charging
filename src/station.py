import sys
import paho.mqtt.client as mqtt
from urllib.parse import urlparse
import json
from time import sleep
import os

# Global variables
MAX_CHARGE_CURRENT = 32
chargeRate = 0


# Clear screen function for pretty printing
def clear():
    os.system("clear")

# Define callback functions


def on_connect(client, userdata, flags, rc):
    # print("rc: " + str(rc))
    # Subscribe to appropiate topic
    client.subscribe("grids/" + gridName + "/properties")
    client.subscribe("services/manager")

    # Publish initial info
    info = client.publish("grids/" + gridName + "/join",
                          payload=json.dumps({'station_id': stationName}), qos=1)


def on_disconnect(client, userdata, mid):
    global chargeRate
    chargeRate = 0


def on_message(client, obj, msg):
    global chargeRate
    # print(msg.topic + " " + str(msg.qos) + " " + str(msg.payload))

    if "properties" in msg.topic:
        properties = json.loads(msg.payload)

        if properties.get('charge_current') <= MAX_CHARGE_CURRENT:
            chargeRate = properties.get('charge_current')
        else:
            chargeRate = MAX_CHARGE_CURRENT

        if chargeRate == 0:
            client.publish("grids/" + gridName + "/reset",
                           payload=json.dumps({'station_id': stationName}), qos=1)

    if "manager" in msg.topic:
        manager = json.loads(msg.payload)

        if manager.get("online"):
            client.publish("grids/" + gridName + "/join",
                           payload=json.dumps({'station_id': stationName}), qos=1)
        else:
            chargeRate = 0


def on_publish(client, obj, mid):
    # print("mid: " + str(mid))
    pass


def on_subscribe(client, obj, mid, granted_qos):
    # print("Subscribed: " + str(mid) + " " + str(granted_qos))
    pass


def on_log(client, obj, level, string):
    # print(string)
    pass


# Parse command line arguments
if len(sys.argv) != 4:
    print("Invalid args, usage is:")
    print("python3 station.py brokerURI gridName stationName")
brokerURI, gridName, stationName = sys.argv[1:]

hostname, port = urlparse(brokerURI).netloc.split(":")

print("Starting station with following settings:")
print(F"broker: {brokerURI}, grid: {gridName}, station: {stationName}")

client = mqtt.Client(stationName, clean_session=True)

client.on_message = on_message
client.on_connect = on_connect
client.on_disconnect = on_disconnect
client.on_publish = on_publish
client.on_subscribe = on_subscribe
client.on_log = on_log
client.will_set("grids/"+gridName+"/leave",
                payload=json.dumps({'station_id': stationName}), qos=1)

# Connect to broker and wait for connection
client.connect(hostname, int(port))
while(not client.is_connected()):
    client.loop()

while(client.is_connected()):
    currentCharge = 0

    clear()

    while(currentCharge < 100):
        client.loop()
        currentCharge += chargeRate*0.1
        print(
            F"\r\rCharge rate: {chargeRate} Current charge: {currentCharge}", end="")
        sleep(0.1)
