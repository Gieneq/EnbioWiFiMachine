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

Set command used to interact with machine. The machine is detected automatically as first fond of USB serial ports.

| Command                          | Description                                                    |
|----------------------------------|----------------------------------------------------------------|
| scales get -f <destination.json> | Read scales from machine and save to destination file.         |
| scales set -f <source.json>      | Save scales from file to machine. Save to FLASH is also used.  |
| devidset <deviceid>              | Sets new deviceid (serial number)                              |
| devidget                         | Get device id.                                                 |
| saveall                          | Save all parameters.                                           |
| isdooropen                       | Check if door is locked.                                       |
| isdoorunlocked                   | Check if door is unlocked                                      |
| doorlock                         | Lock door with feedback switch.                                |
| doorunlock                       | Unlock door with feedback switch.                              |
| doordrvfwd                       | Drive door lock to lock.                                       |
| doordrvbwd                       | Drive door lock to unlock.                                     |
| doordrvnone                      | Stop driving door lock.                                        |
| dtsetnow                         | Set recent date time.                                          |
| run <process id>                 | Start process or test program. Monitor until finish or Ctrl-C. |
| monitor                          | Monitor process parameters every 1s until Ctrl-C.              |
| scales [get, set] -f <filepath>  | Manage sales factors using json file.                          |

## Module

Use `EnbioWiFiMachine` to ineract with device.

## Registers

In [enbio_wifi_machine/modbus_registers.py](enbio_wifi_machine/modbus_registers.py) there is enum ModbusRegister for all types registers: 16b, 32b and strings.
Starting from register address 3400 there are new registers.

### 3 States control

Valves and Relays with digital outputs can be driven using 3 states:

| State | Value |
|-------|-------|
| Auto  | 0     |
| On    | 1     |
| Off   | 2     |

Actually water pump uses hardware timer with variable on_time and interval. Used internally or via extension registers.

### DO State

