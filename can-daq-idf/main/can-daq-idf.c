#include <driver/gpio.h>
#include <driver/twai.h>
#include <driver/uart.h>
#include <esp_err.h>
#include <freertos/FreeRTOS.h>
#include <stdio.h>
#include <esp_timer.h>

#define CAN_RX_PIN 6
#define CAN_TX_PIN 7
#define STATUS_LED_PIN 5

#define UART0_BAUDRATE 1e6

#define CAN_TIMEOUT_MS 1e3

#define MINIMUM_TRANSMIT_UART_FRAME_SIZE (4 + 1)  // CAN ID + DLC
#define MAXIMUM_TRANSMIT_UART_FRAME_SIZE (MINIMUM_TRANSMIT_UART_FRAME_SIZE + 8)  // CAN ID + DLC + 8 data bytes
#define TRANSMIT_TASK_DELAY_MS 10


/// @brief Configure GPIO pin 5 for the external status LED.
/// @details The LED is initially turned off.
void configure_led() {
    const gpio_config_t io_conf = {
        .mode = GPIO_MODE_OUTPUT,
        .intr_type = GPIO_INTR_DISABLE,
        .pull_down_en = GPIO_PULLDOWN_DISABLE,
        .pull_up_en = GPIO_PULLUP_DISABLE,
        .pin_bit_mask = 1 << STATUS_LED_PIN,
    };

    ESP_ERROR_CHECK(gpio_config(&io_conf));
    gpio_set_level(STATUS_LED_PIN, false);
}

/// @brief Configure the TWAI (CAN) driver with the specified timing configuration.
/// @details The TWAI driver is set to normal mode and accepts all messages.
/// @param t_config The timing configuration for the TWAI driver.
void configure_twai(twai_timing_config_t t_config) {
    const twai_general_config_t g_config = TWAI_GENERAL_CONFIG_DEFAULT(CAN_TX_PIN, CAN_RX_PIN, TWAI_MODE_NORMAL);
    const twai_filter_config_t f_config = TWAI_FILTER_CONFIG_ACCEPT_ALL();  // Accept all messages

    ESP_ERROR_CHECK(twai_driver_install(&g_config, &t_config, &f_config));
    ESP_ERROR_CHECK(twai_start());
}

/// @brief Configure the UART driver for communication with the external device.
/// @details The UART is configured with a baud rate of 1 Mbps, 8 data bits, no parity, and 1 stop bit.
void configure_uart() {
    const uart_config_t uart_config = {
        .baud_rate = UART0_BAUDRATE,
        .data_bits = UART_DATA_8_BITS,
        .parity = UART_PARITY_DISABLE,
        .stop_bits = UART_STOP_BITS_1,
        .flow_ctrl = UART_HW_FLOWCTRL_DISABLE,
    };

    ESP_ERROR_CHECK(uart_param_config(UART_NUM_0, &uart_config));
    ESP_ERROR_CHECK(uart_set_pin(UART_NUM_0, 43, 44, UART_PIN_NO_CHANGE, UART_PIN_NO_CHANGE));
    ESP_ERROR_CHECK(uart_driver_install(UART_NUM_0, 1024, 0, 0, NULL, 0));
}

/// @brief Retrieve the CAN baud rate from the computer running the desktop application and set the TWAI driver accordingly.
/// @return The timing configuration for the TWAI driver based on the specified baud rate.
twai_timing_config_t set_can_data_rate() {
    char data[7];
    int length = 0;

    // we expect to recieve the baud rate in bits per second (e.g., 1000000 for 1 Mbps)
    // since 1000000 (1 Mbps) is the maximum supported baud rate, we can use 7 characters to represent it
    while (length <= 0) {
        length = uart_read_bytes(UART_NUM_0, data, 7, 100);
    }

    ESP_ERROR_CHECK(uart_flush_input(UART_NUM_0));
    ESP_ERROR_CHECK(uart_flush(UART_NUM_0));

    // Convert the data to an integer using a standard library function
    int data_rate = (int)strtol(data, NULL, 10);

    // return the timing configuration based on the specified baud rate
    switch (data_rate) {
        case 1000000:
            return (twai_timing_config_t)TWAI_TIMING_CONFIG_1MBITS();
            break;

        case 800000:
            return (twai_timing_config_t)TWAI_TIMING_CONFIG_800KBITS();
            break;

        case 500000:
            return (twai_timing_config_t)TWAI_TIMING_CONFIG_500KBITS();
            break;

        case 250000:
            return (twai_timing_config_t)TWAI_TIMING_CONFIG_250KBITS();
            break;

        case 125000:
            return (twai_timing_config_t)TWAI_TIMING_CONFIG_125KBITS();
            break;

        case 100000:
            return (twai_timing_config_t)TWAI_TIMING_CONFIG_100KBITS();
            break;

        case 50000:
            return (twai_timing_config_t)TWAI_TIMING_CONFIG_50KBITS();
            break;

        case 25000:
            return (twai_timing_config_t)TWAI_TIMING_CONFIG_25KBITS();
            break;

        default:
            return (twai_timing_config_t)TWAI_TIMING_CONFIG_250KBITS();
            break;
    }
}

