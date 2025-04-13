import customtkinter

class TimingConfigScreen:
    width = 500  # Increased width to accommodate wrapped text
    height = 650  # Increased height to accommodate wrapped text

    def __init__(self, master: customtkinter.CTk):
        self.window = customtkinter.CTkToplevel(master)
        self.window.title("Advanced Timing Options")


        self.window.geometry(f"{self.width}x{self.height}")
        self.window.transient(master)
        
        # Wait for the window to be visible before setting grab
        self.window.wait_visibility()
        self.window.grab_set()

        self.create_ui_elements()
        
        # Default values as dict
        self.config_values = {
            'plot_max_points': 1000,
            'plot_update_interval': 100,
            'database_batch_size': 1000,
            'statistics_batch_size': 250
        }
        
    def create_ui_elements(self):
        # Calculate wraplength (window width minus padding)
        wrap_length = self.width - 40

        # Plot points
        plot_points_label = customtkinter.CTkLabel(
            master=self.window,
            text="Maximum Plot Points:",
            anchor="w"
        )
        plot_points_label.pack(padx=20, pady=(20, 5), anchor="w")
        
        plot_points_explanation = customtkinter.CTkLabel(
            master=self.window,
            text="Controls how many data points are shown in the plot at once. Configure this based on your sampling frequency.",
            anchor="w",
            text_color="gray",
            font=("", 12),
            wraplength=wrap_length,
            justify="left"  # Add left justification
        )
        plot_points_explanation.pack(padx=20, pady=(0, 5), anchor="w")
        
        self.plot_points_entry = customtkinter.CTkEntry(
            master=self.window,
            placeholder_text="1000"
        )
        self.plot_points_entry.pack(padx=20, pady=(0, 20), fill="x")
        
        # Update interval
        update_interval_label = customtkinter.CTkLabel(
            master=self.window,
            text="Plot Update Interval (ms):",
            anchor="w"
        )
        update_interval_label.pack(padx=20, pady=(20, 5), anchor="w")
        
        update_interval_explanation = customtkinter.CTkLabel(
            master=self.window,
            text="How frequently the plot refreshes on your screen. Lower values give smoother updates but use more CPU. Configure this based on your system performance.",
            anchor="w",
            text_color="gray",
            font=("", 12),
            wraplength=wrap_length,
            justify="left"  # Add left justification
        )
        update_interval_explanation.pack(padx=20, pady=(0, 5), anchor="w")
        
        self.update_interval_entry = customtkinter.CTkEntry(
            master=self.window,
            placeholder_text="100"
        )
        self.update_interval_entry.pack(padx=20, pady=(0, 20), fill="x")
        
        # Database batch
        db_batch_label = customtkinter.CTkLabel(
            master=self.window,
            text="Database Batch Size:",
            anchor="w"
        )
        db_batch_label.pack(padx=20, pady=(20, 5), anchor="w")
        
        db_batch_explanation = customtkinter.CTkLabel(
            master=self.window,
            text="Number of messages to collect before writing to database. Smaller values mean more frequent writes to the database, but may be fatal for performance. Configure this based on your sampling frequency.",
            anchor="w",
            text_color="gray",
            font=("", 12),
            wraplength=wrap_length,
            justify="left"  # Add left justification
        )
        db_batch_explanation.pack(padx=20, pady=(0, 5), anchor="w")
        
        self.db_batch_entry = customtkinter.CTkEntry(
            master=self.window,
            placeholder_text="1000"
        )
        self.db_batch_entry.pack(padx=20, pady=(0, 20), fill="x")
        
        # Statistics batch
        stats_batch_label = customtkinter.CTkLabel(
            master=self.window,
            text="Statistics Batch Size:",
            anchor="w"
        )
        stats_batch_label.pack(padx=20, pady=(20, 5), anchor="w")
        
        stats_batch_explanation = customtkinter.CTkLabel(
            master=self.window,
            text="Number of messages to process at once for statistics. Affects calculation frequency and CPU usage. Configure this based on your signal frequency.",
            anchor="w",
            text_color="gray",
            font=("", 12),
            wraplength=wrap_length,
            justify="left"  # Add left justification
        )
        stats_batch_explanation.pack(padx=20, pady=(0, 5), anchor="w")
        
        self.stats_batch_entry = customtkinter.CTkEntry(
            master=self.window,
            placeholder_text="250"
        )
        self.stats_batch_entry.pack(padx=20, pady=(0, 20), fill="x")
        
        # Save button
        save_button = customtkinter.CTkButton(
            master=self.window,
            text="Save",
            command=self.save_values
        )
        save_button.pack(pady=20)

    def save_values(self):
        try:
            self.config_values = {
                'plot_max_points': int(self.plot_points_entry.get() or 1000),
                'plot_update_interval': int(self.update_interval_entry.get() or 100),
                'database_batch_size': int(self.db_batch_entry.get() or 1000),
                'statistics_batch_size': int(self.stats_batch_entry.get() or 250)
            }
            self.window.destroy()
        except ValueError:
            error_label = customtkinter.CTkLabel(
                master=self.window,
                text="Please enter valid numbers",
                text_color="red"
            )
            error_label.pack(pady=10)
    
    def get_values(self):
        """Return the configuration values"""
        return self.config_values
