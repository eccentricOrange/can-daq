import customtkinter
import serial

import src.messages
from src.devices import template_device
from src.devices.helpers import EfficientSerial

SERIAL_BAUD_RATES = [
    "50",
    "75",
    "110",
    "134",
    "150",
    "200",
    "300",
    "600",
    "1200",
    "1800",
    "2400",
    "4800",
    "9600",
    "19200",
    "38400",
    "57600",
    "115200",
    "230400",
    "460800",
    "500000",
    "576000",
    "921600",
    "1000000",
    "1152000",
    "1500000",
    "2000000",
    "2500000",
    "3000000",
    "3500000",
    "4000000",
]

CAN_BAUD_RATES = [
    "25000",
    "50000",
    "100000",
    "125000",
    "250000",
    "500000",
    "800000",
    "1000000",
]

class DeviceConfiguration(template_device.DeviceConfiguration):
    serial_port: str
    serial_baud_rate: int
    can_baud_rate: int

    def __init__(
        self,
        serial_port: str = None,
        serial_baud_rate: int = None,
        can_baud_rate: int = None,
    ):
        self.serial_port = serial_port
        self.serial_baud_rate = serial_baud_rate
        self.can_baud_rate = can_baud_rate

    def get_main_speeds(self):
        return {
            "Serial Baud Rate": self.serial_baud_rate,
            "CAN Baud Rate": self.can_baud_rate,
        }
    
    def get_main_ports(self):
        return {
            "Serial Port": self.serial_port,
        }

class Device(template_device.Device):
    device_configuration: DeviceConfiguration
    data_reader: serial.Serial
    initial_hardware_timestamp: int = None
    
    def configure_gui(self, frame: customtkinter.CTkFrame) -> None:
        # serial baud rate
        self.gui.serial_baud_rate_label = customtkinter.CTkLabel(
            master=frame, text="Set Serial Baud Rate", anchor="w"
        )
        self.gui.serial_baud_rate_label.grid(row=0, column=0, pady=5, padx=10, sticky="w")

        self.gui.serial_baud_rate_menu = customtkinter.CTkOptionMenu(
            master=frame, values=SERIAL_BAUD_RATES, width=200
        )
        self.gui.serial_baud_rate_menu.set("1000000")  # Default value
        self.gui.serial_baud_rate_menu.grid(row=0, column=1, pady=5, padx=10, sticky="ew")

        # CAN baud rate
        self.gui.can_baud_rate_label = customtkinter.CTkLabel(
            master=frame, text="Set CAN Baud Rate", anchor="w"
        )
        self.gui.can_baud_rate_label.grid(row=1, column=0, pady=5, padx=10, sticky="w")

        self.gui.can_baud_rate_menu = customtkinter.CTkOptionMenu(
            master=frame, values=CAN_BAUD_RATES, width=200
        )
        self.gui.can_baud_rate_menu.set("1000000")  # Default value
        self.gui.can_baud_rate_menu.grid(row=1, column=1, pady=5, padx=10, sticky="ew")

        # serial port
        self.gui.serial_port_label = customtkinter.CTkLabel(
            master=frame, text="Choose Serial Port", anchor="w"
        )
        self.gui.serial_port_label.grid(row=2, column=0, pady=5, padx=10, sticky="w")

        # Adjust the row numbers for subsequent elements
        self.gui.serial_port_option_menu = customtkinter.CTkOptionMenu(
            master=frame, values=src.protocols.get_serial_ports(), width=200
        )
        self.gui.serial_port_option_menu.grid(row=2, column=1, pady=5, padx=10, sticky="ew")

        self.gui.refresh_button = customtkinter.CTkButton(
            master=frame,
            text="↻",
            command=lambda: src.protocols.refresh_serial_ports(self.gui.serial_port_option_menu),
            fg_color="green",
            width=40,
        )
        self.gui.refresh_button.grid(row=2, column=2, pady=5, padx=(0, 10), sticky="w")

    def initialize_data_reader(self):
        try:
            self.data_reader = EfficientSerial(
                port=self.device_configuration.serial_port,
                baudrate=int(self.device_configuration.serial_baud_rate),
                timeout=1,
            )

            self.data_reader.write(f"{self.device_configuration.can_baud_rate:06}\n".encode())
        except serial.SerialException as e:
            raise ConnectionError(f"Failed to open serial port {self.device_configuration.serial_port}: {str(e)}") from e
        except Exception as e:
            raise RuntimeError(f"Failed to initialize CAN interface: {str(e)}") from e

    def close_data_reader(self) -> None:
        try:
            if hasattr(self, 'data_reader') and self.data_reader.is_open:
                self.data_reader.close()
        except Exception as e:
            raise RuntimeError(f"Failed to close serial port: {str(e)}") from e

    def read_raw_data(self) -> bytes | None:
        if self.data_reader.is_open:
            self.raw_data = self.data_reader.readline()
        else:
            self.raw_data = None
        return self.raw_data

    def parse_raw_data(self, initial_timestamp: float = None) -> src.messages.UniversalMessage:
        # Decode and strip whitespace/newlines
        extracted_string = self.raw_data.strip().decode("utf-8")
        
        # Split the string by commas
        # The expected format: CAN_ID (4 bytes) + DLC + Data bytes + HW timestamp
        # Example: "23,01,00,00,08,BC,07,00,00,07,A6,F7,58,1234567890"
        parts = extracted_string.split(',')
        
        # Remove any empty strings that may result from trailing commas
        parts = [p for p in parts if p]
        
        # Ensure there are at least 5 + DLC fields + 1 for timestamp
        # First 5 fields: 4 for identifier, 1 for DLC
        if len(parts) < 6:
            raise ValueError("Incomplete data frame received")
        
        # Parse identifier from first 4 bytes (little-endian)
        identifier_bytes = [int(parts[i], 16) for i in range(4)]
        message_id = 0
        for i, byte in enumerate(identifier_bytes):
            message_id |= byte << (i * 8)
        
        # Parse data length code (DLC)
        length = int(parts[4], 16)
        
        # Check if we have enough data bytes and one timestamp field
        expected_field_count = 5 + length + 1
        if len(parts) < expected_field_count:
            raise ValueError("Data frame missing expected fields")
        
        # Parse data bytes
        data_start = 5
        data_end = data_start + length
        decoded_data = [int(x, 16) for x in parts[data_start:data_end]]
        
        # Parse hardware timestamp (the last field)
        hardware_timestamp = int(parts[-1]) / 1e6
        
        # Get the initial hardware timestamp
        if not self.initial_hardware_timestamp:
            self.initial_hardware_timestamp = hardware_timestamp

        # Calculate the UNIX timestamp
        unix_timestamp = (hardware_timestamp - self.initial_hardware_timestamp) + initial_timestamp
        
        return src.messages.UniversalMessage(
            id=message_id,
            length=length,
            data=decoded_data,
            timestamp=unix_timestamp,  # Use hardware timestamp here
        )
    

    def transmit_raw_message(self, message):
        bytes_to_transmit = [
            message.id.to_bytes(4, byteorder="little"),
            message.length.to_bytes(1, byteorder="little"),
            message.data,
            '\n'.encode()
        ]

        self.data_reader.write(b''.join(bytes_to_transmit))
    
    
    def extract_device_configuration(self):
        self.device_configuration.serial_baud_rate = int(self.gui.serial_baud_rate_menu.get())
        self.device_configuration.can_baud_rate = int(self.gui.can_baud_rate_menu.get())
        self.device_configuration.serial_port = self.gui.serial_port_option_menu.get()