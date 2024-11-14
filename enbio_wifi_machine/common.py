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


class EnbioDeviceInternalException(Exception):
    """Custom exception for Enbio device specific internal errors."""
    def __init__(self, message):
        super().__init__(message)


@dataclass
class ProcessLine:
    sec: int
    phase: int

    ptrn: int
    ch_pwr: float
    ch_tar: float
    sg_pwr: float
    sg_tar: float

    p_proc: float
    t_proc: float
    t_chmbr: float
    t_stmgn: float

    v1: bool
    v2: bool
    v3: bool
    v5: bool

    pvac: bool
    pwtr: bool

    ch_ab: bool
    sg_a: bool
    sg_b: bool
    sg_c: bool


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
