from enum import Enum


class ModbusRegister(Enum):
    PROC_PHASE = 4
    FIRMWARE_VERSION = 5
    DIP_SWITCH = 164
    DEVICE_ID = 1024
    SAVE_ALL = 76
    SAVE_ALL_SERIALNUM = 77  # Legacy
    SAVE_ALL_ISAVEPARAMS = 118  # Legacy
    DOOR_UNLOCKED = 1531
    DOOR_OPEN = 1528
    COIL_CONTROL = 40
    BOARD_NUM = 512
    PROC_SELECT_START = 95

    EXECUTION_COUNTER = 65

    # SERVICE_COUNTER = 64 TODO
    # HEPA_FILTER_COUNTER = 62 TODO
    # SEND_REPORT_ENABLE = 130 TODO
    # RESET_ONE_YEAR_COUNTER = 239 TODO
    # CLEAR_ERR_HISTORY = 152 TODO

    DATETIME_GET_YEAR = 1512     # Read only
    DATETIME_GET_MONTH = 1513    # Read only
    DATETIME_GET_DAY = 1514      # Read only
    DATETIME_GET_HOUR = 1515     # Read only
    DATETIME_GET_MINUTE = 1516   # Read only
    DATETIME_GET_SECOND = 1517   # Read only
    DATETIME_GET_SET_DAY = 111
    DATETIME_GET_SET_MONTH = 112
    DATETIME_GET_SET_YEAR = 113
    DATETIME_GET_SET_HOUR = 114
    DATETIME_GET_SET_MINUTE = 115
    DATETIME_SAVE = 116

    SCALE_FACTORS_PRESS_PROC_A = 514
    SCALE_FACTORS_TMPR_PROC_A = 516
    SCALE_FACTORS_TMPR_CHMBR_A = 518
    SCALE_FACTORS_TMPR_SG_A = 520
    SCALE_FACTORS_PRESS_PROC_B = 526
    SCALE_FACTORS_TMPR_PROC_B = 528
    SCALE_FACTORS_TMPR_CHMBR_B = 530
    SCALE_FACTORS_TMPR_SG_B = 532

    PRESSURE_PROCESS = 562
    TEMPERATURE_PROCESS = 564
    TEMPERATURE_CHAMBER = 566
    TEMPERATURE_STEAMGEN = 568
    ATMOSPHERIC_PRESSURE = 576

    ADCF_TMPR_PROCESS = 552 #TODO ADC AS FLOAT
    ADCF_TMPR_CHAMBER = 554
    ADCF_TMPR_STEAMGE = 556

    STANDBY_COOLING_THRSH = 223

    RELAY_STEAMGEN_AB = 1519
    RELAY_CHAMBER_AB = 1520
    RELAY_PUMP_VACUUM = 1521
    RELAY_PUMP_WATER = 1522
    VALVE1 = 1523
    VALVE2 = 1524
    VALVE3 = 1525
    VALVE5 = 1526
    RELAY_STEAMGEN_C = 1551

    # Extension
    TEST_FLOAT = 3490
    TEST_INT = 3492
    STM_REBOOT = 3499
    PROC_STATUS = 3502
    PROC_SECONDS = 3500

    PWR_CTRL_PATTERN = 3493
    PWR_CH_CTRL = 3494
    PWR_CH_DRV_MONITOR = 3504
    PWR_CH_TARGET = 3495
    PWR_SG_CTRL = 3496
    PWR_SG_TARGET = 3497
    PWR_SG_DRV_MONITOR = 3505

    VALVES_AND_RELAYS = 3503
