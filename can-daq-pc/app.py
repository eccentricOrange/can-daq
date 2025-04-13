"""
Main Application file
-   entry point for the application
-   configure the database
-   run the main application
"""

import sys
from logging import INFO, FileHandler, Formatter, getLogger
from pathlib import Path

import customtkinter

import src.database_functionality
import src.screens

# constants
CURRENT_PATH = Path(__file__).parent
FOLDER_PATH = Path.home() / ".protocol-data-monitor"
FOLDER_PATH.mkdir(exist_ok=True)

# configure logger
LOGGER_LEVEL = INFO

logger_formatter = Formatter(
    fmt="[{asctime}][{process:05}][{name}][{levelname}] {message}",
    style='{'
)
logger_file_handler = FileHandler(
    FOLDER_PATH / 'protocol-data-monitor.log',
    mode='a'
)

def show_error_dialog(title, message):
    """Show error dialog to user"""

    error_window = customtkinter.CTkToplevel()
    error_window.title(title)
    error_window.geometry("400x200")
    
    label = customtkinter.CTkLabel(error_window, text=message, wraplength=350)
    label.pack(pady=20, padx=20)
    
    button = customtkinter.CTkButton(error_window, text="OK", command=error_window.destroy)
    button.pack(pady=20)
    
    error_window.grab_set()  # Make the error window modal

def main():
    try:
        # configure loggers
        logger_file_handler.setFormatter(logger_formatter)

        logger = getLogger(__name__)
        logger.addHandler(logger_file_handler)
        logger.setLevel(LOGGER_LEVEL)

        current_folder = Path(__file__).parent
        logger.debug(f"Current folder: {current_folder}")
        logger.debug(f"ls {current_folder}: {list(current_folder.iterdir())}")
        logger.debug(f"ls {current_folder / 'src'}: {list((current_folder / 'src').iterdir())}")

        src.screens.protocol_config_screen.logger.addHandler(logger_file_handler)
        src.screens.protocol_config_screen.logger.setLevel(LOGGER_LEVEL)

        src.screens.monitoring_screen.logger.addHandler(logger_file_handler)
        src.screens.monitoring_screen.logger.setLevel(LOGGER_LEVEL)

        src.database_functionality.logger.addHandler(logger_file_handler)
        src.database_functionality.logger.setLevel(LOGGER_LEVEL)

        # configure app
        customtkinter.set_appearance_mode("system")
        customtkinter.set_default_color_theme("blue")

        try:
            # Session Management Screen
            app = customtkinter.CTk()
            app.minsize(600, 400)
            app.title("Session Management")
            initial_screen = src.screens.session_management_screen.SessionManagementScreen(
                app,
                data_folder_path=FOLDER_PATH / "sessions",
                schema_path=CURRENT_PATH / "src/schema.sql",
            )
            app.mainloop()

            if not hasattr(initial_screen, 'session_filename'):
                logger.debug("Session management window closed without selection")
                return

            # Protocol Configuration Screen
            app = customtkinter.CTk()
            app.minsize(600, 400)
            app.title("Protocol Configuration")
            session_config_screen = src.screens.protocol_config_screen.ProtocolConfigScreen(app)
            app.mainloop()

            protocol_frame = session_config_screen.protocol_frame_instance
            device = session_config_screen.device_instance
            timing_config = getattr(session_config_screen, 'timing_config', {
                'plot_max_points': 1000,
                'plot_update_interval': 100,
                'database_batch_size': 1000,
                'statistics_batch_size': 250
            })

            try:
                # Initialize database
                logging_database = src.database_functionality.LoggingDatabase(
                    db_path=initial_screen.session_filename,
                    schema_path=CURRENT_PATH / "src/schema.sql",
                )
            except Exception as e:
                logger.error(f"Failed to initialize database: {str(e)}")
                show_error_dialog("Database Error", f"Failed to initialize database:\n{str(e)}")
                return

            # Monitoring Screen
            app = customtkinter.CTk()
            app.minsize(600, 400)
            app.title("Live data monitoring")
            monitoring_screen = src.screens.monitoring_screen.MonitoringScreen(
                master=app,
                protocol_frame=protocol_frame,
                device=device,
                logging_database=logging_database,
                timing_config=timing_config
            )
            app.mainloop()

        except Exception as e:
            logger.error(f"Application error: {str(e)}")
            show_error_dialog("Application Error", f"An error occurred:\n{str(e)}")
            raise

    except Exception as e:
        # Critical error in logger setup
        print(f"Critical error: {str(e)}")
        show_error_dialog("Critical Error", f"A critical error occurred:\n{str(e)}")
        raise

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"Fatal error: {str(e)}")
        sys.exit(1)