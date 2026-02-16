import json
import time
import threading
import paho.mqtt.client as mqtt
import RPi.GPIO as GPIO
from datetime import datetime

# ---------------- CONFIG ----------------
MQTT_BROKER = "localhost"
MQTT_TOPIC = "ble/#"

PIR_PIN = 17
EXIT_TIMEOUT_SECONDS = 20   # How recent an item must be seen to count as "with you"

LAST_SEEN_FILE = "last_seen.json"
LOG_FILE = "log.json"
REGISTERED_ITEMS_FILE = "registered_items.json"
# ----------------------------------------


# ---------------- GPIO SETUP ----------------
GPIO.setmode(GPIO.BCM)
GPIO.setup(PIR_PIN, GPIO.IN)


# ---------------- HELPERS ----------------
def load_json(path):
    try:
        with open(path, "r") as f:
            return json.load(f)
    except:
        return {}


def save_json(path, data):
    with open(path, "w") as f:
        json.dump(data, f, indent=4)


def log_event(entry):
    logs = load_json(LOG_FILE)
    if "events" not in logs:
        logs["events"] = []

    logs["events"].append(entry)
    save_json(LOG_FILE, logs)


# ---------------- MQTT CALLBACK ----------------
def on_message(client, userdata, msg):
    payload = json.loads(msg.payload.decode())

    mac = payload["item"]
    room = payload["room"]
    rssi = payload.get("rssi", None)

    timestamp = datetime.now().isoformat()

    # Load current last seen
    last_seen = load_json(LAST_SEEN_FILE)

    # DO NOT STORE FRONT DOOR AS LAST SEEN
    if room != "Front Door":
        last_seen[mac] = {
            "room": room,
            "timestamp": timestamp,
            "rssi": rssi
        }
        save_json(LAST_SEEN_FILE, last_seen)

    # Still log the event
    log_event({
        "item": mac,
        "room": room,
        "timestamp": timestamp,
        "rssi": rssi
    })


# ---------------- EXIT CHECK LOGIC ----------------
def check_missing_items():
    print(" Motion detected at front door. Checking items...")

    registered = load_json(REGISTERED_ITEMS_FILE)
    last_seen = load_json(LAST_SEEN_FILE)

    now = datetime.now()

    missing_items = []

    for mac, info in registered.items():
        if mac not in last_seen:
            missing_items.append(info["name"])
            continue

        last_time = datetime.fromisoformat(last_seen[mac]["timestamp"])
        seconds_since_seen = (now - last_time).total_seconds()

        if seconds_since_seen > EXIT_TIMEOUT_SECONDS:
            missing_items.append(info["name"])

    if missing_items:
        print("❗ Missing Items:")
        for item in missing_items:
            print(" -", item)
    else:
        print(" All items accounted for.")


# ---------------- PIR CALLBACK ----------------
def pir_callback(channel):
    check_missing_items()


GPIO.add_event_detect(PIR_PIN, GPIO.RISING, callback=pir_callback, bouncetime=3000)


# ---------------- MQTT SETUP ----------------
client = mqtt.Client()
client.on_message = on_message
client.connect(MQTT_BROKER, 1883, 60)
client.subscribe(MQTT_TOPIC)


print(" Frontdoor Tracker Running...")
client.loop_forever()