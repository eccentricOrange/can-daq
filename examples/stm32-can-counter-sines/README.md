# Counter and sine simulator for STM32

This program will generate CAN packets using an STM32F4 microcontroller, and send them onto a CAN bus using a transceiver and a DE-9 connection. Our CAN-DAQ hardware can then tap into this bus, and listen in on the packets. The data is then sent to a PC over USB, where it can be logged and graphed.

## Key information

| Parameter | Value |
| --- | --- |
| Target | STM32F407GV-based microcontroller, with CAN set up using CAN1 |
| Framework | NA |
| Toolchain provided | STM32CubeIDE |
| USB/UART baud rate | 1 Mbps |
| Number of samples expected | 64,430 |
| Sampling frequency | 1 kHz |
| CAN baud rate | 1 Mbps |
| Protocol specification file | [examples/stm32-can-counter-sines/sines-and-counter.dbc](sines-and-counter.dbc) |
| CAN frame ID | 0x123 |
| CAN DLC | 8 bytes |

## Usage
First set up the following circuit, or use our [Brushed DC Motor development board](https://github.com/eccentricOrange/dcm-dev-board):

### Compatible CAN transceivers
| Part | Status | Fastest CAN version | Cross-compatible footprint |
| --- | --- | --- | --- |
| MCP2551 | EOL (end of life) | CAN 2.0 classic CAN | None |
| MCP2561 | EOL (end of life) | CAN 2.0 classic CAN | with MCP2561FD |
| MCP2561FD | Active | CAN FD | with MCP2561 |

We chose the MCP2561.

### CAN bus
| Purpose | MCP2561 | STM32 |
| --- | --- | --- |
| CAN receive | RXD | PB8 (CAN1_RX) |
| CAN transmit | TXD | PB9 (CAN1_TX) |

External connection via DB9 connector or (unsoldered) JST-XH.

### DE9 pin-out
| DE9 | JST | Purpose |
| --- | --- | --- |
| - | 2 | 5 V |
| 3 | 1 | GND |
| 7 | 3 | CANH |
| 2 | 4 | CANL |

### Code
Simply use a recent version of the STM32CubeIDE to open the project, and flash it to your microcontroller. The code will start generating CAN packets as soon as the microcontroller is powered up.

Now, connect this to our CAN-DAQ via a DE-9 cable, and connect the CAN-DAQ to your PC via USB.

Set up the logger software as normal, and Start Monitoring. You should see four sine waves (90 degrees out of phase), and a continuously increasing counter (0 to 64,429). Once the counter completes, the transmission has completed. At this point you must **Stop Monitoring** to save the data, and then you can check the database to see if 64,000 samples were correctly received.