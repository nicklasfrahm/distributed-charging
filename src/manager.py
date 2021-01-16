import argparse
import os
import sys
import json
import paho.mqtt.client as mqtt
from urllib.parse import urlparse

parser = None
args = None
grids = {}


def clear_screen():
    """Clears the whole console screen."""
    os.system("clear")


def print_grid():
    """Prints information about the managed grids."""
    clear_screen()

    seperator = " | "
    column_width = 16
    column_labels = ["Grid ID", "Station count", "Charging current"]
    column_count = len(column_labels)
    print(seperator.join(map(lambda string: string.ljust(column_width), column_labels)))
    print("".ljust(column_count * column_width +
                   (column_count - 1) * len(seperator), "-"))

    for grid in grids:
        data_columns = [grid, len(grids[grid]["stations"]), "%sA" % (
            grids[grid]["charge_current"])]
        print(seperator.join(map(lambda data: str(
            data).ljust(column_width), data_columns)))


def on_grid_reset(client, userdata, msg):
    """Called if a station successfully drove its charging current to zero and is ready to get instructions."""
    grid_id = msg.topic.split("/")[1]
    if grid_id == "":
        return

    # Check if the grid is known.
    if grids.get(grid_id) is None:
        grids[grid_id] = {
            "current_capacity": 60,
            "stations": {}
        }

    # Parse the payload.
    data = json.loads(msg.payload)
    if data is None:
        return

    # Get the station ID from the payload.
    station_id = data.get("station_id")
    if station_id is None or station_id == "":
        return
    station_id = str(station_id)

    grids[grid_id]["stations"][station_id] = True
    station_count = len(grids[grid_id]["stations"])
    grids[grid_id]["charge_current"] = int(
        grids[grid_id]["current_capacity"] / station_count)

    ready = 0
    for key in grids[grid_id]["stations"]:
        if grids[grid_id]["stations"][key] == True:
            ready += 1

    if ready == station_count:
        client.publish(f"grids/{grid_id}/properties", json.dumps({
            "charge_current": grids[grid_id]["charge_current"]
        }), qos=1)

        print_grid()


def on_grid_join(client, userdata, msg):
    """Called if a station joins a grid."""
    grid_id = msg.topic.split("/")[1]
    if grid_id == "":
        return

    # Check if the grid is known.
    if grids.get(grid_id) is None:
        grids[grid_id] = {
            "current_capacity": 60,
            "charge_current": 0,
            "stations": {}
        }

    # Parse the payload.
    data = json.loads(msg.payload)
    if data is None:
        return

    # Get the station ID from the payload.
    station_id = data.get("station_id")
    if station_id is None or station_id == "":
        return
    station_id = str(station_id)

    grids[grid_id]["charge_current"] = 0
    grids[grid_id]["stations"][station_id] = False
    station_count = len(grids[grid_id]["stations"])

    for key in grids[grid_id]["stations"]:
        grids[grid_id]["stations"][key] = False

    client.publish(f"grids/{grid_id}/properties", json.dumps({
        "charge_current": grids[grid_id]["charge_current"]
    }), qos=1)

    print_grid()


def on_grid_leave(client, userdata, msg):
    """Called if a station leaves a grid."""
    grid_id = msg.topic.split("/")[1]
    if grid_id == "":
        return

    # Check if the grid is known.
    if grids.get(grid_id) is None:
        return

    # Parse the payload.
    data = json.loads(msg.payload)
    if data is None:
        return

    # Get the station ID from the payload.
    station_id = data.get("station_id")
    if station_id is None or station_id == "":
        return
    station_id = str(station_id)

    del grids[grid_id]["stations"][station_id]

    if len(grids[grid_id]["stations"]) != 0:
        station_count = len(grids[grid_id]["stations"])
        grids[grid_id]["charge_current"] = int(
            grids[grid_id]["current_capacity"] / station_count)

        client.publish(f"grids/{grid_id}/properties", json.dumps({
            "charge_current": grids[grid_id]["charge_current"]
        }), qos=1)
    else:
        del grids[grid_id]

    print_grid()


def on_connect(client, userdata, flags, rc):
    """The callback for when the client receives a CONNACK response from the server."""
    clear_screen()
    print(f"[INFO] Connected to broker: {args.broker_uri}")
    print(f"[INFO] Waiting for stations to connect ...")

    # Subscribing in on_connect() means that if we lose the connection and
    # reconnect then subscriptions will be renewed.
    client.publish("services/manager",
                   payload=json.dumps({"online": True}), qos=1)
    client.subscribe("grids/+/join", qos=1)
    client.subscribe("grids/+/leave", qos=1)
    client.subscribe("grids/+/reset", qos=1)


def on_disconnect(client, userdata, rc):
    """The callback if the connection to the MQTT broker breaks."""
    clear_screen()
    print(f"[WARN] Disconnected from broker: {args.broker_uri}")


def main():
    """Contains the basic logic."""
    clear_screen()
    print("[INFO] Starting charging manager ...")

    # Create MQTT client.
    client = mqtt.Client()
    client.on_connect = on_connect
    client.on_disconnect = on_disconnect
    client.will_set("services/manager",
                    payload=json.dumps({"online": False}), qos=1)
    client.message_callback_add("grids/+/join", on_grid_join)
    client.message_callback_add("grids/+/leave", on_grid_leave)
    client.message_callback_add("grids/+/reset", on_grid_reset)

    # Parse MQTT broker URL.
    hostname, port = urlparse(args.broker_uri).netloc.split(":")
    client.connect(hostname, int(port), 60)

    # Keep process alive to wait for incoming messages.
    try:
        client.loop_forever()
    except KeyboardInterrupt:
        clear_screen()
        sys.exit()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('broker_uri', type=str,
                        help='The MQTT broker URI to connect to.')
    args = parser.parse_args()
    main()
