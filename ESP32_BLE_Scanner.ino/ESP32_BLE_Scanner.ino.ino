#include <WiFi.h>
#include <PubSubClient.h>
#include <BLEDevice.h>
#include <BLEScan.h>
#include <BLEAdvertisedDevice.h>

// ---- CONFIG ----
const int RSSI_THRESHOLD = -50;
const char* ssid = "iPhone (4)";
const char* password = "Fluffy11";
const char* mqtt_server = "172.20.10.9"; // Pi 400 MQTT broker IP

const char* ROOM_NAME = "Bedroom";
const char* MQTT_TOPIC = "ble/bedroom";

WiFiClient espClient;
PubSubClient client(espClient);
BLEScan* pBLEScan;

int scanTime = 5;

void setup() {
  Serial.begin(115200);

  WiFi.begin(ssid, password);
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
  }

  client.setServer(mqtt_server, 1883);
  while (!client.connected()) {
    client.connect("esp32_frontdoor");
  }

  BLEDevice::init("");
  pBLEScan = BLEDevice::getScan();
  pBLEScan->setActiveScan(true);
}

void loop() {

  if (!client.connected()) {
    client.connect("esp32_bedroom");  // change per device
  }
  client.loop();

  BLEScanResults* foundDevices = pBLEScan->start(scanTime);

  for (int i = 0; i < foundDevices->getCount(); i++) {

    BLEAdvertisedDevice device = foundDevices->getDevice(i);

    int rssi = device.getRSSI();

    // ONLY detect if strong signal (very close)
    if (rssi >= RSSI_THRESHOLD) {

      String mac = device.getAddress().toString().c_str();

      String payload =
        "{\"item\":\"" + mac +
        "\",\"room\":\"" + ROOM_NAME +
        "\",\"rssi\":" + String(rssi) + "}";

      client.publish(MQTT_TOPIC, payload.c_str());

      Serial.println(payload);  // optional debug
    }
  }

  pBLEScan->clearResults();
  delay(2000);
}