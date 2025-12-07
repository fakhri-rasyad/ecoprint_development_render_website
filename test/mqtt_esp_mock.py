# esp_mqtt_mock.py
import json
import time
import threading
import paho.mqtt.client as mqtt

BROKER = "localhost"
PORT = 1883
ESP_MAC = "AA:BB:CC:DD:EE:FF"

started = False
data_count = 0

# ---------------- MQTT CALLBACKS ----------------
def on_connect(client, userdata, flags, rc):
    print(f"[ESP MOCK] Connected with result code {rc}")
    # Subscribe to commands from the server
    client.subscribe(f"esp/{ESP_MAC}/command")

def on_message(client, userdata, msg):
    global started
    payload = msg.payload.decode()
    print(f"[ESP MOCK] Received: {payload}")

    event = json.loads(payload).get("event")

    if event == "session_start":
        started = True
        print("== Session Started ==")
    elif event in ["session_stop", "session_expired", "esp_timeout"]:
        started = False
        print("== Session Stopped ==")

# ---------------- MQTT CLIENT ----------------
client = mqtt.Client(client_id=f"esp_mock_{ESP_MAC}")
client.on_connect = on_connect
client.on_message = on_message
client.connect(BROKER, PORT, 60)
client.loop_start()

# ---------------- TELEMETRY SENDER ----------------
def send_telemetry():
    global data_count, started
    while True:
        if started:
            event_name = "preparation" if data_count < 15 else "steaming"
            payload = {
                "event": event_name,
                "humidity": 0.0,
                "water_temperature": 0.0,
                "air_temperature": 0.0,
                "water_sufficient": True
            }
            client.publish(f"esp/{ESP_MAC}/telemetry", json.dumps(payload))
            print("[ESP MOCK] Sent telemetry:", payload)
            data_count += 1
        time.sleep(2)

# Run telemetry sender in a separate thread
threading.Thread(target=send_telemetry, daemon=True).start()

# Keep the script running
try:
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    client.loop_stop()
    client.disconnect()
    print("ESP mock stopped.")
