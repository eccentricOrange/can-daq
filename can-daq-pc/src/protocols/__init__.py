"""
List of supported protocols and their details.
-   all protocols inherit from the template_protocol module
-   each protocol has an entry in the `protocol_details` dictionary here
"""

import customtkinter
import serial.tools.list_ports

from . import can_protocol, template_protocol

protocol_details = {
    "CAN": {
        "module": can_protocol,
        "file_extensions": [("DBC Files", "*.dbc")],
    },
}   # dictionary of supported protocols

def get_serial_ports() -> list[str]:
    """
    Helper function to get the list of available serial ports
    """

    ports = serial.tools.list_ports.comports()
    return [port.device for port in ports]

def refresh_serial_ports(serial_port_option_menu: customtkinter.CTkOptionMenu):
    """
    Helper function to refresh the list of available serial ports
    """
    
    serial_port_option_menu.configure(values=get_serial_ports())