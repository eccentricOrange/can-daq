import copy

import matplotlib

matplotlib.use("TkAgg")

import collections
import queue
import threading
import time
from logging import getLogger

import customtkinter
import matplotlib.animation
import matplotlib.figure
import numpy
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg as FigureCanvas

import src.database_functionality
import src.devices
import src.messages
import src.protocols

logger = getLogger(__name__)

PLOT_COLOURS = [
    "#1f77b4",
    "#ff7f0e",
    "#2ca02c",
    "#d62728",
    "#9467bd",
    "#8c564b",
    "#e377c2",
    "#7f7f7f",
    "#bcbd22",
    "#17becf",
]


class MonitoringScreen:
    def __init__(self,
                 master: customtkinter.CTk,
                 protocol_frame: src.protocols.template_protocol.TemplateFrame,
                 device: src.devices.template_device.Device,
                 logging_database: src.database_functionality.LoggingDatabase,
                 timing_config: dict = None):
        self.ctk_frame = customtkinter.CTkFrame(master=master)
        self.protocol_frame = protocol_frame
        self.device = device

        self.monitoring = False
        self.serial_thread = None
        self.population_thread = None
        self.start_time: float = None
        self.data_queue = queue.Queue()
        self.plot_data = {}
        self.database_batch: list[src.protocols.template_protocol.TemplateFrame] = []
        self.statistics_batch: list[src.protocols.template_protocol.TemplateFrame] = []
        self.graph_data = {"timestamps": [], "values": []}
        self.signal_stats = {}
        self.signal_vars = {}
        self.logging_database = logging_database

        # Get timing values from configuration
        self.plot_max_points = timing_config.get('plot_max_points', 1000)
        self.plot_update_interval = timing_config.get('plot_update_interval', 100)
        self.database_batch_size = timing_config.get('database_batch_size', 1000)
        self.statistics_batch_size = timing_config.get('statistics_batch_size', 250)

        logger.info(f"plot_max_points: {self.plot_max_points}")
        logger.info(f"plot_update_interval: {self.plot_update_interval}")
        logger.info(f"database_batch_size: {self.database_batch_size}")
        logger.info(f"statistics_batch_size: {self.statistics_batch_size}")

        self.create_ui_elements()
        self.create_signal_checkboxes()

        # Start update threads
        self.animation = matplotlib.animation.FuncAnimation(
            self.fig, self.animate_plot, interval=self.plot_update_interval, save_count=100
        )

        self.graph_update_thread = threading.Thread(
            target=self.process_data_queue, daemon=True
        )
        self.graph_update_thread.start()

        self.ctk_frame.pack(pady=20, padx=20, fill="both", expand=True)


    def create_ui_elements(self):
        self.control_frame = customtkinter.CTkFrame(master=self.ctk_frame)
        self.control_frame.pack(fill="x", padx=10, pady=5)

        speeds_display = ""

        for property, value in self.device.device_configuration.get_main_speeds().items():
            speeds_display += f"[{property}:{value}] "

        self.baud_rate_text = customtkinter.CTkLabel(
            master=self.control_frame,
            text=speeds_display,
            anchor="w",
        )
        self.baud_rate_text.pack(side="left", padx=5)

        ports_display = ""

        for property, value in self.device.device_configuration.get_main_ports().items():
            ports_display += f"[{property}:{value}] "

        self.serial_port_text = customtkinter.CTkLabel(
            master=self.control_frame,
            text=ports_display,
            anchor="w",
        )
        self.serial_port_text.pack(side="left", padx=5)

        self.status_label = customtkinter.CTkLabel(
            master=self.control_frame, text="Status: Not Monitoring", anchor="w"
        )
        self.status_label.pack(side="left", padx=5)

        self.toggle_button = customtkinter.CTkButton(
            master=self.control_frame,
            text="Start Monitoring",
            command=self.toggle_monitoring,
        )
        self.toggle_button.pack(side="left", padx=5)

        self.main_content = customtkinter.CTkFrame(master=self.ctk_frame)
        self.main_content.pack(fill="both", expand=True, padx=10, pady=5)

        self.left_frame = customtkinter.CTkFrame(master=self.main_content)
        self.left_frame.pack(side="left", fill="both", expand=True, padx=(0, 5), pady=5)

        self.graph_frame = customtkinter.CTkFrame(master=self.left_frame)
        self.graph_frame.pack(fill="both", expand=True, padx=5, pady=5)

        self.right_frame = customtkinter.CTkFrame(master=self.main_content, width=200)
        self.right_frame.pack(side="right", fill="y", padx=(5, 0), pady=5)
        self.right_frame.pack_propagate(False)

        self.signals_frame = customtkinter.CTkScrollableFrame(
            master=self.right_frame,
            label_text="Signal Selection",
            width=180,
        )
        self.signals_frame.pack(fill="both", expand=True, padx=5, pady=5)

        # Add statistics frame
        self.stats_frame = customtkinter.CTkScrollableFrame(
            master=self.right_frame,
            label_text="Signal Statistics",
            width=180,
        )
        self.stats_frame.pack(fill="both", expand=True, padx=5, pady=5)

        self.fig = matplotlib.figure.Figure(figsize=(5, 4), dpi=100)
        self.plot = self.fig.add_subplot(111)
        self.fig.subplots_adjust(right=0.65)  # Give more space for multiple y-axes

        # Check if the app is in dark mode and set colors accordingly
        if customtkinter.get_appearance_mode().lower().strip() == "dark":
            self.fig.patch.set_facecolor('#2e2e2e')
            self.plot.set_facecolor('#2e2e2e')
            self.plot.tick_params(colors='white', which='both')
            self.plot.xaxis.label.set_color('white')
            self.plot.yaxis.label.set_color('white')
            self.plot.title.set_color('white')
        else:
            self.fig.patch.set_facecolor('white')
            self.plot.set_facecolor('white')
            self.plot.tick_params(colors='black', which='both')
            self.plot.xaxis.label.set_color('black')
            self.plot.yaxis.label.set_color('black')
            self.plot.title.set_color('black')

        self.canvas = FigureCanvas(self.fig, master=self.graph_frame)
        self.canvas.draw()
        self.canvas.get_tk_widget().pack(fill="both", expand=True)

        self.lines = {}
        self.plot.grid(True)
        self.plot.set_title("Signals")
        self.plot.set_ylabel("Value")

        self.axes = {}

    def create_signal_checkboxes(self):
        """Create checkboxes for all signals in protocol data"""
        if self.protocol_frame.protocol:
            self.select_all_button = customtkinter.CTkButton(
                master=self.signals_frame,
                text="Select All",
                command=self.select_all_signals,
                height=25,
            )
            self.select_all_button.pack(fill="x", padx=5, pady=2)

            self.deselect_all_button = customtkinter.CTkButton(
                master=self.signals_frame,
                text="Deselect All",
                command=self.deselect_all_signals,
                height=25,
            )
            self.deselect_all_button.pack(fill="x", padx=5, pady=2)

            separator = customtkinter.CTkFrame(master=self.signals_frame, height=1)
            separator.pack(fill="x", padx=5, pady=5)

            for message in self.protocol_frame.protocol.data_properties:
                message_label = customtkinter.CTkLabel(
                    master=self.signals_frame,
                    text=f"Message: {message.name}",
                    anchor="w",
                    font=("Arial", 12, "bold"),
                )
                message_label.pack(anchor="w", padx=5, pady=(10, 2))

                for signal in message.signals:
                    var = customtkinter.BooleanVar(value=False)
                    checkbox = customtkinter.CTkCheckBox(
                        master=self.signals_frame,
                        text=f"{signal.name} ({signal.unit})"
                        if signal.unit
                        else signal.name,
                        variable=var,
                        command=lambda s=signal.name: self.on_signal_toggle(s),
                    )
                    checkbox.pack(anchor="w", padx=20, pady=2)
                    self.signal_vars[signal.name] = {
                        "var": var,
                        "checkbox": checkbox,
                        "data": {"timestamps": [], "values": []},
                        "stats": {
                            "rms": 0.0,
                            "mean": 0.0,
                            "min": float("inf"),
                            "max": float("-inf"),
                            "p2p": 0.0,
                            "labels": {},  # Will store the label widgets
                        },
                    }

    def select_all_signals(self):
        """Select all signals"""
        for signal_data in self.signal_vars.values():
            signal_data["var"].set(True)
        self.update_axes()  # Update axes when checkboxes are toggled

    def deselect_all_signals(self):
        """Deselect all signals"""
        for signal_data in self.signal_vars.values():
            signal_data["var"].set(False)
        self.update_axes()  # Update axes when checkboxes are toggled

    def on_signal_toggle(self, signal_name):
        """Handle signal checkbox toggle"""
        if self.signal_vars[signal_name]["var"].get():
            logger.debug(f"Signal enabled: {signal_name}")
        else:
            logger.debug(f"Signal disabled: {signal_name}")
            self.signal_vars[signal_name]["data"]["timestamps"].clear()
            self.signal_vars[signal_name]["data"]["values"].clear()
        self.update_axes()  # Update axes when checkboxes are toggled

    def toggle_monitoring(self):
        if self.monitoring:
            self.stop_monitoring()
        else:
            self.start_monitoring()

    def create_statistics_labels(self):
        # Create statistics elements
        for widget in self.stats_frame.winfo_children():
            widget.destroy()

        for signal_name, signal_data in self.signal_vars.items():
            if signal_data["var"].get():
                signal_label = customtkinter.CTkLabel(
                    master=self.stats_frame,
                    text=f"\n{signal_name}:",
                    font=("Arial", 12, "bold"),
                )
                signal_label.pack(anchor="w", padx=5)

                stats_text = (
                    f"RMS: {0:.2f}\n"
                    f"Mean: {0:.2f}\n"
                    f"Min: {0:.2f}\n"
                    f"Max: {0:.2f}\n"
                    f"Peak-to-peak: {0:.2f}"
                )
                stats_label = customtkinter.CTkLabel(
                    master=self.stats_frame, text=stats_text, justify="left"
                )
                stats_label.pack(anchor="w", padx=20)

                self.signal_stats[signal_name] = stats_label

    def update_axes(self):
        self.axes.clear()
        self.fig.clear()
        self.lines.clear()

        self.plot = self.fig.add_subplot(1, 1, 1)
        self.plot.grid(True)
        self.plot.set_title("Signals")
        self.plot.set_xlabel("Time /s")
        self.plot.axes.get_yaxis().set_visible(False)
        # self.plot.axes.get_xaxis().set_visible(False)

        # Apply dark mode settings again
        if customtkinter.get_appearance_mode().lower().strip() == "dark":
            self.fig.patch.set_facecolor('#2e2e2e')
            self.plot.set_facecolor('#2e2e2e')
            self.plot.tick_params(colors='white', which='both')
            self.plot.xaxis.label.set_color('white')
            self.plot.yaxis.label.set_color('white')
            self.plot.title.set_color('white')
        else:
            self.fig.patch.set_facecolor('white')
            self.plot.set_facecolor('white')
            self.plot.tick_params(colors='black', which='both')
            self.plot.xaxis.label.set_color('black')
            self.plot.yaxis.label.set_color('black')
            self.plot.title.set_color('black')

        color_index = 0  # Initialize color index

        for message in self.protocol_frame.protocol.data_properties:
            for signal in message.signals:
                if self.signal_vars[signal.name]["var"].get():
                    if signal.name not in self.axes:
                        new_axis = self.plot.twinx()
                        new_axis.set_ylabel(
                            f"{signal.name} ({signal.unit if signal and signal.unit else ''})"
                        )

                        # Set limits for y-axis from signal min and max
                        new_axis.set_ylim(signal.min, signal.max)

                        # Assign a unique color to the y-axis
                        color = PLOT_COLOURS[color_index % len(PLOT_COLOURS)]
                        new_axis.spines["right"].set_color(color)
                        new_axis.tick_params(axis="y", colors=color)
                        new_axis.yaxis.label.set_color(color)
                        new_axis.spines["right"].set_position(
                            ("outward", 60 * (len(self.axes)))
                        )
                        new_axis.get_xaxis().set_visible(False)

                        self.axes[signal.name] = new_axis

                        color_index += 1  # Increment color index

        if self.axes:
            # Combine all legends
            lines = []
            labels = []
            for ax in self.axes.values():
                ax_lines, ax_labels = ax.get_legend_handles_labels()
                lines.extend(ax_lines)
                labels.extend(ax_labels)

            self.plot.legend(lines, labels, bbox_to_anchor=(1.35, 1), loc="upper left")
            self.plot.set_title("Signals")
            self.plot.set_xlabel("Time /s")

        self.create_statistics_labels()

        self.canvas.draw_idle()

    def start_monitoring(self):
        self.monitoring = True

        self.population_thread = threading.Thread(
            target=self.populate_data_buffers, daemon=True
        )
        self.population_thread.start()

        self.serial_thread = threading.Thread(
            target=self.monitor_serial, daemon=True
        )
        self.serial_thread.start()

        self.status_label.configure(text="Status: Monitoring")
        self.toggle_button.configure(text="Stop Monitoring")


        if not self.start_time:
            self.start_time = time.time()

    def stop_monitoring(self):
        self.monitoring = False
        self.status_label.configure(text="Status: Not Monitoring")
        self.toggle_button.configure(text="Start Monitoring")
        self.serial_thread.join()
        self.population_thread.join()
        self.device.close_data_reader()
        self.insert_batch_into_db()
        self.data_queue.queue.clear()

    def monitor_serial(self):
        self.device.initialize_data_reader()

        while self.monitoring:
            self.protocol_frame.raw_data = self.device.read_raw_data()

            try:
                self.protocol_frame.decoded_message = self.device.parse_raw_data(self.start_time)
                self.protocol_frame.interpret_frame()

            except Exception as e:
                logger.error(f"Error interpreting frame: {e}")

            else:
                for signal_name, signal_value in self.protocol_frame.interpreted_data.items():
                    self.data_queue.put((signal_name, self.protocol_frame.timestamp, signal_value))

                self.database_batch.append(copy.copy(self.protocol_frame))
                self.statistics_batch.append(copy.copy(self.protocol_frame))

    def populate_data_buffers(self):
        while self.monitoring:
            if len(self.database_batch) >= self.database_batch_size:
                self.insert_batch_into_db()

            if len(self.statistics_batch) >= self.statistics_batch_size:
                threading.Thread(target=self.calculate_statistics, daemon=True).start()

            time.sleep(0.1)

    def insert_batch_into_db(self):
        threading.Thread(
            target=self.logging_database.insert_frames,
            args=(self.database_batch,),  # This is already correct, but shown for context
            daemon=True,
        ).start()
        self.database_batch = []

    def animate_plot(self, i):
        """
        Animation function to update the plot with new data
        """
        try:
            # Create thread-safe copies of plot data
            plot_data_copy = {}
            for signal_name, signal_data in self.plot_data.items():
                plot_data_copy[signal_name] = {
                    "timestamps": list(signal_data["timestamps"]),
                    "values": list(signal_data["values"])
                }

            for signal_name, signal_data in plot_data_copy.items():
                if signal_name in self.axes:
                    color = self.axes[signal_name].spines["right"].get_edgecolor()
                    if signal_name not in self.lines:
                        (self.lines[signal_name],) = self.axes[signal_name].plot(
                            [], [], "-", label=signal_name, color=color
                        )
                    
                    if signal_data["timestamps"]:
                        self.lines[signal_name].set_data(
                            [x - self.start_time for x in signal_data["timestamps"]],
                            signal_data["values"]
                        )

            # Adjust x-axis limits using the copied data
            if plot_data_copy:
                all_timestamps = []
                for data in plot_data_copy.values():
                    if data["timestamps"]:
                        all_timestamps.extend(data["timestamps"])
                
                if all_timestamps:
                    min_timestamp = min(all_timestamps)
                    max_timestamp = max(all_timestamps)
                    self.plot.set_xlim(
                        max(min_timestamp, max_timestamp - self.plot_max_points) - self.start_time,
                        max_timestamp - self.start_time,
                    )

            self.canvas.draw_idle()
        except Exception as e:
            logger.error(f"Error in animate_plot: {e}")

    def calculate_statistics(self):
        signal_data_map = {signal.name: [] for message in self.protocol_frame.protocol.data_properties for signal in message.signals}

        for frame in self.statistics_batch:
            for signal_name, signal_value in frame.interpreted_data.items():
                if signal_name in signal_data_map:
                    signal_data_map[signal_name].append(signal_value)

        for signal_name, values in signal_data_map.items():
            if values and self.signal_vars[signal_name]["var"].get():  # Check if signal is selected
                values = numpy.array(values)
                mean = numpy.mean(values)
                rms = numpy.sqrt(numpy.mean(values**2))
                min_val = numpy.min(values)
                max_val = numpy.max(values)
                ptp = numpy.ptp(values)

                stats_text = (
                    f"RMS: {rms:.2f}\n"
                    f"Mean: {mean:.2f}\n"
                    f"Min: {min_val:.2f}\n"
                    f"Max: {max_val:.2f}\n"
                    f"Peak-to-peak: {ptp:.2f}"
                )
                self.signal_stats[signal_name].configure(text=stats_text)

        self.statistics_batch = []

    def process_data_queue(self):
        while True:
            try:
                signal_name, timestamp, value = self.data_queue.get(timeout=0.1)
                if signal_name not in self.plot_data:
                    self.plot_data[signal_name] = {
                        "timestamps": collections.deque(maxlen=self.plot_max_points),
                        "values": collections.deque(maxlen=self.plot_max_points),
                    }

                self.plot_data[signal_name]["timestamps"].append(timestamp)
                self.plot_data[signal_name]["values"].append(value)

            except queue.Empty:
                pass
            except Exception as e:
                logger.error(f"Error processing data queue: {e}")