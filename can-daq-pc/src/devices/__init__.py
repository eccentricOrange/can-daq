from . import can_daq, can_daq_windows, template_device

device_details = {
    "CAN-DAQ": {
        "module": can_daq,
    },
    "CAN-DAQ (Windows)": {
        "module": can_daq_windows,
    },
}   # dictionary of supported devices