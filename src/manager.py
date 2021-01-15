#!/usr/bin/python3
import sys
from enum import Enum

if len(sys.argv) < 2:
  print(f"Usage:\n  ./src/manager.py <brokerURI>")
  exit(1)

brokerURI = sys.argv[1]

print("Starting charging manager ...")
