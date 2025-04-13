class Signal:
    """
    Signal class
    -   one signal corresponds to one data field in a message
    -   contains information about the signal, such as its name, unit, min/max values, scaling, offset, etc.
    -   does not contain the actual data, this more used for configuration
    """
    
    name: str
    unit: str

    min: float | int
    max: float | int
    scaling: float | int
    offset: float | int

    start_position: int
    end_position: int
    length: int
    byte_order: str

    def __init__(
        self,
        name: str = None,
        unit: str = None,
        min: float | int = None,
        max: float | int = None,
        scaling: float | int = None,
        offset: float | int = None,
        start_position: int = None,
        end_position: int = None,
        length: int = None,
        byte_order: str = None,
        datatype: str = None,
    ) -> None:
        self.name = name
        self.unit = unit
        self.min = min
        self.max = max
        self.scaling = scaling
        self.offset = offset
        self.start_position = start_position
        self.end_position = end_position
        self.length = length
        self.byte_order = byte_order
        self.datatype = datatype

    def __str__(self):
        return f"{self.name} ({self.unit}): {self.min} - {self.max} ({self.scaling}, {self.offset})"


class Message:
    """
    Message class
    -   one message corresponds to one frame of data
    -   contains information about the message, such as its ID, name, length, signals, etc.
    -   contains a list of Signal objects
    -   does not contain the actual data, this more used for configuration
    """

    id: int
    name: str
    length: int
    signals: list[Signal]
    byte_order: str

    def __init__(
        self,
        id: int,
        name: str,
        length: int,
        signals: list[Signal],
        byte_order: str = None,
    ) -> None:
        self.id = id
        self.name = name
        self.length = length
        self.signals = signals

        if byte_order:
            self.byte_order = byte_order

    def __str__(self):
        string = f"ID: 0x{self.id:08X}\nName: {self.name}\nLength: {self.length}\n\nSignals:\n"

        for signal in self.signals:
            string += f"\t{signal}\n"

        return string
    

class UniversalMessage:
    """
    Universal Message class
    -   protocol-agnostic representation of a message
    -   contains the decoded message data
    -   this must be interpreted to extract the signal values
    """

    id: int
    length: int
    data: bytes
    timestamp: float

    def __init__(self, data: bytes, timestamp: float, id: int = 0, length: int = 0):
        self.id = id
        self.length = length
        self.data = data
        self.timestamp = timestamp

    def __str__(self):
        return f"ID: 0x{self.id:08X}\nLength: {self.length}\nData: {self.data}\nTimestamp: {self.timestamp}"