DO State consist of [Process ID](###Process ID) currently executed and bit fields representing digital outputs.

| Bits    | Description             | Value      |
|---------|-------------------------|------------|
| 15..12  | Process ID              | Process ID |
| 11      | reserved                |            |
| 10      | reserved                |            |
| 9       | reserved                |            |
| 8       | Steamgen heater single  | 1=On       |
| 7       | Valve 5                 | 1=Open     |
| 6       | Valve 3                 | 1=Open     |
| 5       | Valve 2                 | 1=Open     |
| 4       | Valve 1                 | 1=Open     |
| 3       | Water pump (?)          | 1=On       |
| 2       | Vacuum pump             | 1=On       |
| 1       | Chamber heaters         | 1=On       |
| 0       | Steamgen heaters double | 1=On       |

(?) Water pump is driven using PWM. This value means if pumping pattern is activated. It is not if at this time pump is working.

### Process ID

| Process ID | Value |
|------------|-------|
| P121       | 3     |
| P134       | 4     |
| P134FAST   | 7     |
| PRION      | 9     |
| TVAC       | 6     |
| THELIX     | 5     |

### Heating patterns

In PWR pattern value bit0=1 menas forced.

| Pattern             | Value     |
|---------------------|-----------|
| NONE                | 0         |
| CONST_CH2_SG1       | 1<<2 = 4  |
| VARONTIME_CH2_SG1   | 2<<2 = 8  |
| VARONTIME_SG3       | 3<<2 = 12 |
| VARONTIME_ADAPTIVE  | 4<<2 = 16 |
| VARINTERVAL_CH2_SG1 | 5<<2 = 20 |

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


| Enums Label                   | Register | Legacy      | R/W | Tested | Description                                                                                          |
|-------------------------------|----------|-------------|-----|--------|------------------------------------------------------------------------------------------------------|
| `PROC_PHASE`                  | 4u       | ✅ Coherent  | R/- |        | During proces values: 0-12. During test values: 0-5.                                                 |
| `FIRMWARE_VERSION`            | 5u       | ❓ Reclaimed | R/- | y      | Pattern of bit fields: major.minor.patch, <7:0-127>.<5:0-31>.<4:0-15>  exmaple 7.5.4                 |
| `DIP_SWITCH`                  | 164u     | ✅ Coherent  | R/- | y      | Get value of onboard dip switch, 4 bit flags.                                                        |
| `DEVICE_ID`                   | 1024u    | ✅ Coherent  | R/W | y      | Start of 16 registers (32 bytes) of device id (serial number).                                       |
| `SAVE_ALL`                    | 76u      | ✅ Coherent  | R/W | y      | Write 1 to invoke saving. Read until got 0 or 0xFFFF (error).                                        |
| `SAVE_ALL_SERIALNUM`          | 77u      | ✅ Coherent  | R/W | y      | Same as `SAVE_ALL`, remains to match legacy.                                                         |
| `SAVE_ALL_ISAVEPARAMS`        | 118u     | ✅ Coherent  | R/W | y      | Same as `SAVE_ALL`, remains to match legacy.                                                         |
| `DOOR_UNLOCKED`               | 1531u    | ✅ Coherent  | R/- | y      | Door unlocked = signal is High on pin. Read 0xFFFF error.                                            |
| `DOOR_OPEN`                   | 1528u    | ✅ Coherent  | R/- | y      | Door open = signal is High on pin. Read 0xFFFF error.                                                |
| `COIL_CONTROL`                | 40u      | ✅ Coherent  | R/W | y      | Write 0: not driven, 1: drive to unlock, 2: drive to lock. Read previously set value or 0xFFFF error |
| `BOARD_NUM`                   | 512u     | ❓ Reclaimed | R/W | y      | Pattern of bit fields: rev.yy.mm, <5:'A'-'Z'>.<7:0-99>.<4:0-12>  example E.24.06                     |
| `PROC_SELECT_START`           | 95u      | ✅ Coherent  | R/W | y      | 2 Phase: write process_id, then write 1 to start. Read 0xFFFF error                                  |
| `EXECUTION_COUNTER`           | 65u      | ✅ Coherent  | R/W | y      | Read done processes/test count. Write 0 clears logs and resets counter.                              |
| `STATUS_CODE_LOWER`           | 28u      |             |     |        |                                                                                                      |
| `STATUS_CODE_HIGHER`          | 94u      |             |     |        |                                                                                                      |
| `SERVICE_COUNTER`             | 64u      | ✅ Coherent  | -/- |        | TODO                                                                                                 |
| `HEPA_FILTER_COUNTER`         | 62u      | ✅ Coherent  | -/- |        | TODO                                                                                                 |
| `SEND_REPORT_ENABLE`          | 130u     | ✅ Coherent  | -/- |        | TODO                                                                                                 |
| `RESET_ONE_YEAR_COUNTER`      | 239u     | ✅ Coherent  | -/- |        | TODO                                                                                                 |
| `CLEAR_ERR_HISTORY`           | 152u     | ✅ Coherent  | -/- |        | TODO                                                                                                 |
| `PROC_DO_STATE`               | 7u       | ✅ Coherent  | R/- | y      | Read DO State                                                                                        |
| `DATETIME_GET_YEAR`           | 1512u    | ✅ Coherent  | R/- | y      | Read only year value 2000-2099                                                                       |
| `DATETIME_GET_MONTH`          | 1513u    | ✅ Coherent  | R/- | y      | Read only month value: 1-12                                                                          |
| `DATETIME_GET_DAY`            | 1514u    | ✅ Coherent  | R/- | y      | Read only day value: 1-31                                                                            |
| `DATETIME_GET_HOUR`           | 1515u    | ✅ Coherent  | R/- | y      | Read only hour value: 0-24                                                                           |
| `DATETIME_GET_MINUTE`         | 1516u    | ✅ Coherent  | R/- | y      | Read only minute value: 0-60                                                                         |
| `DATETIME_GET_SECOND`         | 1517u    | ✅ Coherent  | R/- | y      | Read only second value: 0-60. Save time clears second to 0.                                          |
| `DATETIME_GET_SET_DAY`        | 111u     | ✅ Coherent  | R/W | y      | Read, write day value: 1-31                                                                          |
| `DATETIME_GET_SET_MONTH`      | 112u     | ✅ Coherent  | R/W | y      | Read, write month value: 1-12                                                                        |
| `DATETIME_GET_SET_YEAR`       | 113u     | ✅ Coherent  | R/W | y      | Read, write year value 2000-2099                                                                     |
| `DATETIME_GET_SET_HOUR`       | 114u     | ✅ Coherent  | R/W | y      | Read, write hour value: 0-24                                                                         |
| `DATETIME_GET_SET_MINUTE`     | 115u     | ✅ Coherent  | R/W | y      | Read, write minute value: 0-60                                                                       |
| `DATETIME_SAVE`               | 116u     | ✅ Coherent  | R/W | y      | Saves time to RTC domain, clearing seconds.                                                          |
| `SCALE_FACTORS_PRESS_PROC_A`  | 514f     | ✅ Coherent  | R/W | y      | Read/write scale factor coefficient 'a' of pressure process sensor.                                  |
| `SCALE_FACTORS_TMPR_PROC_A`   | 516f     | ✅ Coherent  | R/W | y      | Read/write scale factor coefficient 'b' of pressure process sensor.                                  |
| `SCALE_FACTORS_TMPR_CHMBR_A`  | 518f     | ✅ Coherent  | R/W | y      | Read/write scale factor coefficient 'a' of temperature process sensor.                               |
| `SCALE_FACTORS_TMPR_SG_A`     | 520f     | ✅ Coherent  | R/W | y      | Read/write scale factor coefficient 'b' of temperature process sensor.                               |
| `SCALE_FACTORS_PRESS_PROC_B`  | 526f     | ✅ Coherent  | R/W | y      | Read/write scale factor coefficient 'a' of temperature chamber sensor.                               |
| `SCALE_FACTORS_TMPR_PROC_B`   | 528f     | ✅ Coherent  | R/W | y      | Read/write scale factor coefficient 'b' of temperature chamber sensor.                               |
| `SCALE_FACTORS_TMPR_CHMBR_B`  | 530f     | ✅ Coherent  | R/W | y      | Read/write scale factor coefficient 'a' of temperature steamgen sensor.                              |
| `SCALE_FACTORS_TMPR_SG_B`     | 532f     | ✅ Coherent  | R/W | y      | Read/write scale factor coefficient 'b' of temperature steamgen sensor.                              |
| `PRESSURE_PROCESS`            | 562f     | ✅ Coherent  | R/- | y      | Chamber pressure sensor value in bar.                                                                |
| `TEMPERATURE_PROCESS`         | 564f     | ✅ Coherent  | R/- | y      | Temperature process in *C.                                                                           |
| `TEMPERATURE_CHAMBER`         | 566f     | ✅ Coherent  | R/- | y      | Temperature chamber in *C.                                                                           |
| `TEMPERATURE_STEAMGEN`        | 568f     | ✅ Coherent  | R/- | y      | Temperature steamgen in *C.                                                                          |
| `PRESSURE_RELATIVE`           | 574u     | ??          | R/- | y      | Relative pressure value in bar.                                                                      |
| `ATMOSPHERIC_PRESSURE`        | 576f     | ✅ Coherent  | R/- | y      | External pressure onboard sensor value in bar.                                                       |
| `ADCF_PRESS_PROCESS`          | 550u     | ✅ Coherent  | R/- | y      | Retrive raw ADC process pressure sensor value but converted to float (for some unknown reason).      |
| `ADCF_TMPR_PROCESS`           | 552f     | ✅ Coherent  | R/- | y      | Retrive raw ADC process temperature sensor value but converted to float (for some unknown reason).   |
| `ADCF_TMPR_CHAMBER`           | 554f     | ✅ Coherent  | R/- | y      | Retrive raw ADC chamber temperature sensor value but converted to float (for some unknown reason).   |
| `ADCF_TMPR_STEAMGE`           | 556f     | ✅ Coherent  | R/- | y      | Retrive raw ADC steamgen temperature sensor value but converted to float (for some unknown reason).  |
| `RAW_NOTFILTRD_PRESS_PROC`    | 538u     | ✅ Coherent  | R/- | y      | Seems the same as ADCF_PRESS_PROCESS                                                                 |
| `RAW_NOTFILTRD_TMPR_PROC`     | 540u     | ✅ Coherent  | R/- | y      | Seems the same as ADCF_TMPR_PROCESS                                                                  |
| `RAW_NOTFILTRD_TMPR_CHMBR`    | 542u     | ✅ Coherent  | R/- | y      | Seems the same as ADCF_TMPR_CHAMBER                                                                  |
| `RAW_NOTFILTRD_TMPR_STEAMGEN` | 544u     | ✅ Coherent  | R/- | y      | Seems the same as ADCF_TMPR_STEAMGE                                                                  |
| `STANDBY_COOLING_THRSH`       | 223u     | ✅ Coherent  | R/W | y      | Set threshold at whichfans should work on idle state. TODO add variable to set speed.                |
| `RELAY_STEAMGEN_AB`           | 1519u    | ✅ Coherent  | R/W | y      | Read/Write double steamgen relay state. Use 3 state control.                                         |
| `RELAY_CHAMBER_AB`            | 1520u    | ✅ Coherent  | R/W | y      | Read/Write chamber relay state. Use 3 state control.                                                 |
| `RELAY_PUMP_VACUUM`           | 1521u    | ✅ Coherent  | R/W | y      | Read/Write vacuum pump relay state. Use 3 state control.                                             |
| `RELAY_PUMP_WATER`            | 1522u    | ✅ Coherent  | R/W | y      | Read/Write water pump relay state. Use 3 state control.                                              |
| `VALVE1`                      | 1523u    | ✅ Coherent  | R/W | y      | Read/Write valve 1 state. Use 3 state control.                                                       |
| `VALVE2`                      | 1524u    | ✅ Coherent  | R/W | y      | Read/Write valve 2 state. Use 3 state control.                                                       |
| `VALVE3`                      | 1525u    | ✅ Coherent  | R/W | y      | Read/Write valve 3 state. Use 3 state control.                                                       |
| `VALVE5`                      | 1526u    | ✅ Coherent  | R/W | y      | Read/Write valve 5 state. Use 3 state control.                                                       |
| `RELAY_STEAMGEN_C`            | 1551u    | ✅ Coherent  | R/W | y      | Read/Write single steamgen relay state. Use 3 state control.                                         |
| `TEST_FLOAT`                  | 3490f    | ❌ New       | R/W | y      | Test read write of float                                                                             |
| `TEST_INT`                    | 3492u    | ❌ New       | R/W | y      | Test read write of int                                                                               |
| `STM_REBOOT`                  | 3499u    | ❌ New       | -/W | y      | Restart system                                                                                       |
| `PWR_CTRL_PATTERN`            | 3493u    | ❌ New       | R/- | y      | Get recently used heating pattern                                                                    |
| `PWR_CH_CTRL`                 | 3494u    | ❌ New       | R/- | y      | 2 if chamber target temperature forced else 0                                                        |
| `PWR_CH_DRV_MONITOR`          | 3504u    | ❌ New       | R/- | y      | PI ctrl output signal, means percentage power deliverd to chamber heater.                            |
| `PWR_CH_TARGET`               | 0        | ❌ New       | R/- | y      | During PI controlled target value in *C of chamber                                                   |
| `PWR_SG_CTRL`                 | 3496u    | ❌ New       | R/- | y      | 2 if steamgen target temperature forced else 0                                                       |
| `PWR_SG_TARGET`               | 0        | ❌ New       | R/- | y      | During PI controlled target value in *C of stramgen                                                  |
| `PWR_SG_DRV_MONITOR`          | 3505u    | ❌ New       | R/- | y      | PI ctrl output signal, means percentage power deliverd to elected config of steamgen heaters.        |
| `PUMP_WTR_INTERVAL`           | 3506u    | ❌ New       | R/W | y      | Alternative to use 'relay', this uses timer. Value in ms.                                            |
| `PUMP_WTR_ON_TIME`            | 3507u    | ❌ New       | R/W | y      | Alternative to use 'relay', this uses timer. Value in ms.                                            |
| `CHANGE_SCREEN`               | 3550u    | ❌ New       | R/W | y      | Change screenn, not all transitions supported                                                        |
| `TEMPERATURE_EXTERNAL`        | 3510f    | ❌ New       | R/- | y      | Get external (PCB) temperature. Can be 40-80*C easly.                                                |
| `xx`                          | 0        | ?           | -/- |        | xxxx                                                                                                 |
| `xx`                          | 0        | ?           | -/- |        | xxxx                                                                                                 |
| `xx`                          | 0        | ?           | -/- |        | xxxx                                                                                                 |
| `xx`                          | 0        | ?           | -/- |        | xxxx                                                                                                 |
| `xx`                          | 0        | ?           | -/- |        | xxxx                                                                                                 |
| `xx`                          | 0        | ?           | -/- |        | xxxx                                                                                                 |
| `xx`                          | 0        | ?           | -/- |        | xxxx                                                                                                 |
| `xx`                          | 0        | ?           | -/- |        | xxxx                                                                                                 |

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