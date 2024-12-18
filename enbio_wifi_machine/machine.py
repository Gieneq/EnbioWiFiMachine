import csv
import os
import threading
import time
import minimalmodbus
import serial.tools.list_ports
from datetime import datetime
from enbio_wifi_machine.plotter import LivePlotter
from enbio_wifi_machine.common import ProcessType, label_to_process_type, ProcessLine, EnbioDeviceInternalException, \
    float_to_ints, \
    ints_to_float, cfg, process_type_values, ScreenId, ScaleFactors, ScaleFactor, Relay, RelayState, ValveState, \
    DOState, PWRState, SensorsMeasurements, HeatersToggleCounts
from enbio_wifi_machine.modbus_registers import ModbusRegister


class EnbioWiFiMachine:
    """ Abstraction of Enbio WiFi machine via USB Serial Modbus RTU protocol """

    enbio_wifi_usb_serial_number = "ENBIOWIFIBOARD"
    """ Value in USB Serial port used to distinguis Enbio WiFi devices """

    device_id_max_length = 32
    """ Device id is called serial number. Using Device id to distinguish from other """

    def __init__(self, port: [str | None] = None, address=1):
        port = self._detect_modbus_device_port(address) if port is None else port
        if port is None:
            raise EnbioDeviceInternalException("Modbus device not found on any available port.")

        self._device = minimalmodbus.Instrument(port, address, close_port_after_each_call=True, debug=False)
        self._device.serial.baudrate = cfg["serial_port"]
        self._device.serial.bytesize = 8
        self._device.serial.stopbits = 1
        self._device.serial.parity = minimalmodbus.serial.PARITY_EVEN
        self._device.serial.timeout = cfg["serial_timeout"]

    def write_int_register(self, register: int, value: int):
        self._device.write_register(register, value)

    def read_int_register(self, register: int) -> int:
        return self._device.read_register(register)

    def _read_float_register(self, register):
        low, high = self._device.read_registers(register, 2)
        return ints_to_float(low, high)

    def _write_float_register(self, register, float_value):
        low, high = float_to_ints(float_value)
        self._device.write_register(register, low)
        self._device.write_register(register + 1, high)

    def _write_reg_feedback(self, register, value, await_time: float = 0.1):
        """ Writes register and read value back to ensure """

        print(f"_write_reg_feedback {register} -> {value}")
        self._device.write_register(register, value)
        time.sleep(await_time)

        feedback_value = self._device.read_register(register)
        print(f"_write_reg_feedback {register} <- {feedback_value}")

        # Check if the value is as expected
        if value != feedback_value:
            raise EnbioDeviceInternalException(f"Error: Expected value {value}, but got {feedback_value}")

    def _write_ctrl_reg_feedback(self, register, await_time: float = 0.1):
        """ Writes register flag and awaits clearing (reading 0) or getting error result (reading 0xFFFF) """
        activating_value = 1
        success_value = 0
        print(f"_write_ctrl_reg_feedback {register} -> {activating_value}")
        self._device.write_register(register, activating_value)
        time.sleep(await_time)

        feedback_value = self._device.read_register(register)
        print(f"_write_ctrl_reg_feedback {register} <- {feedback_value}")

        # Check if the value is as expected
        if feedback_value != success_value:
            raise EnbioDeviceInternalException(f"Error: Expected value {activating_value}, but got {feedback_value}")

    def _detect_modbus_device_port(self, address) -> str | None:
        """Attempt to automatically detect the Modbus device by scanning available serial ports."""
        # List all available serial ports
        available_ports = serial.tools.list_ports.comports()

        for port in available_ports:
            if port.serial_number != self.enbio_wifi_usb_serial_number:
                continue

            print(f"Found Enbio device on port: {port.name}")

            try:
                # Try to initialize the Modbus device on this port
                tmp_device = minimalmodbus.Instrument(port.device, address, close_port_after_each_call=True, debug=False)
                tmp_device.serial.baudrate = cfg["serial_port"]
                tmp_device.serial.bytesize = 8
                tmp_device.serial.stopbits = 1
                tmp_device.serial.parity = minimalmodbus.serial.PARITY_EVEN
                tmp_device.serial.timeout = cfg["serial_timeout"]

                response_device_id = self._get_device_id(tmp_device)
                print(f"Device found on port {port.device} with device id: {response_device_id}")
                return port.device  # Return the detected port if communication is successful

            except (minimalmodbus.NoResponseError, minimalmodbus.SlaveReportedException, IOError):
                # If there’s no response or an error, skip this port
                continue

        # Return None if no valid Modbus device is found on any port
        return None

    def _drv_coil_until(self, direction_func, stop_condition_func, timeout: float | None = None,
                        action_name: str = "move") -> None:
        """Move the door in a specified direction until a condition is met, with feedback and optional timeout."""
        start_time = time.time()

        # Start moving the door in the specified direction
        direction_func()

        try:
            while not stop_condition_func():
                # Check for timeout
                if timeout is not None and (time.time() - start_time) > timeout:
                    self.door_drv_none()  # Stop the motor
                    raise EnbioDeviceInternalException(f"Timeout reached while attempting to {action_name} the door.")

                time.sleep(0.01)  # Small delay to avoid excessive polling

            # Stop the motor once the condition is met
            self.door_drv_none()
            print(f"Door {action_name} successfully.")

        except Exception as e:
            self.door_drv_none()  # Ensure the motor stops in case of any error
            raise e

    def set_device_id(self, dev_id: str) -> None:
        if len(dev_id) > self.device_id_max_length:
            raise EnbioDeviceInternalException(f"Device ID too long: {len(dev_id)} / {self.device_id_max_length}")

        # Fill zeros 32 bytes in total
        padded_dev_id = dev_id.ljust(self.device_id_max_length, '\0')

        self._device.write_string(ModbusRegister.DEVICE_ID.value, padded_dev_id, self.device_id_max_length)
        print(f"Device ID set to: {dev_id}")

    @classmethod
    def _get_device_id(cls, device: minimalmodbus.Instrument):
        dev_id = device.read_string(ModbusRegister.DEVICE_ID.value, cls.device_id_max_length)
        return dev_id.rstrip('\0')

    def get_device_id(self) -> str:
        try:
            return self._get_device_id(self._device)
        except IOError:
            print("Failed to read device ID.")
            return ""

    def is_door_open(self) -> bool:
        return self._device.read_register(ModbusRegister.DOOR_OPEN.value) != 0

    def is_door_unlocked(self) -> bool:
        return self._device.read_register(ModbusRegister.DOOR_UNLOCKED.value) != 0

    def door_drv_fwd(self) -> None:
        self._write_reg_feedback(ModbusRegister.COIL_CONTROL.value, 2, await_time=0.001)

    def door_drv_bwd(self) -> None:
        self._write_reg_feedback(ModbusRegister.COIL_CONTROL.value, 1, await_time=0.001)

    def door_drv_none(self) -> None:
        self._write_reg_feedback(ModbusRegister.COIL_CONTROL.value, 0, await_time=0.001)

    def door_lock_with_feedback(self, timeout: float | None = None) -> None:
        """Drive forward until the door is locked."""
        self._drv_coil_until(
            direction_func=self.door_drv_fwd,
            stop_condition_func=lambda: not self.is_door_unlocked(),
            timeout=timeout,
            action_name="lock"
        )

    def door_unlock_with_feedback(self, timeout: float | None = None) -> None:
        """Drive backward until the door is unlocked."""
        self._drv_coil_until(
            direction_func=self.door_drv_bwd,
            stop_condition_func=self.is_door_unlocked,
            timeout=timeout,
            action_name="unlock"
        )

    def get_test_int(self) -> int:
        return self._device.read_register(ModbusRegister.TEST_INT.value)

    def set_test_int(self, new_value: int):
        self._device.write_register(ModbusRegister.TEST_INT.value, new_value)

    def get_test_float(self) -> float:
        return self._read_float_register(ModbusRegister.TEST_FLOAT.value)

    def set_test_float(self, new_value: float):
        self._write_float_register(ModbusRegister.TEST_FLOAT.value, new_value)

    def get_firmware_version(self) -> str:
        firmware_value = self._device.read_register(ModbusRegister.FIRMWARE_VERSION.value)
        major = firmware_value >> 9
        minor = (firmware_value >> 4) & 0x1F
        patch = firmware_value & 0xF
        return f"{major}.{minor}.{patch}"

    def get_boardnumber(self) -> (chr, int):
        boardnum = self._device.read_register(ModbusRegister.BOARD_NUM.value)
        return chr((boardnum >> 11) + ord('A')), (boardnum >> 4) & 0x7F, boardnum & 0xF

    def set_boardnumber(self, board_rev: chr, prod_year: int, prod_month: int) -> None:
        if not (board_rev.isalpha() and board_rev.isupper()):
            raise EnbioDeviceInternalException(f"Bad board revision {board_rev}")

        revision_code = ord(board_rev) - ord('A')

        new_boardnum = (revision_code << 11) | (prod_year << 4) | prod_month
        self._device.write_register(ModbusRegister.BOARD_NUM.value, new_boardnum)

    def get_datetime(self) -> datetime:
        # Note: can also use get/set variant
        return datetime(
            year=self._device.read_register(ModbusRegister.DATETIME_GET_YEAR.value),
            month=self._device.read_register(ModbusRegister.DATETIME_GET_MONTH.value),
            day=self._device.read_register(ModbusRegister.DATETIME_GET_DAY.value),
            hour=self._device.read_register(ModbusRegister.DATETIME_GET_HOUR.value),
            minute=self._device.read_register(ModbusRegister.DATETIME_GET_MINUTE.value),
            second=self._device.read_register(ModbusRegister.DATETIME_GET_SECOND.value),
            microsecond=0
        )

    def set_datetime(self, dt: datetime) -> None:
        dt = dt.replace(second=0, microsecond=0)

        self._device.write_register(ModbusRegister.DATETIME_GET_SET_DAY.value, dt.day)
        self._device.write_register(ModbusRegister.DATETIME_GET_SET_MONTH.value, dt.month)
        self._device.write_register(ModbusRegister.DATETIME_GET_SET_YEAR.value, dt.year)
        self._device.write_register(ModbusRegister.DATETIME_GET_SET_HOUR.value, dt.hour)
        self._device.write_register(ModbusRegister.DATETIME_GET_SET_MINUTE.value, dt.minute)

        self._write_ctrl_reg_feedback(ModbusRegister.DATETIME_SAVE.value)

    def get_dpi_switch(self) -> (bool, bool, bool, bool):
        dipsw_value = self._device.read_register(ModbusRegister.DIP_SWITCH.value)
        return dipsw_value & 1 > 0, dipsw_value & 2 > 0, dipsw_value & 4 > 0, dipsw_value & 8 > 0

    def get_standby_cooling_thrsh_tmpr(self) -> int:
        return self._device.read_register(ModbusRegister.STANDBY_COOLING_THRSH.value)

    def set_standby_cooling_thrsh_tmpr(self, thrsh: int) -> None:
        self._device.write_register(ModbusRegister.STANDBY_COOLING_THRSH.value, thrsh)

    def get_process_counter(self) -> int:
        return self._device.read_register(ModbusRegister.EXECUTION_COUNTER.value)

    def clear_process_counter(self) -> None:
        self._write_reg_feedback(ModbusRegister.EXECUTION_COUNTER.value, 0, await_time=1.0)

    def save_all(self) -> None:
        self._write_ctrl_reg_feedback(ModbusRegister.SAVE_ALL.value)

    def reboot(self) -> None:
        try:
            self._device.write_register(ModbusRegister.STM_REBOOT.value, 1)
        except Exception:
            pass

    def start_process(self, process_type: ProcessType) -> None:
        print(f"start screen {self._device.read_register(ModbusRegister.CHANGE_SCREEN.value)}")

        if self._device.read_register(ModbusRegister.PROC_STATUS.value) == 1:
            raise EnbioDeviceInternalException("Process already running")

        print(f"Starting Process Type: {process_type}")

        self._device.write_register(ModbusRegister.PROC_SELECT_START.value, process_type_values[process_type])
        time.sleep(0.5)

        self._write_ctrl_reg_feedback(ModbusRegister.PROC_SELECT_START.value)

    def get_recent_screen(self) -> ScreenId:
        raw_value = self._device.read_register(ModbusRegister.PROC_STATUS.value)
        print(f"Recent screen raw value: {raw_value}")
        try:
            # Attempt to map the raw value to a ScreenId enum
            return ScreenId(raw_value)
        except ValueError:
            # Handle case where raw_value does not match any ScreenId
            raise ValueError(f"Cannot convert {raw_value} to ScreenId enum")

    # def _await_change_screen_to(self, next_screen: ScreenId):
    def interrupt_process(self) -> None:
        if self._device.read_register(ModbusRegister.PROC_STATUS.value) == 1:
            print("interrupt")
            self._device.write_register(ModbusRegister.PROC_SELECT_START.value, 0xFFFF)
            # Soe time to show summary
            time.sleep(3)
            self._write_reg_feedback(ModbusRegister.CHANGE_SCREEN.value, ScreenId.MAIN.value, await_time=0.1)

    def get_do_state(self) -> DOState:
        return DOState.from_bitfields(self._device.read_register(ModbusRegister.PROC_DO_STATE.value))

    def get_pwr_state(self) -> PWRState:
        return PWRState(
            ptrn=self._device.read_register(ModbusRegister.PWR_CTRL_PATTERN.value),

            ch_pwr=self._device.read_register(ModbusRegister.PWR_CH_DRV_MONITOR.value),
            ch_tar=self._device.read_register(ModbusRegister.PWR_CH_TARGET.value),
            sg_pwr=self._device.read_register(ModbusRegister.PWR_SG_DRV_MONITOR.value),
            sg_tar=self._device.read_register(ModbusRegister.PWR_SG_TARGET.value),
        )

    def get_sensors_measurements(self) -> SensorsMeasurements:
        return SensorsMeasurements(
            p_proc=self._read_float_register(ModbusRegister.PRESSURE_PROCESS.value),
            p_ext=self._read_float_register(ModbusRegister.ATMOSPHERIC_PRESSURE.value),
            t_proc=self._read_float_register(ModbusRegister.TEMPERATURE_PROCESS.value),
            t_chmbr=self._read_float_register(ModbusRegister.TEMPERATURE_CHAMBER.value),
            t_stmgn=self._read_float_register(ModbusRegister.TEMPERATURE_STEAMGEN.value),
            t_ext=self._read_float_register(ModbusRegister.TEMPERATURE_EXTERNAL.value),
        )

    def poll_process_line(self) -> ProcessLine:
        return ProcessLine(
            sec=self._device.read_register(ModbusRegister.PROC_SECONDS.value),
            phase=self.get_phase_id(),

            pwr_state=self.get_pwr_state(),
            do_state=self.get_do_state(),
            sensors_msrs=self.get_sensors_measurements(),
        )

    def get_scale_factors(self) -> ScaleFactors:
        scale_factors = ScaleFactors(
            pressure_process=ScaleFactor(
                a=self._read_float_register(ModbusRegister.SCALE_FACTORS_PRESS_PROC_A.value),
                b=self._read_float_register(ModbusRegister.SCALE_FACTORS_PRESS_PROC_B.value)
            ),
            temperature_process=ScaleFactor(
                a=self._read_float_register(ModbusRegister.SCALE_FACTORS_TMPR_PROC_A.value),
                b=self._read_float_register(ModbusRegister.SCALE_FACTORS_TMPR_PROC_B.value)
            ),
            temperature_chamber=ScaleFactor(
                a=self._read_float_register(ModbusRegister.SCALE_FACTORS_TMPR_CHMBR_A.value),
                b=self._read_float_register(ModbusRegister.SCALE_FACTORS_TMPR_CHMBR_B.value)
            ),
            temperature_steamgen=ScaleFactor(
                a=self._read_float_register(ModbusRegister.SCALE_FACTORS_TMPR_SG_A.value),
                b=self._read_float_register(ModbusRegister.SCALE_FACTORS_TMPR_SG_B.value)
            )
        )

        return scale_factors

    def set_scale_factors(self, scale_factors: ScaleFactors) -> None:
        self._write_float_register(ModbusRegister.SCALE_FACTORS_PRESS_PROC_A.value, scale_factors.pressure_process.a)
        self._write_float_register(ModbusRegister.SCALE_FACTORS_PRESS_PROC_B.value, scale_factors.pressure_process.b)

        self._write_float_register(ModbusRegister.SCALE_FACTORS_TMPR_PROC_A.value, scale_factors.temperature_process.a)
        self._write_float_register(ModbusRegister.SCALE_FACTORS_TMPR_PROC_B.value, scale_factors.temperature_process.b)

        self._write_float_register(ModbusRegister.SCALE_FACTORS_TMPR_CHMBR_A.value, scale_factors.temperature_chamber.a)
        self._write_float_register(ModbusRegister.SCALE_FACTORS_TMPR_CHMBR_B.value, scale_factors.temperature_chamber.b)

        self._write_float_register(ModbusRegister.SCALE_FACTORS_TMPR_SG_A.value, scale_factors.temperature_steamgen.a)
        self._write_float_register(ModbusRegister.SCALE_FACTORS_TMPR_SG_B.value, scale_factors.temperature_steamgen.b)

    def get_valve(self, valve_relay: Relay) -> ValveState:
        if valve_relay == Relay.Valve1:
            return ValveState(self._device.read_register(ModbusRegister.VALVE1.value))
        elif valve_relay == Relay.Valve2:
            return ValveState(self._device.read_register(ModbusRegister.VALVE2.value))
        elif valve_relay == Relay.Valve3:
            return ValveState(self._device.read_register(ModbusRegister.VALVE3.value))
        elif valve_relay == Relay.Valve5:
            return ValveState(self._device.read_register(ModbusRegister.VALVE5.value))

    def set_valve(self, valve_relay: Relay, valve_state: ValveState) -> None:
        if valve_relay == Relay.Valve1:
            self._write_reg_feedback(ModbusRegister.VALVE1.value, valve_state.value)
        if valve_relay == Relay.Valve2:
            self._write_reg_feedback(ModbusRegister.VALVE2.value, valve_state.value)
        if valve_relay == Relay.Valve3:
            self._write_reg_feedback(ModbusRegister.VALVE3.value, valve_state.value)
        if valve_relay == Relay.Valve5:
            self._write_reg_feedback(ModbusRegister.VALVE5.value, valve_state.value)

    def get_relay(self, relay: Relay) -> RelayState:
        if relay == Relay.SteamgenDouble:
            return RelayState(self._device.read_register(ModbusRegister.RELAY_STEAMGEN_AB.value))
        elif relay == Relay.Chamber:
            return RelayState(self._device.read_register(ModbusRegister.RELAY_CHAMBER_AB.value))
        elif relay == Relay.VacuumPump:
            return RelayState(self._device.read_register(ModbusRegister.RELAY_PUMP_VACUUM.value))
        elif relay == Relay.WaterPump:
            return RelayState(self._device.read_register(ModbusRegister.RELAY_PUMP_WATER.value))
        elif relay == Relay.SteamgenSingle:
            return RelayState(self._device.read_register(ModbusRegister.RELAY_STEAMGEN_C.value))

    def set_relay(self, relay: Relay, state: RelayState) -> None:
        if relay == Relay.SteamgenDouble:
            self._write_reg_feedback(ModbusRegister.RELAY_STEAMGEN_AB.value, state.value)
        elif relay == Relay.Chamber:
            self._write_reg_feedback(ModbusRegister.RELAY_CHAMBER_AB.value, state.value)
        elif relay == Relay.VacuumPump:
            self._write_reg_feedback(ModbusRegister.RELAY_PUMP_VACUUM.value, state.value)
        elif relay == Relay.WaterPump:
            self._write_reg_feedback(ModbusRegister.RELAY_PUMP_WATER.value, state.value)
        elif relay == Relay.SteamgenSingle:
            self._write_reg_feedback(ModbusRegister.RELAY_STEAMGEN_C.value, state.value)

    def get_pressure(self, sensor: str) -> float:
        if sensor == "process":
            return self._read_float_register(ModbusRegister.PRESSURE_PROCESS.value)
        if sensor == "relative":
            return self._read_float_register(ModbusRegister.PRESSURE_RELATIVE.value)
        if sensor == "external":
            return self._read_float_register(ModbusRegister.ATMOSPHERIC_PRESSURE.value)
        raise ValueError("Bad 'sensor' argument")

    def get_temperature(self, sensor: str) -> float:
        if sensor == "process":
            return self._read_float_register(ModbusRegister.TEMPERATURE_PROCESS.value)
        if sensor == "chamber":
            return self._read_float_register(ModbusRegister.TEMPERATURE_CHAMBER.value)
        if sensor == "steamgen":
            return self._read_float_register(ModbusRegister.TEMPERATURE_STEAMGEN.value)
        if sensor == "external":
            return self._read_float_register(ModbusRegister.TEMPERATURE_EXTERNAL.value)
        raise ValueError("Bad 'sensor' argument")

    def get_raw_temperature(self, sensor: str) -> float:
        if sensor == "pressure":
            return self._read_float_register(ModbusRegister.ADCF_PRESS_PROCESS.value)
        if sensor == "process":
            return self._read_float_register(ModbusRegister.ADCF_TMPR_PROCESS.value)
        if sensor == "chamber":
            return self._read_float_register(ModbusRegister.ADCF_TMPR_CHAMBER.value)
        if sensor == "steamgen":
            return self._read_float_register(ModbusRegister.ADCF_TMPR_STEAMGE.value)
        raise ValueError("Bad 'sensor' argument")

    def get_raw_sensor_value(self, sensor: str) -> float:
        if sensor == "pressure":
            return self._read_float_register(ModbusRegister.ADCF_PRESS_PROCESS.value)
        if sensor == "process":
            return self._read_float_register(ModbusRegister.ADCF_TMPR_PROCESS.value)
        if sensor == "chamber":
            return self._read_float_register(ModbusRegister.ADCF_TMPR_CHAMBER.value)
        if sensor == "steamgen":
            return self._read_float_register(ModbusRegister.ADCF_TMPR_STEAMGE.value)
        raise ValueError("Bad 'sensor' argument")

    def get_heater_toggle_cnts(self) -> HeatersToggleCounts:
        return HeatersToggleCounts(
            sg_ab=self.read_int_register(ModbusRegister.HEATERS_TOGGLE_MSR_SG_AB.value),
            ch_ab=self.read_int_register(ModbusRegister.HEATERS_TOGGLE_MSR_CH_AB.value),
            sg_c=self.read_int_register(ModbusRegister.HEATERS_TOGGLE_MSR_SG_C.value),
        )

    def set_heater_toggle_cnts(self, cnts: HeatersToggleCounts):
        if cnts.sg_ab is not None:
            self.write_int_register(ModbusRegister.HEATERS_TOGGLE_MSR_SG_AB.value, cnts.sg_ab)

        if cnts.ch_ab is not None:
            self.write_int_register(ModbusRegister.HEATERS_TOGGLE_MSR_CH_AB.value, cnts.ch_ab)

        if cnts.sg_c is not None:
            self.write_int_register(ModbusRegister.HEATERS_TOGGLE_MSR_SG_C.value, cnts.sg_c)

    def runmonitor(self, proces_name: str, plotting: bool = False, interval: float = 1.0, identifier: str = "PA") -> None:
        self.start_process(label_to_process_type.get(proces_name))
        plotter = LivePlotter() if plotting else None

        dirname = "measurements"
        os.makedirs(dirname, exist_ok=True)

        start_time = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        filepath = os.path.join(dirname, f"meas_{proces_name}_int_{round(interval*1000)}_id_{identifier}"
                                         f"_fmt_v1_{start_time}.csv")
        
        with open(filepath, mode='w', newline='') as csvfile:
            csvwriter = csv.writer(csvfile)
            csvwriter.writerow(["Time (sec)",
                                "ProcPress (bar)",
                                "ExtPress (bar)",
                                "ProcTempr *C",
                                "ChmbrTempr *C",
                                "SGTempr *C",
                                "ExtTmpr *C",

                                "ProcType",
                                "V1",
                                "V2",
                                "V3",
                                "V5",
                                "Vacuum",
                                "Water",
                                "ChHeat",
                                "ShdHeat",
                                "SgsHeat",

                                "ChTar *C",
                                "ChPWR %",
                                "SgTar *C",
                                "SgPWR %",
                                ])

            proctime = 0.0

            try:
                while True:
                    start_time = time.time()

                    pline = self.poll_process_line()

                    # prevent plot dropping after finish
                    if pline.do_state.proc_type is not None:
                        pline.sec = proctime
                        if plotter is not None:
                            plotter.add_data(pline)
                            plotter.update_plot()

                        csvwriter.writerow([proctime,
                                            pline.sensors_msrs.p_proc,
                                            pline.sensors_msrs.p_ext,
                                            pline.sensors_msrs.t_proc,
                                            pline.sensors_msrs.t_chmbr,
                                            pline.sensors_msrs.t_stmgn,
                                            pline.sensors_msrs.t_ext,

                                            pline.do_state.proc_type.value if pline.do_state.proc_type is not None else 0,

                                            pline.do_state.v1_open,
                                            pline.do_state.v2_open,
                                            pline.do_state.v3_open,
                                            pline.do_state.v5_open,
                                            pline.do_state.pump_vac,
                                            pline.do_state.pump_water,
                                            pline.do_state.ch_heaters,
                                            pline.do_state.sg_heaters_double,
                                            pline.do_state.sg_heater_single,

                                            pline.pwr_state.ch_tar,
                                            pline.pwr_state.ch_pwr,
                                            pline.pwr_state.sg_tar,
                                            pline.pwr_state.sg_pwr,
                                            ])
                        csvfile.flush()

                    # Measure execution time and calculate sleep time
                    exec_time = time.time() - start_time  # Time taken for execution
                    sleep_time = max(0, interval - exec_time)  # Ensure sleep_time is not negative
                    time.sleep(sleep_time)  # Sleep for the remaining time to maintain interval
                    if exec_time > interval:
                        print(f"Warning execution time:{exec_time}, sleep time: {sleep_time} exceeded interval: {interval}")

                    # Update the process time counter
                    proctime += interval

                    # print(pline)
            except KeyboardInterrupt as e:
                print("Interrupting...")
                self.interrupt_process()
                raise e

    def monitor(self) -> None:
        plotter = LivePlotter()
        monitor_time = 0
        try:
            while True:
                time.sleep(1)
                monitor_time += 1
                pline = self.poll_process_line()
                pline.sec = monitor_time
                plotter.add_data(pline)
                plotter.update_plot()
                print(pline)
        except KeyboardInterrupt as e:
            print("Stopping...")
            raise e

    def get_phase_id(self) -> int:
        return self._device.read_register(ModbusRegister.PROC_PHASE.value)

    def set_backlight(self, brightness_perc: int):
        self._device.write_register(ModbusRegister.BACKLIGHT.value, brightness_perc)

    def get_backlight(self) -> int:
        return self._device.read_register(ModbusRegister.BACKLIGHT.value)

    def reset_parameters_with_target(self, target_us: bool = True):
        self._device.write_register(ModbusRegister.USE_DEFAULT_MODBUS_PARAMS.value, 2 if target_us else 1)


