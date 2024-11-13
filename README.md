# Enbio WiFI Machine

Abstraction for Enbio WiFi Sterilizer Modbus registers

## Usage

### 1. Download the Repository
```shell
git clone https://github.com/Gieneq/EnbioWiFiMachine.git
cd EnbioWiFiMachine
```

### 2. Create a Virtual Environment
```shell
python3 venv venv
venv\Scripts\Activate
```
If you encounter issues with script execution, set the PowerShell execution policy:
```shell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope Process
```

### 3. Install
To install the package in editable mode:
```shell
pip install -e .
```

### 4. Check Installation
Verify the installation by running the CLI tool’s help command:
```shell
enbio_wifi_machine --help
```

## CLI

Todo

## Module

Todo

## Registers

In [enbio_wifi_machine/modbus_registers.py](enbio_wifi_machine/modbus_registers.py) there is enum ModbusRegister for all types registers: 16b, 32b and strings.
Starting from register address 3400 there are new registers.

### Process ID 
| Process ID | Value |
|------------|-------|
| P121       | 3     |
| P134       | 4     |
| P134FAST   | 7     |
| PRION      | 9     |
| TVAC       | 6     |
| THELIX     | 5     |

### Process or Test Phase
| Process Phase ID           | Value |
|----------------------------|-------|
| Init                       | 0     |
| Preheat                    | 1     |
| MakeVacuum1                | 2     |
| Pressurize1                | 3     |
| MakeVacuum2                | 4     |
| Pressurize2                | 5     |
| MakeVacuum3                | 6     |
| Pressurize3, Equalibration | 7     |
| Sterylization              | 8     |
| Depressurize               | 9     |
| Drying                     | 10    |
| Equalizing                 | 11    |
| Ending                     | 12    |

| Vecuum Test Phase ID | Value |
|----------------------|-------|
| Init                 | 0     |
| MakeVacuum           | 1     |
| Stabilizing          | 2     |
| Testing              | 3     |
| Equalizing           | 4     |
| Ending               | 5     |


