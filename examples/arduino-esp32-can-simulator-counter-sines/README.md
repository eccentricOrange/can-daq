# Counter and sine simulator for the Arduino framework

This is a simulator for the CAN protocol support in our software. Please understand that no CAN bus is actually used in this scenario; the data is sent over USB to the PC (as it would if a CAN bus was connected to our CAN-DAQ hardware) using a simple microcontroller.


## Key information

| Parameter | Value |
| --- | --- |
| Target | Any Arduino-compatible board which supports `Serial.printf()` |
| Framework | Arduino |
| Toolchain provided | PlatformIO |
| USB/UART baud rate | 1 Mbps |
| Number of samples expected | 74,000 |
| Sampling frequency | 1 kHz |
| CAN baud rate (not used) | 1 Mbps |
| Protocol specification file | [examples/stm32-can-counter-sines/sines-and-counter.dbc](sines-and-counter.dbc) |
| CAN frame ID | 0x123 |
| CAN DLC | 8 bytes |

## Usage
If you use [PlatformIO](https://platformio.org/), simply flash the code from this repository to an ESP32 or other compatible microcontroller. If you are using a different IDE or toolchain, you can find just the firmware at [src/main.cpp](src/main.cpp).

Now, connect the microcontroller to your PC via USB, and launch the debugger software. Use the provided DBC file at the path given above.

Set up the logger software as normal, and Start Monitoring. You should see four sine waves (in phase), and a continuously increasing counter (0 to 74,000). Once the counter completes, the transmission has completed. At this point you must **Stop Monitoring** to save the data, and then you can check the database to see if 74,000 samples were correctly received.