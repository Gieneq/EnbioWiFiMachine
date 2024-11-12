# Enbio WiFI Machine

Abstraction for Enbio WiFi Sterilizer Modbus registers

## Usage

Install 
```shell
pip install -e .
```

Run CLI:
```shell
enbio_wifi_machine --help
```


download todo

install todo

module todo

## CLI

Todo

## Registers

In [enbio_wifi_machine/modbus_registers.py](enbio_wifi_machine/modbus_registers.py) there is ModbusRegister for all types registers: 16b, 32b and strings.
Starting from register address 3400 there are new registers.

| Enums Label            | Register | Legacy      | R/W | Description                                                                          |
|------------------------|----------|-------------|-----|--------------------------------------------------------------------------------------|
| `PROC_PHASE`           | 4u       | ✅ Coherent  | R/- | During proces values 0-12. During test values 0-5.                                   |
| `FIRMWARE_VERSION`     | 5u       | ❓ Reclaimed | R/- | Pattern of bit fields: major.minor.patch, <7:0-127>.<5:0-31>.<4:0-15>  exmaple 7.5.4 |
| `DIP_SWITCH`           | 164u     | ✅ Coherent  | R/- | Get value of onboard dip switch                                                      |
| `DEVICE_ID`            | 1024u    | ✅ Coherent  | R/W | Start of 16 registers (32 bytes) of device id (serial number)                        |
| `SAVE_ALL`             | 76u      | ✅ Coherent  | R/W | Write 1 to invoke. Read until got 0 or 0xFFFF (error)                                |
| `SAVE_ALL_SERIALNUM`   | 77u      | ✅ Coherent  | R/W | Same as `SAVE_ALL`, remains to match legacy.                                         |
| `SAVE_ALL_ISAVEPARAMS` | 118u     | ✅ Coherent  | R/W | Same as `SAVE_ALL`, remains to match legacy.                                         |
| `DOOR_UNLOCKED`        | 1531u    | ✅ Coherent  | R/- | Door unlocked (signal is High on pin). Read 0xFFFF error                             |
| `DOOR_OPEN`            | 1528u    | ✅ Coherent  | R/- | Door open (signal is High on pin). Read 0xFFFF error                                 |
| `COIL_CONTROL`         | 40u      | ✅ Coherent  | R/W | Write 0: not driven, 1: drive to unlock, 2: drive to lock. Read 0xFFFF error         |
| `BOARD_NUM`            | 512u     | ❓ Reclaimed | R/W | Pattern of bit fields: rev.yy.mm, <5:'A'-'Z'>.<7:0-99>.<4:0-12>  exmaple E.24.06     |
| `PROC_SELECT_START`    | 95u      | ✅ Coherent  | R/W | 2 Phase: write process_id, then write 1 to start. Read 0xFFFF error                  |
| `TEST_FLOAT`           | 3490f    | ❌ New       | R/W | Test read write of float                                                             |
| `TEST_INT`             | 3492u    | ❌ New       | R/W | Test read write of int                                                               |
| `STM_REBOOT`           | 3499u    | ❌ New       | -/W | Restart system                                                                       |
| `xx`                   | 0        | ?           | -/- | xxxx                                                                                 |

## Functions


| Function                    | Description                                                        |
|-----------------------------|--------------------------------------------------------------------|
| `get_device_id`             | Return device id called serial number                              |
| `set_device_id`             | Sets device id called serial number. Need to be saved to FLASH before power off. |
| `is_door_open`              | Teturns true if door is open.                                      |
| `is_door_unlocked`          | 0000                                                               |
| `door_drv_fwd`              | 0000                                                               |
| `door_drv_bwd`              | 0000                                                               |
| `door_drv_none`             | 0000                                                               |
| `door_lock_with_feedback`   | 0000                                                               |
| `door_unlock_with_feedback` | 0000                                                               |
| `get_test_int`              | 0000                                                               |
| `set_test_int`              | 0000                                                               |
| `get_firmware_version`      | 0000                                                               |
| `get_boardnumber`           | 0000                                                               |
| `set_boardnumber`           | 0000                                                               |
| `get_datetime`              | 0000                                                               |
| `set_datetime`              | 0000                                                               |
| `get_dpi_switch`            | 0000                                                               |
| `get_standby_cooling_thrsh_tmpr` | 0000                                                               |
| `set_standby_cooling_thrsh_tmpr` | 0000                                                               |
| `get_process_counter`       | 0000                                                               |
| `save_all`     | 0000                                                               |
| `reboot`                       | 0000                                                               |
| `runmonitor`                       | 0000                                                               |
| `monitor`                       | 0000                                                               |
| `get_phase_id`                       | 0000                                                               |
| `xxx`                       | 0000                                                               |
