"""
Database functionality for the data logging system
-   initialize the database
-   insert frames into the database
"""

import csv
import logging
import sqlite3
import threading
from pathlib import Path

import src.protocols

SCHEMA_PATH = Path("src/schema.sql")
DB_PATH = Path("data_logging.db")

logger = logging.getLogger(__name__)

class LoggingDatabase:

    def __init__(self, db_path: Path = DB_PATH, schema_path: Path = SCHEMA_PATH):
        self.logger = logger
        try:
            self.db_path = db_path
            self.schema_path = schema_path

            self.create_and_initialize_db()
        except Exception as e:
            self.logger.error(f"Failed to initialize database: {str(e)}")
            raise

    def create_and_initialize_db(self):
        """
        -   create a database at the specified path
        -   initialize the database with the schema provided
        """

        with open(self.schema_path, "r") as schema_file:
            schema = schema_file.read()
        
        with sqlite3.connect(self.db_path) as conn:
            conn.executescript(schema)
            logger.info(f"Database created at {self.db_path}")

    def insert_frames(self, frames: list[src.protocols.template_protocol.TemplateFrame]):
        """
        Insert frames and their signals with proper relational mapping:
        1. Insert messages and get their IDs
        2. Use message IDs to link signals
        3. Perform everything in a single transaction
        """
        with threading.Lock():
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("PRAGMA journal_mode=MEMORY")
                conn.execute("PRAGMA synchronous=OFF")
                cursor = conn.cursor()
                
                try:
                    cursor.execute("BEGIN TRANSACTION")
                    
                    for frame in frames:
                        # Insert message and get its ID
                        cursor.execute(
                            "INSERT INTO messages (timestamp, message_id, length, raw_data) VALUES (?, ?, ?, ?) RETURNING id",
                            (frame.timestamp, frame.message_id, frame.length, frame.raw_data)
                        )
                        message_id = cursor.fetchone()[0]
                        
                        # Insert associated signals using the message ID
                        signal_values = [
                            (frame.timestamp, message_id, signal_name, value)
                            for signal_name, value in frame.interpreted_data.items()
                        ]
                        
                        if signal_values:
                            cursor.executemany(
                                "INSERT INTO signals (timestamp, frame_id, signal_name, value) VALUES (?, ?, ?, ?)",
                                signal_values
                            )
                    
                    conn.commit()
                except sqlite3.Error as e:
                    conn.rollback()
                    logger.error(f"Database error occurred: {e}")
                    raise
                except Exception as e:
                    self.logger.error(f"Failed to insert data: {str(e)}")
                    conn.rollback()
                    raise

    def export_to_csv(self, output_path: Path) -> None:
        """
        -   query the database for all messages and signals
        -   using the relations between messages and signals, create a CSV file
        -   write only the signals to the CSV file using csv library for proper handling
        """

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            cursor.execute(
                """
                SELECT 
                    messages.id,
                    messages.timestamp, 
                    messages.message_id,
                    messages.length,
                    signals.signal_name, 
                    signals.value 
                FROM signals 
                JOIN messages ON signals.frame_id = messages.id
                """
            )

            with open(output_path, 'w', newline='') as csv_file:
                writer = csv.writer(csv_file)
                writer.writerow(['message_index', 'timestamp', 'message_id', 'length', 'signal_name', 'value'])
                writer.writerows(cursor.fetchall())