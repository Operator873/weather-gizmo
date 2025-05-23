#!/usr/bin/env python3

import configparser
import time

import influxdb_client
from ambient_api.ambientapi import AmbientAPI
from influxdb_client.client.write_api import SYNCHRONOUS

def fetch_data(config):
    api = AmbientAPI(
        AMBIENT_ENDPOINT="https://rt.ambientweather.net/v1",
        AMBIENT_API_KEY=config["Keys"]["api"],
        AMBIENT_APPLICATION_KEY=config["Keys"]["app_key"],
    )

    devices = api.get_devices()
    device = devices[0]  # Written to allow future expansion

    # Avoid throttle limits on AWN
    time.sleep(1)
    data = device.get_data()
    return data  # Return the first item of the list limited to 1 response


def generate_influx_point(data):
    point = influxdb_client.Point("weather").tag("location", "Home")

    for key, value in data.items():
        if key == "date":
            point.time(data["date"])
        elif isinstance(value, int):
            point.field(key, float(value))
        else:
            point.field(key, value)


    return point


def main(config):
    client = influxdb_client.InfluxDBClient(
        url=config["Influx"]["server"],
        token=config["Influx"]["token"],
        org=config["Influx"]["org"],
    )

    influx = client.write_api(write_options=SYNCHRONOUS)

    data = fetch_data(config)

    for item in data:

        influx.write(
            bucket=config["Influx"]["bucket"],
            org=config["Influx"]["org"],
            record=generate_influx_point(item),
        )

    client.close()


if __name__ == "__main__":
    config = configparser.ConfigParser()
    with open("settings.conf", "r") as f:
        config.read_file(f)
    main(config)
