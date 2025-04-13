# CAN-DAQ ESP32 Firmware

This is the firmware for the ESP32 that is used in the CAN-DAQ project.

## Pin-out
Refer to the pin-out for [ESP32-S3 DevKitC 1](https://docs.espressif.com/projects/esp-idf/en/latest/esp32s3/hw-reference/esp32s3/user-guide-devkitc-1.html).

![official pin-out](https://docs.espressif.com/projects/esp-dev-kits/en/latest/esp32s3/_images/ESP32-S3_DevKitC-1_pinlayout_v1.1.jpg)

| ESP Pin | Function | Connected to |
| --- | --- | --- |
| GPIO6 | CAN Rx | MCP2651FD CAN Rx |
| GPIO7 | CAN Tx | MCP2651FD CAN Tx |
| GPIO4 | CAN Standby | MCP2651FD STBY (10k pull-down) |
| GPIO5 | Status | Status LED |
| GPIO46 | Disable debug log | Pull-up resistor (10k to 5V) |

## Output data format
Let us understand the UART/USB data formats used for bidirectional communication between the ESP32 and the computer.

### Receiving CAN messages (ESP32 → Computer)
When the ESP32 receives a CAN message, it sends it to the computer with the following format:

```
23,01,00,00,08,BC,07,00,00,07,A6,F7,58,1687654321000\n
```

All data except the timestamp is sent as hexadecimal values, separated with commas. The frame is terminated with a newline character `'\n'`.

| Byte | Value | Description |
| --- | --- | --- |
| 0 | `23` | Byte 0 of the CAN ID (bits 24-29) |
| 1 | `01` | Byte 1 of the CAN ID (bits 16-23) |
| 2 | `00` | Byte 2 of the CAN ID (bits 8-15) |
| 3 | `00` | Byte 3 of the CAN ID (bits 0-7) |
| 4 | `08` | Data length code (DLC) |
| 5-12 | `BC,07,00,00,07,A6,F7,58` | Data bytes (0-7) |
| 13 | `1687654321000` | Hardware timestamp (microseconds) |
| 14 | `\n` | Newline character |

### Transmitting CAN messages (Computer → ESP32)
To transmit a CAN message, send the following binary data format to the ESP32:

```
[ID0][ID1][ID2][ID3][DLC][Data0..DataN]
```

The data is sent as raw binary values (not as hex strings). For example, to send a message with:
- ID: 0x123 (little-endian)
- DLC: 2
- Data: [0xAB, 0xCD]

Send these 7 bytes: `23 01 00 00 02 AB CD`

| Field | Length | Format | Example |
| --- | --- | --- | --- |
| CAN ID | 4 bytes | Little-endian | `23 01 00 00` for ID 0x123 |
| DLC | 1 byte | Length (0-8) | `02` for 2 data bytes |
| Data | DLC bytes | Raw data | `AB CD` |

## Disable debug log
The ESP32 has a pull-up resistor on GPIO46 to disable the debug log output. We do this to make ensure that our GUI software receives only clean data. See the PCB README for more information.

Additionally, we make the following changes in the `sdkconfig` file, displayed here as diffs from the default. This is done using the `idf.py menuconfig` tool \[[source](https://docs.espressif.com/projects/esp-faq/en/latest/development-environment/debugging.html#how-to-block-debugging-messages-sent-through-uart0-by-default-in-esp32)\].

*  Set `CONFIG_BOOTLOADER_LOG_LEVEL_NONE` to disable log output.

    ```diff
    @@ -387,13 +387,13 @@
    CONFIG_BOOTLOADER_COMPILER_OPTIMIZATION_SIZE=y
    # CONFIG_BOOTLOADER_COMPILER_OPTIMIZATION_DEBUG is not set
    # CONFIG_BOOTLOADER_COMPILER_OPTIMIZATION_PERF is not set
    # CONFIG_BOOTLOADER_COMPILER_OPTIMIZATION_NONE is not set
    -# CONFIG_BOOTLOADER_LOG_LEVEL_NONE is not set
    +CONFIG_BOOTLOADER_LOG_LEVEL_NONE=y
    # CONFIG_BOOTLOADER_LOG_LEVEL_ERROR is not set
    # CONFIG_BOOTLOADER_LOG_LEVEL_WARN is not set
    -# CONFIG_BOOTLOADER_LOG_LEVEL_INFO=y
    +CONFIG_BOOTLOADER_LOG_LEVEL_INFO is not set
    # CONFIG_BOOTLOADER_LOG_LEVEL_DEBUG is not set
    # CONFIG_BOOTLOADER_LOG_LEVEL_VERBOSE is not set
    -CONFIG_BOOTLOADER_LOG_LEVEL=3
    +CONFIG_BOOTLOADER_LOG_LEVEL=0
    ```

*   Turn off Serial log output.

    ```diff
    @@ -1353,20 +1353,17 @@
    CONFIG_HEAP_TRACING_OFF=y
    #
    # Log output
    #
    -# CONFIG_LOG_DEFAULT_LEVEL_NONE is not set
    +CONFIG_LOG_DEFAULT_LEVEL_NONE=y
    # CONFIG_LOG_DEFAULT_LEVEL_ERROR is not set
    # CONFIG_LOG_DEFAULT_LEVEL_WARN is not set
    -CONFIG_LOG_DEFAULT_LEVEL_INFO=y
    +# CONFIG_LOG_DEFAULT_LEVEL_INFO is not set
    # CONFIG_LOG_DEFAULT_LEVEL_DEBUG is not set
    # CONFIG_LOG_DEFAULT_LEVEL_VERBOSE is not set
    -CONFIG_LOG_DEFAULT_LEVEL=3
    +CONFIG_LOG_DEFAULT_LEVEL=0
    CONFIG_LOG_MAXIMUM_EQUALS_DEFAULT=y
    +# CONFIG_LOG_MAXIMUM_LEVEL_ERROR is not set
    +# CONFIG_LOG_MAXIMUM_LEVEL_WARN is not set
    +# CONFIG_LOG_MAXIMUM_LEVEL_INFO is not set
    # CONFIG_LOG_MAXIMUM_LEVEL_DEBUG is not set
    # CONFIG_LOG_MAXIMUM_LEVEL_VERBOSE is not set
    -CONFIG_LOG_MAXIMUM_LEVEL=3
    +CONFIG_LOG_MAXIMUM_LEVEL=0
    # CONFIG_LOG_MASTER_LEVEL is not set
    CONFIG_LOG_COLORS=y
    CONFIG_LOG_TIMESTAMP_SOURCE_RTOS=y
    ```

*   Turn off bootloader logs

    ```diff
    @@ -1981,13 +1978,13 @@
    CONFIG_WIFI_PROV_STA_ALL_CHANNEL_SCAN=y
    # Deprecated options for backward compatibility
    # CONFIG_APP_BUILD_TYPE_ELF_RAM is not set
    # CONFIG_NO_BLOBS is not set
    -# CONFIG_LOG_BOOTLOADER_LEVEL_NONE is not set
    +CONFIG_LOG_BOOTLOADER_LEVEL_NONE=y
    # CONFIG_LOG_BOOTLOADER_LEVEL_ERROR is not set
    # CONFIG_LOG_BOOTLOADER_LEVEL_WARN is not set
    -CONFIG_LOG_BOOTLOADER_LEVEL_INFO=y
    +# CONFIG_LOG_BOOTLOADER_LEVEL_INFO is not set
    # CONFIG_LOG_BOOTLOADER_LEVEL_DEBUG is not set
    # CONFIG_LOG_BOOTLOADER_LEVEL_VERBOSE is not set
    -CONFIG_LOG_BOOTLOADER_LEVEL=3
    +CONFIG_LOG_BOOTLOADER_LEVEL=0
    # CONFIG_APP_ROLLBACK_ENABLE is not set
    # CONFIG_FLASH_ENCRYPTION_ENABLED is not set
    # CONFIG_FLASHMODE_QIO is not set
    ```

