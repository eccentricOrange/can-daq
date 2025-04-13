#include <Arduino.h>

#define SAMPLING_PERIOD 250  // ms
#define SERIAL_BAUDRATE 115200  // bps

#define NUMBER_OF_SAMPLES 4

void setup() {
    Serial.begin(SERIAL_BAUDRATE);
}

void loop() {
    double data[] = {0.000781256, 2.7263452, 1.61803, 0.57721};
    uint8_t uart_buffer[8];

    for (size_t counter = 0; counter < NUMBER_OF_SAMPLES; counter++) {
        memcpy(uart_buffer, &data[counter], sizeof(double));
        Serial.write(uart_buffer, sizeof(double));
    }

    delay(SAMPLING_PERIOD);
}