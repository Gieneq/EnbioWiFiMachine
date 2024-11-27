import os.path
import time
from datetime import datetime, timedelta
import pytest
import re
from enbio_wifi_machine.machine import EnbioWiFiMachine
from enbio_wifi_machine.common import EnbioDeviceInternalException, await_value, float_to_ints, ints_to_float, \
    ProcessType, ScreenId, ScaleFactors, ScaleFactor, ValveState, RelayState, Relay, HeatersToggleCounts

epsilon = 1e-4
minimal_reboot_time_sec = 11
test_data_dir_path = "data"

""" Tools """


def get_next_backup_filepath(directory, base_filename):
    # Separate the base filename and extension
    name, ext = os.path.splitext(base_filename)

    # Check for files with similar naming pattern
    index = 1
    while True:
        indexed_filename = f"{name}_{index}{ext}"
        if not os.path.exists(os.path.join(directory, indexed_filename)):
            break
        index += 1

    return os.path.join(directory, indexed_filename)


""" Unit tests """


def test_float_conversion():
    float_value = 107.33
    low, high = float_to_ints(float_value)
    actual_float = ints_to_float(low, high)
    assert abs(float_value - actual_float) < epsilon


def test_enbio_device_scale_factors_serialize():
    # Sample data
    pressure_scale = ScaleFactor(a=1.0, b=0.5)
    temperature_scale = ScaleFactor(a=2.0, b=1.0)
    chamber_scale = ScaleFactor(a=0.8, b=0.3)
    steamgen_scale = ScaleFactor(a=1.2, b=0.2)

    scales = ScaleFactors(
        pressure_process=pressure_scale,
        temperature_process=temperature_scale,
        temperature_chamber=chamber_scale,
        temperature_steamgen=steamgen_scale
    )

    # Path to the JSON file
    filename = "scale_factors_serialization_test.json"
    path = os.path.join(test_data_dir_path, filename)

    # Save to JSON file
    with open(path, "w") as f:
        f.write(scales.to_json(pretty=True))

    # Load from JSON file
    with open(path, "r") as f:
        loaded_scales = ScaleFactors.from_json(f.read())

    # Check loaded data
    print(loaded_scales)

    assert scales.equals(loaded_scales)


""" Integration tests with real machine """


@pytest.fixture
def enbio_wifi_machine():

    # Ensure test data directory exists
    os.makedirs(test_data_dir_path, exist_ok=True)

    # Setup device for tests
    device = EnbioWiFiMachine()

    yield device

    # Teardown
    device.set_standby_cooling_thrsh_tmpr(70)


def test_int_saving(enbio_wifi_machine):
    val = 125
    enbio_wifi_machine.set_test_int(val)
    assert val == enbio_wifi_machine.get_test_int()


def test_float_saving(enbio_wifi_machine):
    val = 103.71
    enbio_wifi_machine.set_test_float(val)
    assert abs(val - enbio_wifi_machine.get_test_float()) < epsilon


def test_enbio_device_set_devid(enbio_wifi_machine):

    with pytest.raises(EnbioDeviceInternalException) as _:
        new_bad_device_id = "STW02-XX-24-11199111prosiaczek_eli11111111111199"
        enbio_wifi_machine.set_device_id(new_bad_device_id)

    new_device_id = "STW02-XX-24-99999"
    enbio_wifi_machine.set_device_id(new_device_id)
    actual_device_id = enbio_wifi_machine.get_device_id()

    assert actual_device_id == new_device_id


def test_enbio_device_await_door_open(enbio_wifi_machine):
    print("Please open door")
    assert await_value(enbio_wifi_machine.is_door_open, True, 60)


def test_enbio_device_await_door_close(enbio_wifi_machine):
    print("Please close door")
    assert await_value(enbio_wifi_machine.is_door_open, False, 60)


