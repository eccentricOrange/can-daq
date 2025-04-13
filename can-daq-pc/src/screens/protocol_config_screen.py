"""
Protocol Configuration Screen
-   select and configure the protocol
-   parse the protocol file
-   configure hardware connection settings
"""

from logging import getLogger
from pathlib import Path
from tkinter import filedialog

import customtkinter

import src.devices
import src.messages
import src.protocols

logger = getLogger(__name__)


class ProtocolConfigScreen:
    protocol_instance: src.protocols.template_protocol.TemplateProtocol
    device_instance: src.devices.template_device.Device
    frame_instance: src.protocols.template_protocol.TemplateFrame


    def __init__(self, master: customtkinter.CTk):
        self.ctk_frame = customtkinter.CTkFrame(master=master)
        self.ctk_frame.pack(pady=20, padx=20, fill="both", expand=True)
        self.ctk_frame.grid_columnconfigure(1, weight=1)
        self.ctk_frame.grid_columnconfigure(2, weight=0)
        self.protocol_file_selected = False

        self.create_ui_elements()
    
    def create_ui_elements(self):
        """
        create the UI elements for the session configuration screen
        -   protocol selector
        -   protocol specification file upload
        -   protocol configuration (specific to the selected protocol)
        -   submit button
        """

        # UI organization
        self.ctk_frame.pack(pady=20, padx=20, fill="both", expand=True)
        self.ctk_frame.grid_columnconfigure(1, weight=1)
        self.ctk_frame.grid_columnconfigure(2, weight=0)

        self.left_frame = customtkinter.CTkFrame(master=self.ctk_frame)
        self.left_frame.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")

        self.right_frame = customtkinter.CTkFrame(master=self.ctk_frame)
        self.right_frame.grid(row=0, column=1, padx=10, pady=10, sticky="nsew")

        self.ctk_frame.grid_columnconfigure(0, weight=1)
        self.ctk_frame.grid_columnconfigure(1, weight=1)

        # device
        device_selector_label = customtkinter.CTkLabel(
            master=self.left_frame, text="Select Device", anchor="w"
        )
        device_selector_label.grid(row=0, column=0, pady=(20, 5), padx=10, sticky="w")

        self.device_name = customtkinter.StringVar(value="Select")
        self.device_selector = customtkinter.CTkOptionMenu(
            master=self.left_frame,
            values=list(src.devices.device_details.keys()),
            variable=self.device_name,
            width=200,
        )
        self.device_selector.grid(row=0, column=1, pady=(20, 5), padx=10, sticky="w")
        self.device_selector.configure(command=self.populate_device_options)

        # protocol
        protocol_selector_label = customtkinter.CTkLabel(
            master=self.left_frame, text="Select Protocol", anchor="w"
        )
        protocol_selector_label.grid(row=1, column=0, pady=(20, 5), padx=10, sticky="w")

        self.protocol_name = customtkinter.StringVar(value="Select")
        self.protocol_selector = customtkinter.CTkOptionMenu(
            master=self.left_frame,
            values=list(src.protocols.protocol_details.keys()),
            variable=self.protocol_name,
            width=200,
        )
        self.protocol_selector.grid(row=1, column=1, pady=(20, 5), padx=10, sticky="w")
        self.protocol_selector.configure(command=self.populate_protocol_options)

        # specification file
        self.file_label = customtkinter.CTkLabel(
            master=self.left_frame, text="Upload Protocol File", anchor="w"
        )
        self.file_label.grid(row=2, column=0, pady=(20, 5), padx=10, sticky="w")

        upload_button = customtkinter.CTkButton(
            master=self.left_frame,
            text="Upload",
            command=self.upload_protocol_file,
            width=100,
        )
        upload_button.grid(row=2, column=1, pady=(20, 5), padx=10, sticky="e")

        clear_button = customtkinter.CTkButton(
            master=self.left_frame,
            text="Clear",
            command=self.clear_protocol_file,
            width=100,
        )
        clear_button.grid(row=2, column=2, pady=(20, 5), padx=10, sticky="e")

        self.file_path_label = customtkinter.CTkLabel(
            master=self.left_frame,
            text="No protocol file selected",
            anchor="w",
            wraplength=400,
        )
        self.file_path_label.grid(
            row=3, column=0, columnspan=2, pady=(0, 20), padx=10, sticky="w"
        )

        # Add timing config button before the Submit button
        timing_button = customtkinter.CTkButton(
            master=self.ctk_frame,
            text="Advanced Timing Options",
            command=lambda: self.show_timing_config(),
            width=160,
            fg_color="transparent",  # Makes it a secondary button
            border_width=1,
            text_color=("gray10", "gray90")  # Dark mode compatible colors
        )
        timing_button.grid(row=3, column=0, columnspan=2, pady=(10, 0), padx=10, sticky="ew")

        # Move existing submit button to row 5
        submit_button = customtkinter.CTkButton(
            master=self.ctk_frame,
            text="Continue",
            command=lambda: self.continue_to_monitoring(),
            width=240,
            height=40,
            font=("helvetica", 14, "bold")
        )
        submit_button.grid(row=5, column=0, columnspan=2, pady=(20, 40), padx=10, sticky="ew")

        # Specification output
        self.text_display = customtkinter.CTkLabel(
            master=self.ctk_frame,
            text="",
            anchor="w",
            wraplength=800,
            justify="left"
        )
        self.text_display.grid(row=4, column=0, columnspan=2, pady=(20, 10), padx=10, sticky="nsew")

        self.left_frame.grid_columnconfigure(1, weight=1)
        self.right_frame.grid_columnconfigure(1, weight=1)

    def populate_protocol_options(self, *args):
        """
        provide list of all protocols available for selection
        """

        self.protocol_module = src.protocols.protocol_details[self.protocol_name.get()]["module"]
        self.protocol_instance: src.protocols.template_protocol.TemplateProtocol = self.protocol_module.Protocol()
        

    def populate_device_options(self, *args):
        """
        provide list of all devices available for selection
        """
        tuple(map(lambda x: x.destroy(), self.right_frame.winfo_children()))
        self.device_module = src.devices.device_details[self.device_name.get()]["module"]
        self.device_instance = self.device_module.Device()
        self.device_instance.gui = self
        self.device_instance.configure_gui(self.right_frame)

    def upload_protocol_file(self):
        """
        open file dialog to select protocol specification file
        """
        file_path = filedialog.askopenfilename(filetypes=src.protocols.protocol_details[self.protocol_name.get()]["file_extensions"])
        
        if file_path:
            self.protocol_file_selected = True
            self.file_path_label.configure(text=f"Selected file: {file_path}")
            self.protocol_instance.set_specification_path(Path(file_path))
            self.text_display.configure(text=str(self.protocol_instance))
        else:
            self.protocol_file_selected = False

    def clear_protocol_file(self):
        """
        Clear the selected protocol file
        """
        self.protocol_file_selected = False
        self.file_path_label.configure(text="No protocol file selected")
        if hasattr(self, 'protocol_instance'):
            self.protocol_instance.set_specification_path(None)
            self.text_display.configure(text="")

    def show_timing_config(self):
        """Open timing configuration window"""
        from src.screens.timing_config_screen import TimingConfigScreen
        timing_screen = TimingConfigScreen(self.ctk_frame)
        self.ctk_frame.wait_window(timing_screen.window)
        self.timing_config = timing_screen.get_values()

    def continue_to_monitoring(self):
        """
        parse the connection settings and continue to the monitoring screen
        """
        if self.protocol_name.get() == "Select":
            error_window = customtkinter.CTkToplevel()
            error_window.title("Error")
            error_window.geometry("300x100")
            
            error_label = customtkinter.CTkLabel(
                master=error_window,
                text="Please select a protocol before continuing.",
                wraplength=250
            )
            error_label.pack(pady=10, padx=10)  
            
            return

        if self.device_name.get() == "Select":
            error_window = customtkinter.CTkToplevel()
            error_window.title("Error")
            error_window.geometry("300x100")
            
            error_label = customtkinter.CTkLabel(
                master=error_window,
                text="Please select a device before continuing.",
                wraplength=250
            )
            error_label.pack(pady=10, padx=10)  
            
            return

        if not self.protocol_file_selected:
            error_window = customtkinter.CTkToplevel()
            error_window.title("Error")
            error_window.geometry("300x100")
            
            error_label = customtkinter.CTkLabel(
                master=error_window,
                text="Please select a protocol specification file before continuing.",
                wraplength=250
            )
            error_label.pack(pady=10, padx=10)  
            
            return

        if not hasattr(self, 'timing_config'):
            self.timing_config = {
                'plot_max_points': 1000,
                'plot_update_interval': 100,
                'database_batch_size': 1000,
                'statistics_batch_size': 250
            }

        self.protocol_frame_instance: src.protocols.template_protocol.TemplateFrame = self.protocol_module.Frame()
        self.protocol_frame_instance.protocol = self.protocol_instance
        self.device_instance.device_configuration = self.device_module.DeviceConfiguration()
        self.device_instance.extract_device_configuration()
        self.ctk_frame.master.destroy()