def thread_procedure(procedure: str, test_machine: EnbioWiFiMachine, lock: threading.Lock):
    if procedure == "door":
        while True:
            with lock:
                if test_machine.is_door_unlocked():
                    test_machine.door_lock_with_feedback()
                else:
                    test_machine.door_unlock_with_feedback()
            time.sleep(0.01)

    elif procedure == "valves":
        valves_list = [[Relay.Valve1, True], [Relay.Valve2, False], [Relay.Valve3, True], [Relay.Valve5, False]]
        while True:
            with lock:
                for idx, valve_state in enumerate(valves_list):
                    valve, state = valve_state
                    test_machine.set_valve(valve, ValveState.Open if state else ValveState.Closed)
                    valves_list[idx] = [valve, not state]
            time.sleep(0.1)

    elif procedure == "wtr":
        wtr_state = True
        while True:
            with lock:
                test_machine.set_relay(Relay.WaterPump, RelayState.On if wtr_state else RelayState.Off)
                wtr_state = not wtr_state
            time.sleep(0.33)

    elif procedure == "vac":
        wtr_state = True
        while True:
            with lock:
                test_machine.set_relay(Relay.VacuumPump, RelayState.On if wtr_state else RelayState.Off)
                wtr_state = not wtr_state
            time.sleep(0.6)


