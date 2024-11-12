from enum import Enum
import time
import struct
import minimalmodbus
from dataclasses import dataclass


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
