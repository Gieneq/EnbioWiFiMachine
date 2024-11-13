import time
from datetime import datetime, timedelta
import pytest
import re
from enbio_wifi_machine.machine import EnbioWiFiMachine
from enbio_wifi_machine.common import EnbioDeviceInternalException, await_value, float_to_ints, ints_to_float, \
    ProcessType, ScreenId

epsilon = 1e-4
minimal_reboot_time_sec = 11


@pytest.fixture
def enbio_wifi_machine():
    # Setup device for tests
    device = EnbioWiFiMachine()

    yield device

    # Teardown
    device.set_standby_cooling_thrsh_tmpr(70)


def test_int_saving(enbio_wifi_machine):
    val = 125
    enbio_wifi_machine.set_test_int(val)
    assert val == enbio_wifi_machine.get_test_int()


def test_float_conversion():
    float_value = 107.33
    low, high = float_to_ints(float_value)
    actual_float = ints_to_float(low, high)
    assert abs(float_value - actual_float) < epsilon


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
    time.sleep(10)

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
