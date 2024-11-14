import time
import struct
import minimalmodbus
import serial.tools.list_ports
from datetime import datetime
# from .proc_runner import ProcRunner
from .common import ProcessType, label_to_process_type, ProcessLine, EnbioDeviceInternalException, float_to_ints, \
    ints_to_float, cfg, process_type_values, ScreenId, ScaleFactors, ScaleFactor, Relay, RelayState, ValveState
from .modbus_registers import ModbusRegister


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
            time.sleep(3)

            self._device.write_register(ModbusRegister.CHANGE_SCREEN.value, ScreenId.MAIN.value)
            for _ in range(0, 50):
                print(f"screen {self._device.read_register(ModbusRegister.CHANGE_SCREEN.value)}")
                time.sleep(0.5)
            # self._write_reg_feedback(ModbusRegister.CHANGE_SCREEN.value, ScreenId.MAIN.value, await_time=1)

    def poll_process_line(self) -> ProcessLine:
        valves_and_relays = self._device.read_register(ModbusRegister.VALVES_AND_RELAYS.value)

        return ProcessLine(
            sec=self._device.read_register(ModbusRegister.PROC_SECONDS.value),
            phase=self._device.read_register(ModbusRegister.PROC_PHASE.value),

            ptrn=self._device.read_register(ModbusRegister.PWR_CTRL_PATTERN.value),
            ch_pwr=self._device.read_register(ModbusRegister.PWR_CH_DRV_MONITOR.value),
            ch_tar=self._device.read_register(ModbusRegister.PWR_CH_TARGET.value),
            sg_pwr=self._device.read_register(ModbusRegister.PWR_SG_CTRL.value),
            sg_tar=self._device.read_register(ModbusRegister.PWR_SG_DRV_MONITOR.value),

            p_proc=round(self._read_float_register(ModbusRegister.PRESSURE_PROCESS.value), 3),
            t_proc=round(self._read_float_register(ModbusRegister.TEMPERATURE_PROCESS.value), 3),
            t_chmbr=round(self._read_float_register(ModbusRegister.TEMPERATURE_CHAMBER.value), 3),
            t_stmgn=round(self._read_float_register(ModbusRegister.TEMPERATURE_STEAMGEN.value), 3),

            v1=valves_and_relays & (1 << 0) > 0,
            v2=valves_and_relays & (1 << 1) > 0,
            v3=valves_and_relays & (1 << 2) > 0,
            v5=valves_and_relays & (1 << 3) > 0,

            pvac=valves_and_relays & (1 << 4) > 0,
            pwtr=valves_and_relays & (1 << 5) > 0,

            ch_ab=valves_and_relays & (1 << 6) > 0,
            sg_a=valves_and_relays & (1 << 7) > 0,
            sg_b=valves_and_relays & (1 << 8) > 0,
            sg_c=valves_and_relays & (1 << 9) > 0,
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
        if sensor == "process":
            return self._read_float_register(ModbusRegister.ADCF_TMPR_PROCESS.value)
        if sensor == "chamber":
            return self._read_float_register(ModbusRegister.ADCF_TMPR_CHAMBER.value)
        if sensor == "steamgen":
            return self._read_float_register(ModbusRegister.ADCF_TMPR_STEAMGE.value)
        raise ValueError("Bad 'sensor' argument")

    def runmonitor(self, proces_name: str) -> None:
        pass
        # proc_runner = ProcRunner(self._device)
        # proc_runner.start(label_to_process_type.get(proces_name))
        #
        # try:
        #     while True:
        #         time.sleep(1)
        #         print(proc_runner.poll_progress())
        # except KeyboardInterrupt as e:
        #     print("Interrupting...")
        #     proc_runner.interrupt()
        #     raise e

    def monitor(self) -> None:
        pass
        # proc_runner = ProcRunner(self._device)
        #
        # try:
        #     while True:
        #         time.sleep(1)
        #         print(proc_runner.poll_progress())
        # except KeyboardInterrupt as e:
        #     print("Stopping...")
        #     raise e


    def get_phase_id(self) -> int:
        return self._device.read_register(ModbusRegister.PROC_PHASE.value)


# if __name__ == '__main__':
#     enbio_device = EnbioDevice()
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
