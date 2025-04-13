"""
Template Protocol
-   provide Signal and Message classes, to be used as-is
-   provide TemplateProtocol and TemplateFrame classes, to be inherited from
"""

from pathlib import Path
from typing import Any

import src.messages


class TemplateProtocol:
    """
    Template Protocol class
    -   to be inherited from by other protocol classes
    -   provides base methods for configuring the files. other methods are to be implemented by the child class
    """

    specification_format: Any = None
    data_properties: list[src.messages.Message] = []

    def __init__(self, path: Path = None):
        self.specification_path = path

    def set_specification_path(self, path: Path) -> None:
        """
        -   set the path to the protocol specification file
        -   load the specification file and parse it
        """

        self.specification_path = path
        self.load_specification()
        self.get_data_properties()

    def load_specification(self) -> None:
        """
        process the specification file. e.g., using a library function
        """
        ...

    def get_data_properties(self) -> list[src.messages.Message]:
        """
        extract the data properties from the specification file into our own data structure
        """
        ...

    def __str__(self) -> str:
        string = ""

        for message in self.data_properties:
            string += f"{message}"

        return string


class TemplateFrame:
    """
    Template Frame class
    -   to be inherited from by other frame classes
    -   this should only be instantiated once per session. the object should be re-used for every sample/frame
    -   the data reader (e.g. serial port) is part of this class and the main program should be independent of it
    -   acquired data as a UniversalMessage object should be interpreted and stored here
    """

    protocol: TemplateProtocol
    message_id: int = None
    length: int = None
    raw_data: bytes = None
    interpreted_data: dict = {}
    database_id: int = None
    timestamp: float = None
    decoded_message: src.messages.UniversalMessage

    def __init__(self,
        id: int = None,
        length: int = None,
        raw_data: bytes = None,
        interpreted_data: dict = {},
        timestamp: float = None,
        protocol: TemplateProtocol = None
    ):
        self.message_id = id
        self.length = length
        self.raw_data = raw_data
        self.interpreted_data = interpreted_data
        self.timestamp = timestamp
        self.protocol = protocol

    def interpret_frame(self) -> None:
        """
        -   interpret the parsed data into meaningful values
        -   use the Signal and Message classes to interpret the data
        -   store the interpreted data in the `interpreted_data` dictionary
        """
        ...


    def encode_frame(self) -> src.messages.UniversalMessage:
        """
        -   encode the interpreted data into a format that can be transmitted
        -   use the Signal and Message classes to encode the data
        -   return the encoded data
        """
        ...

    def __str__(self) -> str:
        string = f"ID: 0x{self.message_id:08X}\nLength: {self.length}\nRaw Data: {' '.join(map(hex, self.raw_data))}"
        string += f"\nDecoded Data: {self.interpreted_data}"
        return string
