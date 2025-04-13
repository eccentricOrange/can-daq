# CAN-DAQ User Interface Code
This is the code for the CAN-DAQ User Interface. The code is written in Python and uses the Tkinter library along with matplotlib for the GUI. The code is designed for the CAN-DAQ device to visualize and log CAN bus data.

## Functionality
- Create a GUI window with Tkinter
- Read serial data from the CAN-DAQ device
- Parse and interpret CAN frames as per the DBC file
- Plot the selected parameters in real-time
- Log all the data to an SQLite database

## Data Model

The system uses a carefully designed data model to represent CAN messages and signals at different stages of processing. This model is defined in `messages.py` and forms the backbone of communication between the CAN-DAQ device and the application layer.

### Core Classes

#### Signal Class
Represents a single data point within a CAN message:
- Configuration-only class (doesn't hold actual values)
- Defines properties like name, unit, scaling, offset
- Used to describe how to interpret raw CAN data
- Properties:
  - `name`: Signal identifier (e.g., "EngineSpeed")
  - `unit`: Physical unit (e.g., "rpm")
  - `min/max`: Valid range for the signal
  - `scaling/offset`: For converting raw values (value = raw * scaling + offset)
  - `start_position/length`: Bit-level location in the message
  - `byte_order`: Endianness of the data
  - `datatype`: Data type for interpretation (e.g., "float", "uint16")

#### Message Class
Represents a container for multiple signals:
- Configuration-only class (doesn't hold actual values)
- Contains metadata about the CAN message frame
- Holds a list of Signal objects
- Properties:
  - `id`: Message identifier (e.g., CAN ID)
  - `name`: Human-readable identifier
  - `length`: Size in bytes
  - `signals`: List of Signal objects
  - `byte_order`: Default endianness for the message

#### UniversalMessage Class
The bridge between the CAN-DAQ device and the application:
- Contains actual data (not just configuration)
- Used for transferring data between pipeline stages
- Properties:
  - `id`: Message identifier
  - `length`: Data length in bytes
  - `data`: Raw bytes
  - `timestamp`: When the message was received

### Data Flow Example

Here's how these classes interact in practice:

1. **DBC Configuration**:
   ```python
   # Define available messages and signals from the DBC file
   engine_rpm = Signal(
       name="EngineRPM",
       unit="rpm",
       min=0,
       max=8000,
       scaling=0.1,
       offset=0
   )
   
   engine_data = Message(
       id=0x100,
       name="EngineData",
       length=8,
       signals=[engine_rpm]
   )
   ```

2. **Device Layer**:
   ```python
   # CAN-DAQ device reads raw CAN data and creates UniversalMessage
   raw_bytes = device.read_raw_data()
   message = UniversalMessage(
       id=0x100,
       length=8,
       data=raw_bytes,
       timestamp=time.time()
   )
   ```

3. **Interpretation**:
   ```python
   # Interpret UniversalMessage using DBC configuration
   frame = ProtocolFrame(protocol=can_protocol)
   frame.decoded_message = message
   frame.interpret_frame()
   # frame.interpreted_data = {"EngineRPM": 2500.0}
   ```

### Integration with Database

The system stores both raw and interpreted CAN data:
- Messages table: Stores UniversalMessage data
- Signals table: Stores interpreted values for each signal
- Preserves both raw data for reprocessing and interpreted data for quick access

## Usage

This section provides a quick start guide for end-users. For detailed instructions, please refer to the [manual](/docs/manual/manual.md).

### Using Pre-built Executables (Recommended)

Pre-built executables are available for different operating systems in the Releases section. Simply:
1. Download the appropriate executable for your system
2. Run the executable
3. Follow the application screens (detailed in the manual)

### Running from Source

If you prefer to run from source (mainly for developers), you'll need Python installed:

1.  Create a Python virtual environment:

    ```bash
    python -m venv .venv
    ```

1.  Activate the virtual environment:

    - On Windows:

        ```bash
        .venv\Scripts\activate
        ```

    - On macOS and Linux:

        ```bash
        source .venv/bin/activate
        ```

1.  Install the required packages:

    ```bash
    python -m pip install -r requirements.txt
    ```

1.  Run the application:

    ```bash
    python app.py
    ```

### Application Flow

The application guides you through several screens:

1. Session Management - Create new monitoring sessions or export previous ones
2. DBC Configuration - Select and configure your CAN-DAQ device and DBC file
3. Monitoring Screen - Real-time data visualization and logging

Each screen provides clear options and validation to ensure proper configuration. See the manual for detailed instructions for each screen.
