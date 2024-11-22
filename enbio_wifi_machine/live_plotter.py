import matplotlib.pyplot as plt
from collections import deque
from enbio_wifi_machine.common import ProcessLine


# Define deque to store live data
class LivePlotter:
    def __init__(self, buffer_size=250):
        self.sec_data = deque(maxlen=buffer_size)
        self.p_proc_data = deque(maxlen=buffer_size)
        self.t_proc_data = deque(maxlen=buffer_size)
        self.t_chmbr_data = deque(maxlen=buffer_size)
        self.t_stmgn_data = deque(maxlen=buffer_size)
        self.ch_heaters_states = deque(maxlen=buffer_size)
        self.sg_heaters_double_states = deque(maxlen=buffer_size)
        self.sg_heater_single_states = deque(maxlen=buffer_size)

        plt.ion()
        self.fig, self.ax1 = plt.subplots()
        self.line_t_proc, = self.ax1.plot([], [], label="t_proc", color="blue")
        self.line_t_chmbr, = self.ax1.plot([], [], label="t_chmbr", color="green")
        self.line_t_stmgn, = self.ax1.plot([], [], label="t_stmgn", color="orange")
        self.ax1.set_title("Live Sensor Measurements")
        self.ax1.set_xlabel("Time (sec)")
        self.ax1.set_ylabel("Temperature (°C)")
        self.ax1.legend(loc="upper left")
        self.ax1.grid()
        self.ax2 = self.ax1.twinx()
        self.line_p_proc, = self.ax2.plot([], [], label="p_proc", color="red")
        self.ax2.set_ylabel("p_proc")
        self.ax2.tick_params(axis="y", labelcolor="red")
        self.ax2.legend(loc="upper right")

    def update_plot(self):
        self.ax1.clear()  # Clear the primary axis to redraw everything
        self.ax2.clear()  # Clear the secondary axis to redraw everything

        # Plot temperature and pressure data
        self.ax1.plot(self.sec_data, self.t_proc_data, label="t_proc", color="blue")
        self.ax1.plot(self.sec_data, self.t_chmbr_data, label="t_chmbr", color="green")
        self.ax1.plot(self.sec_data, self.t_stmgn_data, label="t_stmgn", color="orange")
        self.ax2.plot(self.sec_data, self.p_proc_data, label="p_proc", color="red")

        # Set labels and legends for both axes
        self.ax1.set_title("Live Sensor Measurements")
        self.ax1.set_xlabel("Time (sec)")
        self.ax1.set_ylabel("Temperature (°C)")
        self.ax1.legend(loc="upper left")
        self.ax1.grid()
        self.ax2.set_ylabel("p_proc")
        self.ax2.tick_params(axis="y", labelcolor="red")
        self.ax2.legend(loc="upper right")

        # Add filled backgrounds for heater states
        for i in range(1, len(self.sec_data)):  # Iterate through time intervals
            start_time = self.sec_data[i - 1]
            end_time = self.sec_data[i]

            # Draw filled regions for heater states
            if self.ch_heaters_states[i] and (self.sg_heaters_double_states[i] or self.sg_heater_single_states[i]):
                self.ax1.axvspan(start_time, end_time, color="red", alpha=0.8, label="both ch and sg - bad")
            else:
                if self.ch_heaters_states[i]:
                    self.ax1.axvspan(start_time, end_time, color="green", alpha=0.1, label="ch_heaters ON")
                if self.sg_heaters_double_states[i]:
                    self.ax1.axvspan(start_time, end_time, color="orange", alpha=0.4, label="sg_heaters_double ON")
                if self.sg_heater_single_states[i]:
                    self.ax1.axvspan(start_time, end_time, color="orange", alpha=0.2, label="sg_heater_single ON")


        # Rescale axes dynamically
        self.ax1.relim()
        self.ax1.autoscale_view()
        self.ax2.relim()
        self.ax2.autoscale_view()

        # Redraw the plot
        plt.draw()
        plt.pause(0.01)

    def add_data(self, process_line: ProcessLine):
        sensors = process_line.sensors_msrs
        do_state = process_line.do_state

        self.sec_data.append(process_line.sec)
        self.p_proc_data.append(sensors.p_proc)
        self.t_proc_data.append(sensors.t_proc)
        self.t_chmbr_data.append(sensors.t_chmbr)
        self.t_stmgn_data.append(sensors.t_stmgn)
        self.ch_heaters_states.append(do_state.ch_heaters)
        self.sg_heaters_double_states.append(do_state.sg_heaters_double)
        self.sg_heater_single_states.append(do_state.sg_heater_single)