def test_enbio_device_check_lock_drv(enbio_wifi_machine):
    assert not enbio_wifi_machine.is_door_open()

    enbio_wifi_machine.door_drv_fwd()
    time.sleep(0.25)

    enbio_wifi_machine.door_drv_none()
    time.sleep(0.25)

    enbio_wifi_machine.door_drv_bwd()
    time.sleep(0.25)

    enbio_wifi_machine.door_drv_none()
    time.sleep(0.25)


def test_enbio_device_check_lock_with_feedback(enbio_wifi_machine):
    assert not enbio_wifi_machine.is_door_open()

    enbio_wifi_machine.door_lock_with_feedback(timeout=0.5)
    time.sleep(0.25)
    assert not enbio_wifi_machine.is_door_unlocked()

    enbio_wifi_machine.door_unlock_with_feedback(timeout=0.5)
    time.sleep(0.25)
    assert enbio_wifi_machine.is_door_unlocked()


def test_enbio_device_datetime_cmp(enbio_wifi_machine):

    time_to_set = datetime.now().replace(second=0, microsecond=0)
    enbio_wifi_machine.set_datetime(time_to_set)

    time_to_set_obtained = enbio_wifi_machine.get_datetime()
    time_diff = abs((time_to_set_obtained - time_to_set).total_seconds())
    print(f"Time diff between set and get: {time_diff}")
    assert time_diff < 0.1


def test_enbio_device_datetime_driff(enbio_wifi_machine):
    seconds_to_wait = float(5)

    time_to_set = datetime.now().replace(second=0, microsecond=0)
    enbio_wifi_machine.set_datetime(time_to_set)

    time_to_add = timedelta(seconds=seconds_to_wait)
    time.sleep(seconds_to_wait)

    new_datetime_target = time_to_set + time_to_add
    new_datetime_obtained = enbio_wifi_machine.get_datetime()

    actual_seconds_passed = (new_datetime_obtained - new_datetime_target).total_seconds()
    print(f"Time diff between set and get: {actual_seconds_passed}")
    assert actual_seconds_passed != seconds_to_wait


def test_enbio_device_datetime_saving_reboot():
    # Do not use fixture!
    machine = EnbioWiFiMachine()
    seconds_to_wait = float(2 * minimal_reboot_time_sec)

    time_to_set = datetime.now().replace(second=0, microsecond=0)
    machine.set_datetime(time_to_set)

    # Reboot and sleep
    time_to_add = timedelta(seconds=seconds_to_wait)
    machine.reboot()
    time.sleep(seconds_to_wait)

    # Recreate machine
    machine = EnbioWiFiMachine()
    new_datetime_target = time_to_set + time_to_add
    new_datetime_obtained = machine.get_datetime()

    actual_seconds_passed = (new_datetime_obtained - new_datetime_target).total_seconds()
    print(f"Time diff between set and get: {actual_seconds_passed}")
    assert actual_seconds_passed != seconds_to_wait


def test_enbio_device_firmware_version(enbio_wifi_machine):
    pattern = r"^\d+\.\d+\.\d+$"
    firmware_version = enbio_wifi_machine.get_firmware_version()
    assert re.match(pattern, firmware_version), f"Firmware version '{firmware_version}' not match pattern 'Ma.Mi.P'"


# def test_enbio_device_phase_id(enbio_wifi_machine):
#     assert enbio_wifi_machine.get_phase_id() == 1


def test_enbio_device_boardnumber(enbio_wifi_machine):
    enbio_wifi_machine.set_boardnumber('A', 0, 1)
    assert enbio_wifi_machine.get_boardnumber() == ('A', 0, 1)

    enbio_wifi_machine.set_boardnumber('C', 23, 5)
    assert enbio_wifi_machine.get_boardnumber() == ('C', 23, 5)

    enbio_wifi_machine.set_boardnumber('Z', 99, 12)
    assert enbio_wifi_machine.get_boardnumber() == ('Z', 99, 12)


