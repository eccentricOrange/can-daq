# Constant strain data generator

This is a simulator for the UART protocol support in our software. Please understand that no sensors connected over UART are actually used in this scenario; the data is sent over USB to the PC (as it would if a UART sensor was connected), using a simple microcontroller.


## Key information

| Parameter | Value |
| --- | --- |
| Target | Any Arduino-compatible board which supports `Serial.write()` |
| Framework | Arduino |
| Toolchain provided | PlatformIO |
| USB/UART baud rate | 1 Mbps |
| Sampling frequency | 4 hz |
| Data type | Double (8 bytes) per value |
| Number of samples per transmission | 4 |
| Protocol specification file | [examples/arduino-esp32-uart-constant-data/strains.json](strains.json) |


## Usage
If you use [PlatformIO](https://platformio.org/), simply flash the code from this repository to an ESP32 or other compatible microcontroller. If you are using a different IDE or toolchain, you can find just the firmware at [src/main.cpp](src/main.cpp).

Now, connect the microcontroller to your PC via USB, and launch the debugger software. Use the provided DBC file at the path given above.

Set up the logger software as normal, and Start Monitoring. You should see four constant values coming in at 4 Hz. Once you are done, you can **Stop Monitoring** to save the data, and then you can check the database to see if the data was correctly received.