def start_lol_threads(test_machine: EnbioWiFiMachine):
    """ Dont ask why """
    lock = threading.Lock()

    procedures = ["door", "valves", "wtr", "vac"]

    threads: list[threading.Thread] = []

    for procedure in procedures:
        thread = threading.Thread(target=thread_procedure, args=(procedure, test_machine, lock))
        threads.append(thread)
        thread.start()

    for thread in threads:
        thread.join()

    print("lol done")


if __name__ == '__main__':
    machine = EnbioWiFiMachine()
    start_lol_threads(machine)

    # machine.write_int_register(ModbusRegister.PUMP_WTR_INTERVAL.value, 300)
    # print(f"Water pump: {machine.read_int_register(ModbusRegister.PUMP_WTR_ON_TIME.value)}/"
    #       f"{machine.read_int_register(ModbusRegister.PUMP_WTR_INTERVAL.value)}")
    #
    # machine.write_int_register(ModbusRegister.PUMP_WTR_ON_TIME.value, 22)
    #
    # time.sleep(4)
    # machine.write_int_register(ModbusRegister.PUMP_WTR_ON_TIME.value, 0)

#
#     enbio_device.set_standby_cooling_thrsh_tmpr(20)

#     new_device_id = "STW02-XX-24-99999"
#     tool.set_device_id(new_device_id)
#     device_id = tool.get_device_id()
#
#     assert device_id == new_device_id
#
#     # current_datetime = datetime.now()
#     # print("Current datetime:", current_datetime)
#     #
#     # specific_datetime = datetime(2024, 11, 5, 14, 30)  # November 5, 2024, 2:30 PM
#     # print("Specific datetime:", specific_datetime)
#     #
#     # # Subtract the datetimes to get a timedelta object
#     # time_difference = current_datetime - specific_datetime
#     #
#     # # Get the difference in seconds
#     # difference_in_seconds = abs(time_difference.total_seconds())
#     # print("Difference in seconds:", difference_in_seconds)
#
#     # tool = ModbusTool(port=None)
#     #
#     # try:
#     #     tool.door_drv_fwd()
#     # except Exception as e:
#     #     tool.door_drv_none()
#     #     print(e)
