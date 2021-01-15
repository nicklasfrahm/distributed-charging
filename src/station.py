#!/usr/bin/python3

import sys
import paho.mqtt.client as mqtt


if len(sys.argv) != 4:
    print("Invalid args, usage is:")
    print("python3 station.py brokerURI gridName stationName")
brokerURI, gridName, stationName = sys.argv[1:]

print("Starting station with following settings:")
print(F"broker: {brokerURI}, grid: {gridName}, station: {stationName}")
