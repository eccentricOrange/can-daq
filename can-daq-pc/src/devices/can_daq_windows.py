import time

import serial

import src.devices.can_daq as can_daq
from src.devices.helpers import EfficientSerial


class DeviceConfiguration(can_daq.DeviceConfiguration): ...

class Device(can_daq.Device):
    def initialize_data_reader(self):
        try:
            self.data_reader = EfficientSerial(
                port=self.device_configuration.serial_port,
                baudrate=int(self.device_configuration.serial_baud_rate),
                timeout=1,
            )

            time.sleep(0.5)

            self.data_reader.write(f"{self.device_configuration.can_baud_rate:06}\n".encode())
        except serial.SerialException as e:
            raise ConnectionError(f"Failed to open serial port {self.device_configuration.serial_port}: {str(e)}") from e
        except Exception as e:
            raise RuntimeError(f"Failed to initialize CAN interface: {str(e)}") from e