def test_enbio_device_dipswitch(enbio_wifi_machine):
    dipsw_value = enbio_wifi_machine.get_dpi_switch()

    assert isinstance(dipsw_value, tuple)

    assert len(dipsw_value) == 4

    assert all(isinstance(element, bool) for element in dipsw_value)


def test_enbio_device_fans_cooling(enbio_wifi_machine):
    thrsh_tpr = 10

    enbio_wifi_machine.set_standby_cooling_thrsh_tmpr(thrsh_tpr)

    time.sleep(3)

    assert enbio_wifi_machine.get_standby_cooling_thrsh_tmpr() == thrsh_tpr


def test_enbio_device_clear_process_counter(enbio_wifi_machine):
    enbio_wifi_machine.clear_process_counter()

    proc_cnter = enbio_wifi_machine.get_process_counter()
    print(f"Got process counter {proc_cnter}")
    assert proc_cnter == 0


def test_enbio_device_start_check_recent_screen(enbio_wifi_machine):
    assert enbio_wifi_machine.get_recent_screen() == ScreenId.MAIN


def test_enbio_device_start_interrupt_process(enbio_wifi_machine):
    process_duration_seconds = 12

    processes_counter_before = enbio_wifi_machine.get_process_counter()

    enbio_wifi_machine.start_process(ProcessType.P121)
    processes_counter_after = enbio_wifi_machine.get_process_counter()
    time.sleep(process_duration_seconds)

    enbio_wifi_machine.interrupt_process()
    print(f"Process counter before: {processes_counter_before}, after: {processes_counter_after}")

    assert processes_counter_after == processes_counter_before + 1

    # Delay some time to let device release lock
    time.sleep(1)


def test_enbio_device_saving():
    # Do not use fixture!
    tool = EnbioWiFiMachine()

    new_device_id = "STW02-XX-24-99999"
    tool.set_device_id(new_device_id)

    tool.save_all()

    # Reboot and sleep
    tool.reboot()
    time.sleep(minimal_reboot_time_sec)

    tool = EnbioWiFiMachine()
    device_id = tool.get_device_id()

    assert device_id == new_device_id


def test_enbio_device_lock_frequent(enbio_wifi_machine):
    for _ in range(20):
        assert not enbio_wifi_machine.is_door_open()
        enbio_wifi_machine.door_lock_with_feedback(timeout=0.5)
        assert not enbio_wifi_machine.is_door_unlocked()

        enbio_wifi_machine.door_unlock_with_feedback(timeout=0.5)
        assert enbio_wifi_machine.is_door_unlocked()


def test_enbio_device_scale_factors_load_save(enbio_wifi_machine):
    scale_factors_filename = "scale_factors.json"
    path = os.path.join(test_data_dir_path, scale_factors_filename)

    sf = enbio_wifi_machine.get_scale_factors()
    json_data = sf.to_json()
    with open(path, "w") as f:
        f.write(json_data)

    enbio_wifi_machine.set_scale_factors(sf)

    actual_sf = enbio_wifi_machine.get_scale_factors()

    assert sf == actual_sf


def test_enbio_device_scale_factors_load_save_with_reboot():
    # Do not use fixture!
    enbio_wifi_machine = EnbioWiFiMachine()
    scale_factors_filename = "backup_scale_factors.json"
    path = get_next_backup_filepath(test_data_dir_path, scale_factors_filename)

    original_sf = enbio_wifi_machine.get_scale_factors()
    json_data = original_sf.to_json()
    with open(path, "w") as f:
        f.write(json_data)

    # Use temporary sale factors
    tmp_scales = ScaleFactors(
        pressure_process=ScaleFactor(a=8.71000003487803e-05, b=0.924238007068634),
        temperature_process=ScaleFactor(a=0.0058479998260736465, b=15.80257682800293),
        temperature_chamber=ScaleFactor(a=0.00384500003606081, b=15.295173072814941),
        temperature_steamgen=ScaleFactor(a=0.004634000185132027, b=14.816951560974121)
    )

    enbio_wifi_machine.set_scale_factors(tmp_scales)
    enbio_wifi_machine.save_all()

    # Reboot and sleep
    enbio_wifi_machine.reboot()
    time.sleep(minimal_reboot_time_sec)

    actual_sf = enbio_wifi_machine.get_scale_factors()

    # Set scales before assert to prevent discarding
    enbio_wifi_machine.set_scale_factors(original_sf)

    assert tmp_scales.equals(actual_sf)


