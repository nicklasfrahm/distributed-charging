import argparse
import json
import paho.mqtt.client as mqtt

from urllib.parse import urlparse

parser = argparse.ArgumentParser()
parser.add_argument('broker_uri', type=str, help='The MQTT broker URI to connect to.')

grids = {}
args = None

# Called if a station joins a grid.
def on_grid_join(client, userdata, msg):
  grid_id = msg.topic.split("/")[1]
  if grid_id == "":
    return

  # Check if the grid is known.
  if grids.get(grid_id) is None:
    grids[grid_id] = {
      "current_capacity": int(60),
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
  charge_current = int(grids[grid_id]["current_capacity"] / station_count)

  client.publish(f"grids/{grid_id}/properties", json.dumps({
    "charge_current": charge_current
  }), qos=1)

  print(f"[GRID] ID: {grid_id}\tStations: {station_count}\tCurrent: {charge_current}A")

# Called if a station leaves a grid.
def on_grid_leave(client, userdata, msg):
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
    charge_current = int(grids[grid_id]["current_capacity"] / station_count)

    client.publish(f"grids/{grid_id}/properties", json.dumps({
      "charge_current": charge_current
    }), qos=1)

    print(f"[GRID] ID: {grid_id}\tStations: {station_count}\tCurrent: {charge_current}A")
  else:
    del grids[grid_id]

# The callback for when the client receives a CONNACK response from the server.
def on_connect(client, userdata, flags, rc):
  print(f"[INFO] Connected to broker: {args.broker_uri}")

  # Subscribing in on_connect() means that if we lose the connection and
  # reconnect then subscriptions will be renewed.
  client.subscribe("grids/+/join", qos=1)
  client.subscribe("grids/+/leave", qos=1)

def main():
  print("[INFO] Starting charging manager ...")

  # Create MQTT client.
  client = mqtt.Client()
  client.on_connect = on_connect
  client.message_callback_add("grids/+/join", on_grid_join)
  client.message_callback_add("grids/+/leave", on_grid_leave)

  # Parse MQTT broker URL.
  hostname, port = urlparse(args.broker_uri).netloc.split(":")
  client.connect(hostname, int(port), 60)

  # Keep process alive to wait for incoming messages.
  client.loop_forever()

if __name__ == "__main__":
  args = parser.parse_args()
  main()
