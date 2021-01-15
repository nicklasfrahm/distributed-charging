# Distributed charging

A proof of concept for a distributed charging infrastructure.

# Architecture

The application consists of three components:

- `./src/station.py <brokerURI> <gridName> <stationName>`
- `./src/manager.py <brokerURI>`
- Mosquitto MQTT broker

# Public broker

A public broker can be found at `mqtt://nfrah16.dedyn.io:1883`.

# Dependencies

This project provides a requirement.txt file for your convenience. 
Run ```pip install -r requirements.txt``` to install them.

If you need a broker, Mosquitto is an easy to use broker.

# License

This project is licensed under the term of the [MIT license](./LICENSE.md).
