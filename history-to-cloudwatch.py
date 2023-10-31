#!/usr/bin/with-contenv python3

import datetime
import time
import sys
import boto3
import json
import requests
import logging
from os import environ


# Setup logs. Note only logs to stderr will show up in HomeAssistant Log tab
logger = logging.getLogger("history-to-cloudwatch")
logger.setLevel(logging.INFO)
handler = logging.StreamHandler(stream=sys.stderr)
formatter = logging.Formatter("%(asctime)s - %(message)s")
handler.setFormatter(formatter)
logger.addHandler(handler)


# Load username and password from the options.json file, and check we have them
with open("/data/options.json", "r") as options_file:
    options: dict[str, str] = json.loads(options_file.read())
headers = {
    "Authorization": f"Bearer {environ['SUPERVISOR_TOKEN']}",
    "content-type": "application/json",
}
cw = boto3.client('cloudwatch', aws_access_key_id=options["aws-access-key"], aws_secret_access_key=options["aws-secret-key"], region_name=options["aws-region"])

# Load the entities to monitor
entities = options.get("sensors")
if raw_entities := options.get("sensors"):
    entities = raw_entities.split(",")
else:
    raise RuntimeError("No temperature or humidity sensor configured. Please add them in the Configuration tab")

def determine_cloudwatch_unit(unit_of_measurement):
    return {
        "\u00b0C": "None",
        "%": "Percent"
    }.get(unit_of_measurement, "None")

def send_metrics(hours: int = 1):
    start_time = time.time()
    logger.info("Starting metric collection and submission")

    current_time = datetime.datetime.now(datetime.timezone.utc)
    metrics_start = (current_time - datetime.timedelta(hours=hours, minutes=5)).isoformat('T' ,'seconds')
    url = f"http://supervisor/core/api/history/period/{metrics_start}?filter_entity_id={','.join(entities)}"

    response = requests.get(url, headers=headers)

    if not response.ok:
        raise RuntimeError(f"Unable to gather data from Home Assistant: {response.content}")

    metrics = []

    for sensor_data in response.json():
        for metric in sensor_data:
            if metric["state"] in ["unknown", "unavailable"]:
                continue
            timestamp = datetime.datetime.fromisoformat(metric["last_updated"])
            metrics.append({
                "MetricName": metric["attributes"]["device_class"].capitalize(),
                "Dimensions": [
                    {"Name": "Sensor", "Value": metric["attributes"]["friendly_name"].replace("\u2019", "'")},
                    {"Name": "entity_id", "Value": metric["entity_id"]},
                ],
                "Value": float(metric["state"]),
                "Unit": determine_cloudwatch_unit(metric["attributes"]["unit_of_measurement"]),
                "Timestamp": timestamp
            })

    for i in range(0, len(metrics), 1000):
        chunk = metrics[i:i + 1000]
        cw.put_metric_data(Namespace=options["cloudwatch-namespace"], MetricData=chunk)
    logger.info(f"{len(metrics)} metrics detected in the last hour. Sending them to CloudWatch.")
    duration = time.time() - start_time
    logger.info(f"Metric collection completed in {duration:.3f} seconds. {len(metrics)} metrics sent to CloudWatch")


logger.info("Running startup metrics emission")
send_metrics()

logger.info("We will now send metrics to CloudWatch at every full hour.")
while True:
    now = time.localtime()
    seconds_until_next_hour = 3600 - (now.tm_min * 60 + now.tm_sec)
    logger.info(f"It is now {now.tm_hour}:{now.tm_min}:{now.tm_sec}. Will wait {seconds_until_next_hour} seconds to send metrics.")
    time.sleep(seconds_until_next_hour)
    send_metrics()
    # Adding a small sleep to ensure we don't finish too early.
    time.sleep(10)