/// @brief If there is a message on the CAN bus, read it, package it up, and send it to the computer running the desktop application.
/// @details The message is printed in the format: ID, DLC, data bytes, and hardware timestamp.
/// @details The ID is printed as 4 bytes in little-endian format, followed by the data length code (DLC) and the data bytes.
/// @details The hardware timestamp is appended at the end of the message.
/// @details The transmitted message is comma-separated and terminated with a newline.
/// @details If no message is received within the timeout period, "Nothing" is printed.
/// @details If an error occurs while receiving the message, the error code is printed.
void read_twai_task() {
    twai_message_t message;
    esp_err_t status = twai_receive(&message, pdMS_TO_TICKS(CAN_TIMEOUT_MS));

    if (status == ESP_OK) {
        gpio_set_level(STATUS_LED_PIN, true);

        // Capture hardware timestamp immediately after receiving the message.
        uint64_t hw_timestamp = esp_timer_get_time(); // time in microseconds

        // Print the identifier (4 bytes, little-endian)
        for (size_t i = 0; i < 4; i++) {
            printf("%02X,", (uint8_t)((message.identifier >> (i * 8)) & 0xFF));
        }

        // Print the data length code
        printf("%02X,", (uint8_t)message.data_length_code);

        // Print the raw data bytes
        for (size_t i = 0; i < message.data_length_code; i++) {
            printf("%02X,", (uint8_t)(message.data[i]));
        }

        // Append the hardware timestamp (for example, as 64-bit integer in decimal)
        printf("%llu\n", hw_timestamp);

        gpio_set_level(STATUS_LED_PIN, false);

    } else if (status == ESP_ERR_TIMEOUT) {
        printf("Nothing\n");
    } else {
        printf("Failed to receive message, error code: %04x\n", status);
    }
}

/// @brief Transmit CAN messages received from the computer running the desktop application.
/// @details The message is expected to be in the format: ID, DLC, data bytes.
/// @details The ID is printed as 4 bytes in little-endian format, followed by the data length code (DLC) and the data bytes.
void transmit_can_messages_task() {
    int length_received = 0;
    char uart_data[MAXIMUM_TRANSMIT_UART_FRAME_SIZE];
    twai_message_t message;

    while (true) {

        length_received = uart_read_bytes(UART_NUM_0, uart_data, MAXIMUM_TRANSMIT_UART_FRAME_SIZE, pdMS_TO_TICKS(1000));

        if (length_received >= MINIMUM_TRANSMIT_UART_FRAME_SIZE) {
            // turn on the status LED
            gpio_set_level(STATUS_LED_PIN, true);

            message.identifier = 0;
            message.data_length_code = 0;

            // Parse the identifier
            for (size_t i = 0; i < 4; i++) {
                message.identifier |= (uint32_t)uart_data[i] << (i * 8);
            }

            // Parse the data length code
            message.data_length_code = uart_data[4];

            // Copy the data bytes
            for (size_t i = 0; i < message.data_length_code; i++) {
                message.data[i] = uart_data[i + 5];
            }

            // Transmit the message
            esp_err_t status = twai_transmit(&message, pdMS_TO_TICKS(CAN_TIMEOUT_MS));

            // Turn off the status LED
            gpio_set_level(STATUS_LED_PIN, false);

            uart_flush_input(UART_NUM_0);
            uart_data[0] = '\0';
            length_received = -1;
        } 

    }
    
}

/// @brief Main function of the application.
void app_main(void) {
    uart_set_baudrate(UART_NUM_0, UART0_BAUDRATE);
    configure_led();
    configure_uart();
    twai_timing_config_t t_config = set_can_data_rate();

    configure_twai(t_config);

    xTaskCreate(transmit_can_messages_task, "transmit_can_messages_task", 4096, NULL, 5, NULL);

    while (true) {
        read_twai_task();
    }
}