def test_enbio_device_valves(enbio_wifi_machine):
    valves_list = [Relay.Valve1, Relay.Valve2, Relay.Valve3, Relay.Valve5]
    for valve in valves_list:
        print(f"Test valve: {valve}")
        enbio_wifi_machine.set_valve(valve, ValveState.Open)
        assert enbio_wifi_machine.get_valve(valve) == ValveState.Open
        time.sleep(1)
        enbio_wifi_machine.set_valve(valve, ValveState.Closed)
        assert enbio_wifi_machine.get_valve(valve) == ValveState.Closed
        time.sleep(1)
        enbio_wifi_machine.set_valve(valve, ValveState.Auto)
        assert enbio_wifi_machine.get_valve(valve) == ValveState.Auto


def test_enbio_device_relays(enbio_wifi_machine):
    relays_list = [Relay.SteamgenDouble, Relay.Chamber, Relay.VacuumPump, Relay.WaterPump, Relay.SteamgenSingle]
    for relay in relays_list:
        print(f"Test relay: {relay}")
        enbio_wifi_machine.set_relay(relay, RelayState.On)
        assert enbio_wifi_machine.get_relay(relay) == RelayState.On
        time.sleep(1)
        enbio_wifi_machine.set_relay(relay, RelayState.Off)
        assert enbio_wifi_machine.get_relay(relay) == RelayState.Off
        time.sleep(1)
        enbio_wifi_machine.set_relay(relay, RelayState.Auto)
        assert enbio_wifi_machine.get_relay(relay) == RelayState.Auto


def test_get_pressures_temperatures(enbio_wifi_machine):
    print(f"pressure process: {enbio_wifi_machine.get_pressure('process')} bar")
    print(f"pressure external: {enbio_wifi_machine.get_pressure('external')} bar")
    print(f"pressure relative: {enbio_wifi_machine.get_pressure('relative')} bar")

    print(f"temperature process: {enbio_wifi_machine.get_temperature('process')} *C")
    print(f"temperature chamber: {enbio_wifi_machine.get_temperature('chamber')} *C")
    print(f"temperature steamgen: {enbio_wifi_machine.get_temperature('steamgen')} *C")
    print(f"temperature external: {enbio_wifi_machine.get_temperature('external')} *C")


def test_get_adc_raw_temperature(enbio_wifi_machine):
    print(f"pressure process sensor raw ADC value: {enbio_wifi_machine.get_raw_temperature('pressure')}")
    print(f"temperature process sensor raw ADC value: {enbio_wifi_machine.get_raw_temperature('process')}")
    print(f"temperature chamber sensor raw ADC value: {enbio_wifi_machine.get_raw_temperature('chamber')}")
    print(f"temperature steamgen sensor raw ADC value: {enbio_wifi_machine.get_raw_temperature('steamgen')}")


def test_enbio_device_do_state_valves(enbio_wifi_machine):
    enbio_wifi_machine.set_valve(Relay.Valve1, ValveState.Open)
    enbio_wifi_machine.set_valve(Relay.Valve2, ValveState.Closed)
    enbio_wifi_machine.set_valve(Relay.Valve3, ValveState.Open)
    enbio_wifi_machine.set_valve(Relay.Valve5, ValveState.Closed)

    do_state = enbio_wifi_machine.get_do_state()
    print(f"DO State: {do_state}")

    assert do_state.v1_open is True
    assert do_state.v2_open is False
    assert do_state.v3_open is True
    assert do_state.v5_open is False

    valves_list = [Relay.Valve1, Relay.Valve2, Relay.Valve3, Relay.Valve5]
    for valve in valves_list:
        enbio_wifi_machine.set_valve(valve, ValveState.Auto)


