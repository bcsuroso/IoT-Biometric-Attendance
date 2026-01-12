#include <ESP8266WiFi.h>
#include <PubSubClient.h>
#include <Servo.h>

// ---------------- PIN ----------------
#define TRIG D5
#define ECHO D7
#define SERVO_PIN D6

// ---------------- WIFI & MQTT ----------------
const char* ssid = "CALVIN-Student-2G";
const char* password = "CITStudentsOnly";   
const char* mqtt_server = "10.252.255.202";

WiFiClient espClient;
PubSubClient client(espClient);
Servo servoMotor;

// ---------------- TOPICS ----------------
#define TOPIC_ULTRA "sensor/ultrasonic"
#define TOPIC_GATE  "gate/servo"

// ---------------- GLOBAL ----------------
long lastSend = 0;

// ---------------- SERVO FUNCTION ----------------
void bukaGerbang() {
  Serial.println("[SERVO] Membuka pintu...");
  servoMotor.write(180);
  delay(3000);

  Serial.println("[SERVO] Menutup pintu...");
  servoMotor.write(0);
}

// ---------------- CALLBACK MQTT ----------------
void callback(char* topic, byte* payload, unsigned int length) {
  String msg = "";
  for (int i = 0; i < length; i++)
    msg += (char)payload[i];

  if (String(topic) == TOPIC_GATE) {
    if (msg == "BUKA") {
      bukaGerbang();
    }
  }
}

// ---------------- RECONNECT MQTT ----------------
void reconnect() {
  while (!client.connected()) {
    if (client.connect("ESP_Absensi01")) {
      client.subscribe(TOPIC_GATE);
    } else {
      delay(500);
    }
  }
}

// ---------------- WIFI ----------------
void setup_wifi() {
  WiFi.begin(ssid, password);
  while (WiFi.status() != WL_CONNECTED) delay(500);
}

// ---------------- ULTRASONIC FUNCTION ----------------
int bacaUltrasonic() {
  digitalWrite(TRIG, LOW);
  delayMicroseconds(2);

  digitalWrite(TRIG, HIGH);
  delayMicroseconds(10);
  digitalWrite(TRIG, LOW);

  long duration = pulseIn(ECHO, HIGH);
  int distance = duration * 0.034 / 2;

  Serial.print("[ULTRASONIC] Jarak: ");
  Serial.print(distance);
  Serial.println(" cm");

  return distance;
}

// ---------------- SETUP ----------------
void setup() {
  Serial.begin(115200);

  pinMode(TRIG, OUTPUT);
  pinMode(ECHO, INPUT);

  servoMotor.attach(SERVO_PIN);
  servoMotor.write(0);

  setup_wifi();

  client.setServer(mqtt_server, 1883);
  client.setCallback(callback);
}

// ---------------- LOOP ----------------
void loop() {
  if (!client.connected()) reconnect();
  client.loop();

  // Kirim jarak ultrasonic tiap 500 ms + print ke serial
  if (millis() - lastSend >= 1000) {
    lastSend = millis();
    int jarak = bacaUltrasonic();

    char buf[10];
    sprintf(buf, "%d", jarak);
    client.publish(TOPIC_ULTRA, buf);
  }
}

//////////////////////////////////////////////////////////////////////////////////

// #include <ESP8266WiFi.h>
// #include <PubSubClient.h>

// // ===== WIFI =====
// const char* ssid = "CALVIN-Student-2G";
// const char* password = "CITStudentsOnly";

// // ===== MQTT =====
// const char* mqtt_server = "10.252.254.106";   // ganti jika perlu
// const int   mqtt_port   = 1883;

// WiFiClient espClient;
// PubSubClient client(espClient);

// unsigned long lastMQTTCheck = 0;

// // ================= SETUP =================
// void setup() {
//   Serial.begin(115200);
//   delay(2000);

//   Serial.println("=== ESP8266 MQTT STATUS DEBUG ===");

//   // WiFi
//   WiFi.begin(ssid, password);
//   Serial.print("[WIFI] Connecting");

//   while (WiFi.status() != WL_CONNECTED) {
//     delay(500);
//     Serial.print(".");
//   }

//   Serial.println();
//   Serial.println("[WIFI] CONNECTED");
//   Serial.print("[WIFI] IP Address: ");
//   Serial.println(WiFi.localIP());

//   // MQTT
//   client.setServer(mqtt_server, mqtt_port);
// }

// // ================= LOOP =================
// void loop() {
//   // cek MQTT tiap 3 detik
//   if (millis() - lastMQTTCheck > 3000) {
//     lastMQTTCheck = millis();

//     if (!client.connected()) {
//       Serial.println("[MQTT] NOT CONNECTED");
//       connectMQTT();
//     } else {
//       Serial.println("[MQTT] CONNECTED");
//     }
//   }

//   client.loop();
// }

// // ================= MQTT CONNECT =================
// void connectMQTT() {
//   Serial.print("[MQTT] Connecting to broker ");
//   Serial.print(mqtt_server);
//   Serial.print(" ... ");

//   if (client.connect("ESP_MQTT_DEBUG")) {
//     Serial.println("SUCCESS");
//   } else {
//     Serial.print("FAILED, rc=");
//     Serial.print(client.state());
//     Serial.println(" (lihat arti kode di bawah)");
//   }
// }
