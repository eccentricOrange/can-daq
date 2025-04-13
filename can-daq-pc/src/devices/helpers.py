import serial

class EfficientSerial(serial.Serial):
    """
    A subclass of serial.Serial that implements an efficient readline method.
    -   Adapted from https://github.com/pyserial/pyserial/issues/216#issuecomment-369414522
    """
    
    buffer = bytearray()

    def readline(self):
        i = self.buffer.find(b"\n")
        if i >= 0:
            r = self.buffer[:i+1]
            self.buffer = self.buffer[i+1:]
            return r
        while True:
            i = max(1, min(2048, self.in_waiting))
            data = self.read(i)
            i = data.find(b"\n")
            if i >= 0:
                r = self.buffer + data[:i+1]
                self.buffer[0:] = data[i+1:]
                return r
            else:
                self.buffer.extend(data)