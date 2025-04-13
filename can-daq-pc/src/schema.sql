CREATE TABLE IF NOT EXISTS messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp REAL,
    message_id INTEGER,
    length INTEGER,
    raw_data BLOB
);

CREATE TABLE IF NOT EXISTS signals (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp REAL,
    frame_id INTEGER,
    signal_name TEXT,
    value REAL,
    FOREIGN KEY(frame_id) REFERENCES messages(id)
);

-- Add indexes for better insertion and query performance
CREATE INDEX IF NOT EXISTS idx_messages_timestamp_msgid ON messages(timestamp, message_id);
CREATE INDEX IF NOT EXISTS idx_signals_frameid_timestamp ON signals(frame_id, timestamp);
CREATE INDEX IF NOT EXISTS idx_signals_signalname ON signals(signal_name);

