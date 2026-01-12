# IoT-Based Biometric Attendance System

![IoT](https://img.shields.io/badge/IoT-ESP8266-blue)
![OpenCV](https://img.shields.io/badge/CV-Face%20Recognition-green)
![Status](https://img.shields.io/badge/Status-Prototype-yellow)

## 📌 Project Overview
A secure **Smart Attendance System** designed to mitigate identity spoofing in communal or academic environments. This system integrates **Multi-Factor Authentication (MFA)** combining Face Recognition and dynamic QR Codes, synchronized in real-time via cloud protocols.

## 🚀 Key Features
* **Multi-Factor Authentication:** Requires both Face Verification (OpenCV) and QR Code scanning.
* **Real-Time Sync:** Uses **MQTT** protocol for low-latency communication between edge devices and the server.
* **Anti-Spoofing:** Liveness detection algorithms to prevent photo-based bypass attempts.
* **Cloud Dashboard:** Integrated with **Firebase** and **Node-RED** for live attendance monitoring.

## 🛠 Hardware & Tech Stack
* **Microcontroller:** ESP8266 / ESP32
* **Sensors:** Camera Module (for vision input)
* **Software:** Python (OpenCV), C++ (Arduino IDE)
* **Cloud/Connectivity:** MQTT Broker, Firebase Realtime Database, Node-RED

## ⚙️ System Architecture
1.  **Input:** Camera captures user face; Mobile app generates dynamic QR.
2.  **Processing:** Python script verifies face biometrics; ESP8266 verifies QR token.
3.  **Validation:** Both signals must match within a 5-second window.
4.  **Output:** Data sent to Firebase; Access granted (Solenoid Lock triggers).