def test_enbio_device_do_state_pumps_vacuum(enbio_wifi_machine):
    enbio_wifi_machine.set_relay(Relay.VacuumPump, RelayState.On)
    time.sleep(0.25)

    do_state = enbio_wifi_machine.get_do_state()
    print(f"DO State: {do_state}")
    assert do_state.pump_vac is True
    assert do_state.pump_water is False

    enbio_wifi_machine.set_relay(Relay.VacuumPump, RelayState.Off)

    do_state = enbio_wifi_machine.get_do_state()
    print(f"DO State: {do_state}")
    assert do_state.pump_vac is False
    assert do_state.pump_water is False

    enbio_wifi_machine.set_relay(Relay.VacuumPump, RelayState.Auto)


def test_enbio_device_do_state_pumps_water(enbio_wifi_machine):
    enbio_wifi_machine.set_relay(Relay.WaterPump, RelayState.On)
    time.sleep(2.25)

    do_state = enbio_wifi_machine.get_do_state()
    print(f"DO State: {do_state}")
    assert do_state.pump_vac is False
    assert do_state.pump_water is True

    enbio_wifi_machine.set_relay(Relay.WaterPump, RelayState.Off)

    do_state = enbio_wifi_machine.get_do_state()
    print(f"DO State: {do_state}")
    assert do_state.pump_vac is False
    assert do_state.pump_water is False

    enbio_wifi_machine.set_relay(Relay.WaterPump, RelayState.Auto)


def test_poll_procline(enbio_wifi_machine):
    procline = enbio_wifi_machine.poll_process_line()
    print(procline)


def test_backlight(enbio_wifi_machine):
    brightness_values = [0, 1, 2, 3, 55, 99, 75]

    for brightness_value in brightness_values:
        enbio_wifi_machine.set_backlight(brightness_value)
        time.sleep(0.5)
        assert enbio_wifi_machine.get_backlight() == brightness_value


def test_enbio_device_do_state_process(enbio_wifi_machine):
    enbio_wifi_machine.start_process(ProcessType.P121)
    time.sleep(5)

    do_state = enbio_wifi_machine.get_do_state()

    enbio_wifi_machine.interrupt_process()
    # Delay some time to let device release lock
    time.sleep(1)

    assert do_state.proc_type == ProcessType.P121


def test_enbio_defice_restore_defaults(enbio_wifi_machine):
    device_id = enbio_wifi_machine.get_device_id()
    scales = enbio_wifi_machine.get_scale_factors()

    enbio_wifi_machine.reset_parameters_with_target(target_us=True)

    device_id_after_reset = enbio_wifi_machine.get_device_id()
    scales_after_reset = enbio_wifi_machine.get_scale_factors()

    assert device_id == device_id_after_reset
    assert scales.equals(scales_after_reset)


def test_enbio_device_heaters_toggle_counters(enbio_wifi_machine):
    print(enbio_wifi_machine.get_heater_toggle_cnts())

    cnts_to_set = HeatersToggleCounts(
        sg_ab=120,
        ch_ab=10,
        sg_c=3330,
    )
    enbio_wifi_machine.set_heater_toggle_cnts(cnts_to_set)
    after_set = enbio_wifi_machine.get_heater_toggle_cnts()

    cnts_to_clear = HeatersToggleCounts(
        sg_ab=0,
        ch_ab=0,
        sg_c=0,
    )
    enbio_wifi_machine.set_heater_toggle_cnts(cnts_to_clear)

    assert after_set == cnts_to_set

