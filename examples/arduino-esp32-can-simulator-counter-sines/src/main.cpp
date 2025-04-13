#include <Arduino.h>
#include <math.h>

#define LED_PIN 2

// sine constants
#define AMPLITUDE 127.0
#define FREQUENCY 5             // Hz
#define SAMPLING_FREQUENCY 1482  // Hz

// Serial constants
#define SERIAL_BAUDRATE 1e6

// CAN constants
#define DLC (uint8_t)8
#define CAN_ID (uint32_t)0x123

int16_t value;
uint32_t id = 0;

void wait_for_can_bus_rate() {
    while (Serial.available() <= 6);
    while (Serial.available()) {
        Serial.read();
    }
}

void transmit_once() {
    static bool led_state = LOW;
    static uint8_t uart_buffer[8];

    for (int count = 0; count < 250; ++count) {
        for (int n = 0; n < SAMPLING_FREQUENCY / FREQUENCY; n++) {

            // put the ID into the first 4 bytes of the buffer, little endian
            for (int i = 0; i < 4; i++) {
                uart_buffer[i] = (id >> (i * 8)) & 0xFF;
            }

            // put the value into each of the last 4 bytes of the buffer
            value = (int16_t)(AMPLITUDE * sin(2.0 * PI * FREQUENCY * n / SAMPLING_FREQUENCY));
            value += AMPLITUDE;
            for (int i = 0; i < 4; i++) {
                uart_buffer[i + 4] = (uint8_t)(value);
            }

            // print the identifier
            for (size_t i = 0; i < 4; i++) {
                Serial.printf("%02X,", (uint8_t)((CAN_ID >> (i * 8)) & 0xFF));
            }

            // print the data length code
            Serial.printf("%02X,", (uint8_t)DLC, HEX);

            // print the data
            for (size_t i = 0; i < DLC; i++) {
                Serial.printf("%02X,", uart_buffer[i], HEX);
            }

            // Print a newline to separate messages
            Serial.print("\n");

            led_state = !led_state;
            digitalWrite(LED_PIN, led_state);
            delayMicroseconds(1e6 / SAMPLING_FREQUENCY);
            id++;
        }
    }
}

void setup() {
    Serial.begin(SERIAL_BAUDRATE);
    pinMode(LED_PIN, OUTPUT);
    digitalWrite(LED_PIN, LOW);
	wait_for_can_bus_rate();
    transmit_once();
    digitalWrite(LED_PIN, LOW);
}

void loop() {}