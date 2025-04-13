"""
Session Management Screen
-   create new logging sessions
-   search and export existing sessions
"""

import logging
from datetime import datetime
from pathlib import Path
from tkinter import filedialog

import customtkinter
from tkcalendar import DateEntry

from src.database_functionality import LoggingDatabase

logger = logging.getLogger(__name__)

SCHEMA_PATH = Path("src/schema.sql")

class SessionManagementScreen:
    def __init__(self, master: customtkinter.CTk, data_folder_path: Path, schema_path: Path = SCHEMA_PATH):
        self.data_folder_path = data_folder_path
        self.data_folder_path.mkdir(parents=True, exist_ok=True)  # Ensure folder exists
        self.schema_path = schema_path
        self.filtered_sessions = []  # Store filtered session list
        
        self.master = master
        self.ctk_frame = customtkinter.CTkFrame(master=master)
        self.ctk_frame.pack(pady=20, padx=20, fill="both", expand=True)
        
        # Configure the main frame's grid
        self.ctk_frame.grid_columnconfigure(0, weight=1)
        self.ctk_frame.grid_rowconfigure(0, weight=1)
        
        self.create_ui_elements()
        self.current_view = None
        self.show_main_menu()

        # Add new instance variables to track UI elements
        self.main_menu_elements = []
        self.new_session_elements = []
        self.load_session_elements = []

    def create_ui_elements(self):
        # Create the frames
        self.main_frame = customtkinter.CTkFrame(master=self.ctk_frame)
        self.new_session_frame = customtkinter.CTkFrame(master=self.ctk_frame)
        self.load_session_frame = customtkinter.CTkFrame(master=self.ctk_frame)
        
        # Configure each frame's grid
        for frame in [self.main_frame, self.new_session_frame, self.load_session_frame]:
            frame.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
            frame.grid_columnconfigure(0, weight=1)
            frame.grid_rowconfigure(0, weight=1)
            frame.grid_remove()  # Hide all frames initially
            
    def clear_frame(self, frame):
        """Clear all widgets from a frame"""
        for widget in frame.winfo_children():
            widget.destroy()

    def show_main_menu(self):
        if self.current_view:
            self.current_view.grid_remove()
        
        self.clear_frame(self.main_frame)
        
        # Main menu buttons
        button_frame = customtkinter.CTkFrame(self.main_frame)
        button_frame.grid(row=0, column=0, padx=20, pady=20)
        
        self.main_menu_elements = [button_frame]  # Track for cleanup
        
        new_session_btn = customtkinter.CTkButton(
            button_frame,
            text="Create New Session",
            command=self.show_new_session
        )
        new_session_btn.pack(pady=10, padx=20)
        
        load_session_btn = customtkinter.CTkButton(
            button_frame,
            text="Export Previous Session",
            command=self.show_load_session
        )
        load_session_btn.pack(pady=10, padx=20)
        
        self.current_view = self.main_frame
        self.main_frame.grid()

    def show_new_session(self):
        if self.current_view:
            self.current_view.grid_forget()
            
        self.clear_frame(self.new_session_frame)
        self.new_session_elements = []  # Reset tracked elements

        # Session name input
        name_label = customtkinter.CTkLabel(
            self.new_session_frame,
            text="Enter Session Name:"
        )
        name_label.pack(pady=(20,5))
        self.new_session_elements.append(name_label)
        
        self.session_name = customtkinter.CTkEntry(self.new_session_frame)
        self.session_name.pack(pady=5)
        self.new_session_elements.append(self.session_name)
        
        # Preview label
        self.preview_label = customtkinter.CTkLabel(
            self.new_session_frame,
            text="",
            wraplength=300
        )
        self.preview_label.pack(pady=10)
        self.new_session_elements.append(self.preview_label)
        
        # Update preview on keystroke
        self.session_name.bind('<KeyRelease>', self.update_filename_preview)
        
        # Buttons
        create_btn = customtkinter.CTkButton(
            self.new_session_frame,
            text="Create Session",
            command=self.create_session
        )
        create_btn.pack(pady=10)
        self.new_session_elements.append(create_btn)
        
        back_btn = customtkinter.CTkButton(
            self.new_session_frame,
            text="Back",
            command=self.show_main_menu
        )
        back_btn.pack(pady=10)
        self.new_session_elements.append(back_btn)
        
        self.current_view = self.new_session_frame
        self.new_session_frame.grid()

    def show_load_session(self):
        if self.current_view:
            self.current_view.grid_forget()
            
        self.clear_frame(self.load_session_frame)
        self.load_session_elements = []  # Reset tracked elements

        # Search frame
        search_frame = customtkinter.CTkFrame(self.load_session_frame)
        search_frame.pack(fill="x", padx=10, pady=10)
        self.load_session_elements.append(search_frame)
        
        # Search by name
        self.name_search = customtkinter.CTkEntry(
            search_frame,
            placeholder_text="Search by name..."
        )
        self.name_search.pack(side="left", padx=5)
        self.name_search.bind('<KeyRelease>', self.filter_sessions)
        
        # Date filter
        self.date_filter = DateEntry(
            search_frame,
            width=12,
            background='darkblue',
            foreground='white',
            borderwidth=2
        )
        self.date_filter.pack(side="left", padx=5)
        self.date_filter.bind('<<DateEntrySelected>>', self.filter_sessions)
        
        # Session list with scrollable frame
        self.session_frame = customtkinter.CTkScrollableFrame(
            self.load_session_frame,
            height=200
        )
        self.session_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Track currently selected session and label
        self.selected_session = None
        self.selected_label = None
        
        # Buttons
        button_frame = customtkinter.CTkFrame(self.load_session_frame)
        button_frame.pack(fill="x", padx=10, pady=10)
        
        export_btn = customtkinter.CTkButton(
            button_frame,
            text="Export Selected",
            command=self.export_session
        )
        export_btn.pack(side="left", padx=5)
        
        back_btn = customtkinter.CTkButton(
            button_frame,
            text="Back",
            command=self.show_main_menu
        )
        back_btn.pack(side="left", padx=5)
        
        # Populate session list
        self.refresh_session_list()
        
        self.current_view = self.load_session_frame
        self.load_session_frame.grid()

    def handle_session_click(self, label, session_name):
        # Unhighlight previous selection
        if self.selected_label:
            self.selected_label.configure(fg_color="transparent")
        
        # Highlight new selection
        label.configure(fg_color="#1f538d")  # Dark blue color
        self.selected_label = label
        self.selected_session = session_name

    def update_filename_preview(self, event=None):
        name = self.session_name.get()
        if name:
            timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
            filename = f"{name}_{timestamp}.db"
            self.preview_label.configure(text=f"Database will be created as:\n{filename}")
        else:
            self.preview_label.configure(text="")

    def create_session(self):
        name = self.session_name.get()
        if name:
            timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
            self.session_filename = self.data_folder_path / f"{name}_{timestamp}.db"
            self.master.destroy()

    def refresh_session_list(self):
        """List all .db files in the data folder"""
        # Clear existing labels
        for widget in self.session_frame.winfo_children():
            widget.destroy()
        
        self.selected_session = None
        self.selected_label = None
        
        self.filtered_sessions = sorted(
            [f for f in self.data_folder_path.glob("*.db")],
            key=lambda x: x.stat().st_mtime,
            reverse=True
        )
        
        for db_file in self.filtered_sessions:
            label = customtkinter.CTkLabel(
                self.session_frame,
                text=db_file.name,
                anchor="w",
                padx=5,
                pady=5,
                corner_radius=6
            )
            label.pack(fill="x", pady=2)
            label.bind("<Button-1>", lambda e, l=label, n=db_file.name: self.handle_session_click(l, n))

    def filter_sessions(self, event=None):
        """Filter sessions based on name search and date"""
        search_term = self.name_search.get().lower()
        selected_date = self.date_filter.get_date()
        
        # Clear existing labels
        for widget in self.session_frame.winfo_children():
            widget.destroy()
        
        self.selected_session = None
        self.selected_label = None
        self.filtered_sessions = []
        
        for db_file in self.data_folder_path.glob("*.db"):
            file_date = datetime.fromtimestamp(db_file.stat().st_mtime).date()
            
            if (search_term in db_file.stem.lower() and 
                (selected_date is None or file_date == selected_date)):
                self.filtered_sessions.append(db_file)
        
        # Sort by modification time (newest first)
        self.filtered_sessions.sort(key=lambda x: x.stat().st_mtime, reverse=True)
        
        for db_file in self.filtered_sessions:
            label = customtkinter.CTkLabel(
                self.session_frame,
                text=db_file.name,
                anchor="w",
                padx=5,
                pady=5,
                corner_radius=6
            )
            label.pack(fill="x", pady=2)
            label.bind("<Button-1>", lambda e, l=label, n=db_file.name: self.handle_session_click(l, n))

    def export_session(self):
        try:
            if not self.selected_session:
                logger.warning("No session selected for export")
                return
                
            db_path = self.data_folder_path / self.selected_session
            
            output_path = filedialog.asksaveasfilename(
                defaultextension=".csv",
                filetypes=[("CSV files", "*.csv")],
                initialfile=f"{db_path.stem}.csv"
            )
            
            if output_path:
                db = LoggingDatabase(db_path=db_path, schema_path=self.schema_path)
                db.export_to_csv(Path(output_path))
                logger.info(f"Successfully exported {db_path.name} to {output_path}")
        
        except Exception as e:
            logger.error(f"Failed to export session: {e}")