| Enums Label                  | Register | Legacy      | R/W | Tested | Description                                                                                          |
|------------------------------|----------|-------------|-----|--------|------------------------------------------------------------------------------------------------------|
| `PROC_PHASE`                 | 4u       | ✅ Coherent  | R/- |        | During proces values: 0-12. During test values: 0-5.                                                 |
| `FIRMWARE_VERSION`           | 5u       | ❓ Reclaimed | R/- | y      | Pattern of bit fields: major.minor.patch, <7:0-127>.<5:0-31>.<4:0-15>  exmaple 7.5.4                 |
| `DIP_SWITCH`                 | 164u     | ✅ Coherent  | R/- | y      | Get value of onboard dip switch, 4 bit flags.                                                        |
| `DEVICE_ID`                  | 1024u    | ✅ Coherent  | R/W | y      | Start of 16 registers (32 bytes) of device id (serial number).                                       |
| `SAVE_ALL`                   | 76u      | ✅ Coherent  | R/W | y      | Write 1 to invoke saving. Read until got 0 or 0xFFFF (error).                                        |
| `SAVE_ALL_SERIALNUM`         | 77u      | ✅ Coherent  | R/W | y      | Same as `SAVE_ALL`, remains to match legacy.                                                         |
| `SAVE_ALL_ISAVEPARAMS`       | 118u     | ✅ Coherent  | R/W | y      | Same as `SAVE_ALL`, remains to match legacy.                                                         |
| `DOOR_UNLOCKED`              | 1531u    | ✅ Coherent  | R/- | y      | Door unlocked = signal is High on pin. Read 0xFFFF error.                                            |
| `DOOR_OPEN`                  | 1528u    | ✅ Coherent  | R/- | y      | Door open = signal is High on pin. Read 0xFFFF error.                                                |
| `COIL_CONTROL`               | 40u      | ✅ Coherent  | R/W | y      | Write 0: not driven, 1: drive to unlock, 2: drive to lock. Read previously set value or 0xFFFF error |
| `BOARD_NUM`                  | 512u     | ❓ Reclaimed | R/W | y      | Pattern of bit fields: rev.yy.mm, <5:'A'-'Z'>.<7:0-99>.<4:0-12>  example E.24.06                     |
| `PROC_SELECT_START`          | 95u      | ✅ Coherent  | R/W | y      | 2 Phase: write process_id, then write 1 to start. Read 0xFFFF error                                  |
| `EXECUTION_COUNTER`          | 65u      | ✅ Coherent  | R/W | y      | Read done processes/test count. Write 0 clears logs and resets counter.                              |
| `SERVICE_COUNTER`            | 64u      | ✅ Coherent  | -/- |        | TODO                                                                                                 |
| `HEPA_FILTER_COUNTER`        | 62u      | ✅ Coherent  | -/- |        | TODO                                                                                                 |
| `SEND_REPORT_ENABLE`         | 130u     | ✅ Coherent  | -/- |        | TODO                                                                                                 |
| `RESET_ONE_YEAR_COUNTER`     | 239u     | ✅ Coherent  | -/- |        | TODO                                                                                                 |
| `CLEAR_ERR_HISTORY`          | 152u     | ✅ Coherent  | -/- |        | TODO                                                                                                 |
| `DATETIME_GET_YEAR`          | 1512u    | ✅ Coherent  | -/- | y      | Read only year value 2000-2099                                                                       |
| `DATETIME_GET_MONTH`         | 1513u    | ✅ Coherent  | -/- | y      | Read only month value: 1-12                                                                          |
| `DATETIME_GET_DAY`           | 1514u    | ✅ Coherent  | -/- | y      | Read only day value: 1-31                                                                            |
| `DATETIME_GET_HOUR`          | 1515u    | ✅ Coherent  | -/- | y      | Read only hour value: 0-24                                                                           |
| `DATETIME_GET_MINUTE`        | 1516u    | ✅ Coherent  | -/- | y      | Read only minute value: 0-60                                                                         |
| `DATETIME_GET_SECOND`        | 1517u    | ✅ Coherent  | -/- | y      | Read only second value: 0-60. Save time clears second to 0.                                          |
| `DATETIME_SET_DAY`           | 111u     | ✅ Coherent  | -/- | y      | Read, write day value: 1-31                                                                          |
| `DATETIME_SET_MONTH`         | 112u     | ✅ Coherent  | -/- | y      | Read, write month value: 1-12                                                                        |
| `DATETIME_SET_YEAR`          | 113u     | ✅ Coherent  | -/- | y      | Read, write year value 2000-2099                                                                     |
| `DATETIME_SET_HOUR`          | 114u     | ✅ Coherent  | -/- | y      | Read, write hour value: 0-24                                                                         |
| `DATETIME_SET_MINUTE`        | 115u     | ✅ Coherent  | -/- | y      | Read, write minute value: 0-60                                                                       |
| `DATETIME_SAVE`              | 116u     | ✅ Coherent  | -/- | y      | Saves time to RTC domain, clearing seconds.                                                          |
| `SCALE_FACTORS_PRESS_PROC_A` | 514f     | ✅ Coherent  | -/- |        | xxxx                                                                                                 |
| `SCALE_FACTORS_TMPR_PROC_A`  | 516f     | ✅ Coherent  | -/- |        | xxxx                                                                                                 |
| `SCALE_FACTORS_TMPR_CHMBR_A` | 518f     | ✅ Coherent  | -/- |        | xxxx                                                                                                 |
| `SCALE_FACTORS_TMPR_SG_A`    | 520f     | ✅ Coherent  | -/- |        | xxxx                                                                                                 |
| `SCALE_FACTORS_PRESS_PROC_B` | 526f     | ✅ Coherent  | -/- |        | xxxx                                                                                                 |
| `SCALE_FACTORS_TMPR_PROC_B`  | 528f     | ✅ Coherent  | -/- |        | xxxx                                                                                                 |
| `SCALE_FACTORS_TMPR_CHMBR_B` | 530f     | ✅ Coherent  | -/- |        | xxxx                                                                                                 |
| `SCALE_FACTORS_TMPR_SG_B`    | 532f     | ✅ Coherent  | -/- |        | xxxx                                                                                                 |
| `PRESSURE_PROCESS`           | 562f     | ✅ Coherent  | -/- |        | xxxx                                                                                                 |
| `TEMPERATURE_PROCESS`        | 564f     | ✅ Coherent  | -/- |        | xxxx                                                                                                 |
| `TEMPERATURE_CHAMBER`        | 566f     | ✅ Coherent  | -/- |        | xxxx                                                                                                 |
| `TEMPERATURE_STEAMGEN`       | 568f     | ✅ Coherent  | -/- |        | xxxx                                                                                                 |
| `ATMOSPHERIC_PRESSURE`       | 576f     | ✅ Coherent  | -/- |        | xxxx                                                                                                 |
| `ADCF_TMPR_PROCESS`          | 552f     | ✅ Coherent  | -/- |        | xxxx                                                                                                 |
| `ADCF_TMPR_CHAMBER`          | 554f     | ✅ Coherent  | -/- |        | xxxx                                                                                                 |
| `ADCF_TMPR_STEAMGE`          | 556f     | ✅ Coherent  | -/- |        | xxxx                                                                                                 |
| `STANDBY_COOLING_THRSH`      | 223u     | ✅ Coherent  | -/- |        | xxxx                                                                                                 |
| `RELAY_STEAMGEN_AB`          | 1519u    | ✅ Coherent  | -/- |        | xxxx                                                                                                 |
| `RELAY_CHAMBER_AB`           | 1520u    | ✅ Coherent  | -/- |        | xxxx                                                                                                 |
| `RELAY_PUMP_VACUUM`          | 1521u    | ✅ Coherent  | -/- |        | xxxx                                                                                                 |
| `RELAY_PUMP_WATER`           | 1522u    | ✅ Coherent  | -/- |        | xxxx                                                                                                 |
| `VALVE1`                     | 1523u    | ✅ Coherent  | -/- |        | xxxx                                                                                                 |
| `VALVE2`                     | 1524u    | ✅ Coherent  | -/- |        | xxxx                                                                                                 |
| `VALVE3`                     | 1525u    | ✅ Coherent  | -/- |        | xxxx                                                                                                 |
| `VALVE5`                     | 1526u    | ✅ Coherent  | -/- |        | xxxx                                                                                                 |
| `RELAY_STEAMGEN_C`           | 1551u    | ✅ Coherent  | -/- |        | xxxx                                                                                                 |
| `TEST_FLOAT`                 | 3490f    | ❌ New       | R/W | y      | Test read write of float                                                                             |
| `TEST_INT`                   | 3492u    | ❌ New       | R/W | y      | Test read write of int                                                                               |
| `STM_REBOOT`                 | 3499u    | ❌ New       | -/W | y      | Restart system                                                                                       |
| `PWR_CTRL_PATTERN`           | 0        | ?           | -/- |        | xxxx                                                                                                 |
| `PWR_CH_CTRL`                | 0        | ?           | -/- |        | xxxx                                                                                                 |
| `PWR_CH_DRV_MONITOR`         | 0        | ?           | -/- |        | xxxx                                                                                                 |
| `PWR_CH_TARGET`              | 0        | ?           | -/- |        | xxxx                                                                                                 |
| `PWR_SG_CTRL`                | 0        | ?           | -/- |        | xxxx                                                                                                 |
| `PWR_SG_TARGET`              | 0        | ?           | -/- |        | xxxx                                                                                                 |
| `PWR_SG_DRV_MONITOR`         | 0        | ?           | -/- |        | xxxx                                                                                                 |
| `VALVES_AND_RELAYS`          | 0        | ?           | -/- |        | xxxx                                                                                                 |
| `CHANGE_SCREEN`              | 3550     | ❌ New       | R/W | y      | Change screenn, not all transitions supported                                                        |
| `xx`                         | 0        | ?           | -/- |        | xxxx                                                                                                 |
| `xx`                         | 0        | ?           | -/- |        | xxxx                                                                                                 |
| `xx`                         | 0        | ?           | -/- |        | xxxx                                                                                                 |
| `xx`                         | 0        | ?           | -/- |        | xxxx                                                                                                 |
| `xx`                         | 0        | ?           | -/- |        | xxxx                                                                                                 |
| `xx`                         | 0        | ?           | -/- |        | xxxx                                                                                                 |
| `xx`                         | 0        | ?           | -/- |        | xxxx                                                                                                 |
| `xx`                         | 0        | ?           | -/- |        | xxxx                                                                                                 |
| `xx`                         | 0        | ?           | -/- |        | xxxx                                                                                                 |
| `xx`                         | 0        | ?           | -/- |        | xxxx                                                                                                 |

