# MacBook CPU Usage Logger

A Python script that samples CPU usage on a MacBook and publishes the readings
to AWS IoT Core over MQTT with mutual TLS.

## Requirements

- macOS and Python 3
- An AWS IoT Core device certificate, its private key, and the Amazon Root CA
- An AWS IoT policy attached to the active device certificate

## Setup

1. Create and activate a virtual environment, then install the dependencies:

   ```sh
   python3 -m venv .venv
   source .venv/bin/activate
   python -m pip install -r requirements.txt
   ```

2. Place the device certificate, private key, and Amazon Root CA in `certs/`.
   Keep the private key secret; do not commit credentials or certificates.

3. Create a `.env` file in the project directory:

   ```dotenv
   AWS_IOT_ENDPOINT=your-endpoint-ats.iot.your-region.amazonaws.com
   AWS_IOT_CLIENT_ID=your-device-client-id
   AWS_IOT_TOPIC=devices/macbook/cpu
   AWS_IOT_CERT=certs/device.pem.crt
   AWS_IOT_KEY=certs/private.pem.key
   AWS_IOT_CA=certs/AmazonRootCA1.pem
   PUBLISH_INTERVAL=5
   ```

   `AWS_IOT_ENDPOINT` is the IoT data endpoint hostname for your AWS account
   and region (without `https://`). Certificate and key paths are resolved
   relative to the directory where you run the script.

4. In AWS IoT Core, activate the device certificate and attach a policy that
   allows the device to connect using the configured client ID and publish to
   the configured topic. Restrict policy resources to the intended client and
   topic.

## Run

From the project directory, with the virtual environment activated:

```sh
python main.py
```

The script prints each published JSON message. Press `Ctrl+C` to stop it; it
will disconnect from AWS IoT Core.

Each message contains the device ID, device type, metric name, CPU usage
percentage, unit, and a UTC ISO 8601 timestamp. Messages are published with
MQTT QoS 1.

## Troubleshooting

- **Missing configuration / file not found:** Check the required `.env`
  entries and ensure certificate paths point to existing files.
- **Connection closes unexpectedly:** Verify the endpoint, certificate status,
  certificate-to-private-key pairing, attached IoT policy, and client ID. An
  already-connected client using the same client ID can also disconnect this
  client.
- **Enable connection diagnostics:** Set `AWS_IOT_DEBUG=1` in `.env` and rerun
  the script. AWS CRT debug logs are written to standard error.
