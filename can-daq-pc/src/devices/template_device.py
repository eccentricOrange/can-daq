from typing import Any

import src.messages
import customtkinter

class DeviceConfiguration:
    def get_main_speeds(self) -> dict[str, int]:
        """
        return the main speeds for the device
        """
        ...

    def get_main_ports(self) -> dict[str, int]:
        """
        return the main ports for the device
        """

    def __str__(self) -> str:
        """
        return a string representation of the device configuration
        """
        
        string = "SPEEDS\n"
        
        for key, value in self.get_main_speeds().items():
            string += f"{key}: {value}\n"

        string += "\nPORTS\n"

        for key, value in self.get_main_ports().items():
            string += f"{key}: {value}\n"

        return string

class Device:
    data_reader: Any
    decoded_message: src.messages.UniversalMessage
    raw_data: bytes
    device_configuration: DeviceConfiguration
    gui: Any

    def __init__(self,
        data_reader: Any = None,
        device_configuration: DeviceConfiguration = None,
        gui: Any = None,
    ):
        self.data_reader = data_reader
        self.device_configuration = device_configuration
        self.gui = gui

    def configure_gui(self, frame: customtkinter.CTkFrame) -> None:
        """
        -   create the GUI elements for the protocol configuration
        -   add the elements to the GUI Tkinter frame
        """
        ...
    
    def initialize_data_reader(self) -> None:
        """
        -   initialize the data reader (e.g. serial port) using any required parameters (e.g. baud rate)
        -   open the data reader
        -   send any required configuration data to the device
        """
        ...

    def close_data_reader(self) -> None:
        """
        close the data reader
        """
        ...

    def read_raw_data(self) -> bytes:
        """
        -   read the raw data from the data reader
        -   do not attempt to interpret the data here, keep it in raw bytes
        """
        ...

    def parse_raw_data(self, initial_timestamp: float = None) -> src.messages.UniversalMessage:
        """
        -   parse the raw data into a format that can be interpreted
        -   for example, extract the message ID, length, and data bytes
        -   do not attempt to derive meaning from the data here
        """
        ...

    def transmit_raw_message(self, message: src.messages.UniversalMessage) -> None:
        """
        -   transmit the message to the device
        -   the message should be in the format required by the device
        """
        ...

    def extract_device_configuration(self) -> DeviceConfiguration:
        """
        -   extract the device configuration from the GUI elements
        -   store the configuration in the frame object
        """
        ...

    def __str__(self) -> str:
        """
        return a string representation of the device
        """
        return str(self.device_configuration)