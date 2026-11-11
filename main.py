
import os
import json
import time
import signal
import psutil

from datetime import datetime, timezone
from dotenv import load_dotenv

from awscrt import io, mqtt
from awsiot import mqtt_connection_builder


# --------------------------------------------------
# 1. LOAD ENVIRONMENT CONFIGURATION
# --------------------------------------------------

load_dotenv()

ENDPOINT = os.getenv("AWS_IOT_ENDPOINT")
CLIENT_ID = os.getenv("AWS_IOT_CLIENT_ID", "akuddev-macbook")
TOPIC = os.getenv("AWS_IOT_TOPIC", "devices/macbook/cpu")

CERT_PATH = os.getenv("AWS_IOT_CERT")
KEY_PATH = os.getenv("AWS_IOT_KEY")
CA_PATH = os.getenv("AWS_IOT_CA")

INTERVAL = int(os.getenv("PUBLISH_INTERVAL", "5"))

DEVICE_ID = CLIENT_ID

running = True

if os.getenv("AWS_IOT_DEBUG", "").lower() in {"1", "true", "yes"}:
    io.init_logging(io.LogLevel.Debug, "stderr")


# --------------------------------------------------
# 2. VALIDATE CONFIGURATION
# --------------------------------------------------

required = {
    "AWS_IOT_ENDPOINT": ENDPOINT,
    "AWS_IOT_CERT": CERT_PATH,
    "AWS_IOT_KEY": KEY_PATH,
    "AWS_IOT_CA": CA_PATH,
}

for name, value in required.items():
    if not value:
        raise ValueError(f"Missing configuration: {name}")

for path in [CERT_PATH, KEY_PATH, CA_PATH]:
    if not os.path.isfile(path):
        raise FileNotFoundError(f"File not found: {path}")


# --------------------------------------------------
# 3. HANDLE GRACEFUL SHUTDOWN
# --------------------------------------------------

def stop_program(signum, frame):
    global running
    print("\nShutdown requested...")
    running = False


signal.signal(signal.SIGINT, stop_program)
signal.signal(signal.SIGTERM, stop_program)


# --------------------------------------------------
# 4. CONNECT TO AWS IOT CORE
# --------------------------------------------------

print("Connecting to AWS IoT Core...")

mqtt_connection = mqtt_connection_builder.mtls_from_path(
    endpoint=ENDPOINT,
    cert_filepath=CERT_PATH,
    pri_key_filepath=KEY_PATH,
    ca_filepath=CA_PATH,
    client_id=CLIENT_ID,
    clean_session=True,
    keep_alive_secs=30,
)

connect_future = mqtt_connection.connect()
connect_future.result()

print("Successfully connected to AWS IoT Core!")


# --------------------------------------------------
# 5. COLLECT AND PUBLISH CPU METRICS
# --------------------------------------------------

try:
    while running:

        # Read actual MacBook CPU usage
        cpu_usage = psutil.cpu_percent(interval=1)

        # Create IoT telemetry message
        payload = {
            "device_id": DEVICE_ID,
            "device_type": "macbook",
            "metric": "cpu_usage",
            "cpu_usage": cpu_usage,
            "unit": "percent",
            "timestamp": datetime.now(
                timezone.utc
            ).isoformat()
        }

        # Convert Python dictionary into JSON
        message = json.dumps(payload)

        # Publish to AWS IoT Core
        publish_future, _ = mqtt_connection.publish(
            topic=TOPIC,
            payload=message,
            qos=mqtt.QoS.AT_LEAST_ONCE
        )
        publish_future.result()

        print(f"Published: {message}")

        # Wait before sending the next reading
        for _ in range(INTERVAL):
            if not running:
                break
            time.sleep(1)

except Exception as error:
    print(f"Publishing error: {error}")
    raise

finally:

    print("Disconnecting from AWS IoT Core...")

    mqtt_connection.disconnect().result()

    print("Device disconnected.")
