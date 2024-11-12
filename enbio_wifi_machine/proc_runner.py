import time
import minimalmodbus
import serial.tools.list_ports
from enum import Enum
from datetime import datetime
from .common import ProcessType, ProcessLine, read_float_register, process_type_values, \
    EnbioDeviceInternalException

from .modbus_registers import ModbusRegister


class ProcRunner:
    def __init__(self, device: minimalmodbus.Instrument):
        self._device = device
        self.selected_process = None

    # todo use Machine's functions
    def _write_ctrl_reg_feedback(self, register, await_time: float = 0.1):
        activating_value = 1
        success_value = 0
        print(f"_write_ctrl_reg_feedback {register} -> {activating_value}")
        self._device.write_register(register, activating_value)
        time.sleep(await_time)

        feedback_value = self._device.read_register(register)
        print(f"_write_ctrl_reg_feedback {register} <- {feedback_value}")

        # Check if the value is as expected
        if feedback_value != success_value:
            raise EnbioDeviceInternalException(
                f"Error: Expected value {activating_value}, but got {feedback_value}")

    def start(self, process_type: ProcessType) -> None:
        if self._device.read_register(ModbusRegister.PROC_STATUS.value) == 1:
            raise EnbioDeviceInternalException("Process already running")

        print("Start")
        self.selected_process = process_type

        self._device.write_register(ModbusRegister.PROC_SELECT_START.value, process_type_values[process_type])
        time.sleep(0.1)
        self._write_ctrl_reg_feedback(ModbusRegister.PROC_SELECT_START.value)

    def interrupt(self) -> None:
        if self._device.read_register(ModbusRegister.PROC_STATUS.value) == 1:
            print("interrupt")
            self.selected_process = None
            self._device.write_register(ModbusRegister.PROC_SELECT_START.value, 0xFFFF)

    def poll_progress(self) -> ProcessLine:
        valves_and_relays = self._device.read_register(ModbusRegister.VALVES_AND_RELAYS.value)

        # todo move to Machine
        return ProcessLine(
            sec=self._device.read_register(ModbusRegister.PROC_SECONDS.value),
            phase=self._device.read_register(ModbusRegister.PROC_PHASE.value),

            ptrn=self._device.read_register(ModbusRegister.PWR_CTRL_PATTERN.value),
            ch_pwr=self._device.read_register(ModbusRegister.PWR_CH_DRV_MONITOR.value),
            ch_tar=self._device.read_register(ModbusRegister.PWR_CH_TARGET.value),
            sg_pwr=self._device.read_register(ModbusRegister.PWR_SG_CTRL.value),
            sg_tar=self._device.read_register(ModbusRegister.PWR_SG_DRV_MONITOR.value),

            p_proc=round(read_float_register(self._device, ModbusRegister.PRESSURE_PROCESS.value), 3),
            t_proc=round(read_float_register(self._device, ModbusRegister.TEMPERATURE_PROCESS.value), 3),
            t_chmbr=round(read_float_register(self._device, ModbusRegister.TEMPERATURE_CHAMBER.value), 3),
            t_stmgn=round(read_float_register(self._device, ModbusRegister.TEMPERATURE_STEAMGEN.value), 3),

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