## Functions


| Function                         | Description                                                                      |
|----------------------------------|----------------------------------------------------------------------------------|
| `get_device_id`                  | Return device id called serial number                                            |
| `set_device_id`                  | Sets device id called serial number. Need to be saved to FLASH before power off. |
| `is_door_open`                   | Teturns true if door is open.                                                    |
| `is_door_unlocked`               | 0000                                                                             |
| `door_drv_fwd`                   | 0000                                                                             |
| `door_drv_bwd`                   | 0000                                                                             |
| `door_drv_none`                  | 0000                                                                             |
| `door_lock_with_feedback`        | 0000                                                                             |
| `door_unlock_with_feedback`      | 0000                                                                             |
| `get_test_int`                   | 0000                                                                             |
| `set_test_int`                   | 0000                                                                             |
| `get_firmware_version`           | 0000                                                                             |
| `get_boardnumber`                | 0000                                                                             |
| `set_boardnumber`                | 0000                                                                             |
| `get_datetime`                   | 0000                                                                             |
| `set_datetime`                   | 0000                                                                             |
| `get_dpi_switch`                 | 0000                                                                             |
| `get_standby_cooling_thrsh_tmpr` | 0000                                                                             |
| `set_standby_cooling_thrsh_tmpr` | 0000                                                                             |
| `get_process_counter`            | 0000                                                                             |
| `save_all`                       | 0000                                                                             |
| `reboot`                         | 0000                                                                             |
| `runmonitor`                     | 0000                                                                             |
| `monitor`                        | 0000                                                                             |
| `get_phase_id`                   | 0000                                                                             |
| `xxx`                            | 0000                                                                             |

## TODOs

Places worth extra attention:
- [ ] Clearing execution processes counter