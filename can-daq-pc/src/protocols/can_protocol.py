"""
CAN Protocol
-   parse the DBC file
-   configure the CAN hardware connection settings
-   acquire and interpret the CAN frames
"""

import cantools
import serial

import src.messages
import src.protocols
from src.protocols import template_protocol


class Protocol(template_protocol.TemplateProtocol):
    specification_format: cantools.db.Database

    def load_specification(self):
        try:
            self.specification_format = cantools.db.load_file(str(self.specification_path))
        except Exception as e:
            raise ValueError(f"Failed to load DBC file: {str(e)}") from e

    def get_data_properties(self) -> list[src.messages.Message]:
        try:
            self.data_properties = []  # Reset the list before populating

            for message in self.specification_format.messages:
                signals = []
                for signal in message.signals:
                    # Use 0 and 100 as default min/max if not specified
                    min_val = signal.minimum if signal.minimum is not None else 0
                    max_val = signal.maximum if signal.maximum is not None else 100

                    signals.append(
                        src.messages.Signal(
                            name=signal.name,
                            unit=signal.unit,
                            min=min_val,  # Use the default if None
                            max=max_val,  # Use the default if None
                            scaling=signal.scale,
                            offset=signal.offset,
                            start_position=signal.start,
                            length=signal.length,
                            byte_order=signal.byte_order,
                        )
                    )

                self.data_properties.append(
                    src.messages.Message(
                        id=message.frame_id,
                        name=message.name,
                        length=message.length,
                        signals=signals,
                    )
                )

            return self.data_properties
        except Exception as e:
            raise ValueError(f"Failed to parse DBC messages: {str(e)}") from e


class Frame(template_protocol.TemplateFrame):
    protocol: Protocol
    data_reader: serial.Serial
    serial_baud_rate: int
    can_baud_rate: int
    serial_port: str

    def interpret_frame(self) -> None:
        """
        - Interpret the (parsed) CAN frame using the DBC database.
        - If the DBC database does not contain the message, raise a `ValueError`.
        - Return the interpreted CAN frame as a dictionary. If the message is not found, return `None`.
        """

        try:
            self.interpreted_data = self.protocol.specification_format.decode_message(self.decoded_message.id, bytes(self.decoded_message.data))

        except KeyError as e:
            error_message = f"Message not found in DBC file: {self.message_id}"
            raise ValueError(error_message) from e
        
        else:
            self.message_id = self.decoded_message.id
            self.length = self.decoded_message.length
            self.timestamp = self.decoded_message.timestamp


    def encode_frame(self) -> src.messages.UniversalMessage:
        """
        -   encode the interpreted data into a format that can be transmitted
        """

        if not self.timestamp:
            self.timestamp = 0

        data_as_bytes = self.protocol.specification_format.encode_message(self.message_id, self.interpreted_data)
        self.decoded_message = src.messages.UniversalMessage(self.message_id, self.length, data_as_bytes, self.timestamp)
        return self.decoded_message
        

def test():
    TEST_DATA = bytes((
        0x35,
        0x30,
        0x2c,
        0x30,
        0x31,
        0x2c,
        0x30,
        0x30,
        0x2c,
        0x30,
        0x30,
        0x2c,
        0x30,
        0x38,
        0x2c,
        0x45,
        0x38,
        0x2c,
        0x30,
        0x33,
        0x2c,
        0x30,
        0x30,
        0x2c,
        0x30,
        0x30,
        0x2c,
        0x30,
        0x30,
        0x2c,
        0x30,
        0x30,
        0x2c,
        0x30,
        0x30,
        0x2c,
        0x30,
        0x30,
        0x2c,
        0xd,
        0xa,
    ))
    can_protocol = Protocol("../examples/stm32-can-counter-sines/sines-and-counter.dbc")
    can_protocol.load_specification()
    can_protocol.get_data_properties()
    print(can_protocol)

    frame = Frame(can_protocol, serial.Serial())
    frame.raw_data = TEST_DATA
    frame.parse_raw_data()
    frame.interpret_frame()
    print(frame)


if __name__ == "__main__":
    test()
