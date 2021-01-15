# Distributed charging

A proof of concept for a distributed charging infrastructure.

# Architecture

The application consists of three components:

- `./src/station.py <brokerURI> <gridName> <stationName>`
- `./src/manager.py <brokerURI>`
- Mosquitto MQTT broker

# Public broker

A public broker can be found at `mqtt://nfrah16.dedyn.io:1883`.

# License

This project is licensed under the term of the [MIT license](./LICENSE.md).
