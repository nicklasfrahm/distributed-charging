import sys
import json
import os
import argparse
import paho.mqtt.client as mqtt
from urllib.parse import urlparse
from time import sleep

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

    print("Client disconnected!")


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


def main(args):
    global brokerURI
    global gridName
    global stationName
    brokerURI = args.broker_uri
    gridName = args.grid_id
    stationName = args.station_id

    if brokerURI.count(":") != 2:
        print(f"error: Broker URI invalid and not in format: mqtt://<host>:<post>")
        exit(1)
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
    client.will_set(f"grids/{gridName}/leave",
                    payload=json.dumps({"station_id": stationName}), qos=1)

    # Connect to broker and wait for connection
    client.connect(hostname, int(port))
    try:
        while(not client.is_connected()):
            client.loop()

        while(client.is_connected()):
            currentCharge = 0

            clear()

            while(currentCharge < 100):
                client.loop()
                currentCharge += chargeRate*0.1
                if currentCharge > 100:
                    currentCharge = 100
                print(
                    F"\r\rGrid: {gridName}   Station: {stationName}   Charge rate: {chargeRate}A   Current charge: {int(currentCharge)}%", end="")
                sleep(0.1)

            # End of charge cycle, restart from 0%
            print("\n\nCharging complete!")
            print("\rResuming in 3..", end="")
            client.loop()
            sleep(1)

            print("\rResuming in 2..", end="")
            client.loop()
            sleep(1)

            print("\rResuming in 1..", end="")
            client.loop()
            sleep(1)
    except KeyboardInterrupt:
        clear()
        sys.exit()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('broker_uri', type=str,
                        help='The MQTT broker URI to connect to.')
    parser.add_argument('grid_id', type=str,
                        help='The name of the grid the station is connected to.')
    parser.add_argument('station_id', type=str,
                        help='The name of the station.')
    main(parser.parse_args())
