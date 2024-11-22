from enum import Enum
import time
import struct
import minimalmodbus
from dataclasses import dataclass, asdict
import json

cfg = {
    "serial_timeout": 2.5,
    "serial_port": 115200,
}


def ints_to_float(low, high):
    """Convert a tuple of two 16-bit integers to a float."""
    int_value = (low << 16) | high
    packed_value = struct.pack(">I", int_value)  # ">I" for big-endian 32-bit unsigned integer
    return struct.unpack(">f", packed_value)[0]  # ">f" for big-endian 32-bit float


def float_to_ints(float_value):
    """Convert a float to a tuple of two 16-bit integers."""
    packed_value = struct.pack(">f", float_value)  # ">f" for big-endian 32-bit float
    int_value = struct.unpack(">I", packed_value)[0]  # ">I" for big-endian 32-bit unsigned integer
    low = (int_value >> 16) & 0xFFFF
    high = int_value & 0xFFFF
    return low, high


def await_value(function, value, timeout: [float | None] = None) -> bool:
    start_time = time.time()
    while True:
        if function() == value:
            return True
        if timeout is not None and (time.time() - start_time) > timeout:
            return False

        time.sleep(0.25)


def read_float_register(device: minimalmodbus.Instrument, register):
    low, high = device.read_registers(register, 2)

    int_value = low << 16 | high
    assert 0 <= int_value <= 0xFFFFFFFF

    packed_value = struct.pack(">I", int_value)  # ">I" for big-endian 32-bit unsigned integer

    float_value = struct.unpack(">f", packed_value)[0]  # ">f" for big-endian 32-bit float

    return float_value


class ProcessType(Enum):
    P134 = 1
    P134FAST = 2
    P121 = 3
    PRION = 4
    TVAC = 5
    THELIX = 6


@dataclass
class DOState:
    proc_type: None | ProcessType
    sg_heaters_double: bool
    ch_heaters: bool
    pump_vac: bool
    pump_water: bool
    v1_open: bool
    v2_open: bool
    v3_open: bool
    v5_open: bool
    sg_heater_single: bool

    @staticmethod
    def from_bitfields(raw_value: int) -> "DOState":
        proc_value = (raw_value & 0xF000) >> 12
        proc_type = get_process_type_by_value(proc_value)

        do_state = DOState(
            proc_type=proc_type,
            sg_heaters_double=raw_value & (1 << 0) > 0,
            ch_heaters=raw_value & (1 << 1) > 0,
            pump_vac=raw_value & (1 << 2) > 0,
            pump_water=raw_value & (1 << 3) > 0,
            v1_open=raw_value & (1 << 4) > 0,
            v2_open=raw_value & (1 << 5) > 0,
            v3_open=raw_value & (1 << 6) > 0,
            v5_open=raw_value & (1 << 7) > 0,
            sg_heater_single=raw_value & (1 << 8) > 0,
        )
        return do_state


class Relay(Enum):
    SteamgenDouble = 0
    Chamber = 1
    VacuumPump = 2
    WaterPump = 3
    Valve1 = 4
    Valve2 = 5
    Valve3 = 6
    Valve5 = 7
    SteamgenSingle = 11


class ValveState(Enum):
    Auto = 0
    Open = 1
    Closed = 2


class RelayState(Enum):
    Auto = 0
    On = 1
    Off = 2


class ScreenId(Enum):
    MAIN = 0


process_labels = ["121", "134", "134f", "prion", "tvac", "thelix"]


label_to_process_type = {
    "121": ProcessType.P121,
    "134": ProcessType.P134,
    "134f": ProcessType.P134FAST,
    "prion": ProcessType.PRION,
    "tvac": ProcessType.TVAC,
    "thelix": ProcessType.THELIX,
}


process_type_values = {
    ProcessType.P121: 3,
    ProcessType.P134: 4,
    ProcessType.P134FAST: 7,
    ProcessType.PRION: 9,
    ProcessType.TVAC: 6,
    ProcessType.THELIX: 5,
}

reverse_process_type_values = {value: key for key, value in process_type_values.items()}


def get_process_type_by_value(value):
    return reverse_process_type_values.get(value, None)


class EnbioDeviceInternalException(Exception):
    """Custom exception for Enbio device specific internal errors."""
    def __init__(self, message):
        super().__init__(message)


@dataclass
class PWRState:
    ptrn: int
    ch_pwr: float
    ch_tar: float
    sg_pwr: float
    sg_tar: float


@dataclass
class SensorsMeasurements:
    p_proc: float
    p_ext: float
    t_proc: float
    t_chmbr: float
    t_stmgn: float
    t_ext: float


@dataclass
class ProcessLine:
    sec: int
    phase: int

    pwr_state: PWRState
    do_state: DOState
    sensors_msrs: SensorsMeasurements


@dataclass
class ScaleFactor:
    a: float
    b: float

    def to_json(self):
        return json.dumps(asdict(self))

    def equals(self, other: "ScaleFactor", precision: int = 3) -> bool:
        """Check if two ScaleFactor instances are equal up to a given decimal precision."""
        return (
                round(self.a, precision) == round(other.a, precision) and
                round(self.b, precision) == round(other.b, precision)
        )


@dataclass
class ScaleFactors:
    pressure_process: ScaleFactor
    temperature_process: ScaleFactor
    temperature_chamber: ScaleFactor
    temperature_steamgen: ScaleFactor

    def to_json(self, pretty: bool = True):
        return json.dumps(asdict(self), indent=4 if pretty else None)

    @staticmethod
    def from_json(json_data: str) -> "ScaleFactors":
        """Deserialize a JSON string to a ScaleFactors object."""
        data = json.loads(json_data)
        return ScaleFactors(
            pressure_process=ScaleFactor(**data['pressure_process']),
            temperature_process=ScaleFactor(**data['temperature_process']),
            temperature_chamber=ScaleFactor(**data['temperature_chamber']),
            temperature_steamgen=ScaleFactor(**data['temperature_steamgen']),
        )

    def equals(self, other: "ScaleFactors", precision: int = 3) -> bool:
        """Check if two ScaleFactors instances are equal up to a given decimal precision."""
        return (
                self.pressure_process.equals(other.pressure_process, precision) and
                self.temperature_process.equals(other.temperature_process, precision) and
                self.temperature_chamber.equals(other.temperature_chamber, precision) and
                self.temperature_steamgen.equals(other.temperature_steamgen, precision)
        )
