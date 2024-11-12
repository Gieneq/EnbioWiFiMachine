import argparse
from datetime import datetime
from .machine import EnbioWiFiMachine
from .common import process_labels, EnbioDeviceInternalException


def main():
    parser = argparse.ArgumentParser(description="CLI tool to set and get device name via Modbus.")
    subparsers = parser.add_subparsers(dest="command")

    # Subcommand for setting device ID
    devidset_parser = subparsers.add_parser("devidset", help="Set the device name.")
    devidset_parser.add_argument("devid", type=str, help="The name to set for the device.")

    # Subcommand for getting device ID
    _ = subparsers.add_parser("devidget", help="Get the current device name.")

    # Subcommand for saving all
    _ = subparsers.add_parser("saveall", help="Save all.")

    # Subcommand for door lock
    _ = subparsers.add_parser("isdooropen", help="Get door open state, 1 means door is open.")

    # Subcommand for door lock
    _ = subparsers.add_parser("isdoorunlocked", help="Get door lock state, 1 means door is unlocked.")

    _ = subparsers.add_parser("doorlock", help="todo.")

    _ = subparsers.add_parser("doorunlock", help="todo.")

    _ = subparsers.add_parser("doordrvfwd", help="todo.")

    _ = subparsers.add_parser("doordrvbwd", help="todo.")

    _ = subparsers.add_parser("doordrvnone", help="todo.")

    _ = subparsers.add_parser("dtsetnow", help="todo.")

    runparser = subparsers.add_parser("runmonitor", help=f"Run program {process_labels}, example: run 134f.")
    runparser.add_argument(
        "procname",
        type=str,
        choices=process_labels,
        help=f"Run one of {process_labels}"
    )

    _ = subparsers.add_parser("monitor", help="todo.")

    args = parser.parse_args()

    # Initialize the ModbusTool instance
    try:
        tool = EnbioWiFiMachine()
    except EnbioDeviceInternalException as e:
        print(f"Enbio Mosbus failed, reason: {e}")

    if args.command == "devidset":
        try:
            tool.set_device_id(args.devid)
            print(f"Device ID set to: {args.name} success")
        except EnbioDeviceInternalException as e:
            print(f"Device ID set to: {args.name} failed : {e}")

    elif args.command == "devidget":
        print(tool.get_device_id())

    elif args.command == "saveall":
        try:
            print(f"Saved all done")
            tool.save_all()
        except EnbioDeviceInternalException as e:
            print(f"Saved all failed: {e}")

    elif args.command == "isdooropen":
        print(f"Door open: {tool.is_door_open()}")

    elif args.command == "isdoorunlocked":
        print(f"Door unlocked: {tool.is_door_unlocked()}")

    elif args.command == "doorlock":
        try:
            tool.door_lock_with_feedback()
            print(f"Door got locked")
        except EnbioDeviceInternalException as e:
            print(f"Door locking failed: {e}")
        except Exception as e:
            print(f"An unexpected error occurred: {e}")

    elif args.command == "doorunlock":
        try:
            tool.door_unlock_with_feedback()
            print(f"Door got unlocked")
        except EnbioDeviceInternalException as e:
            print(f"Door unlocking failed: {e}")
        except Exception as e:
            print(f"An unexpected error occurred: {e}")

    elif args.command == "doordrvfwd":
        try:
            tool.door_drv_fwd()
        except EnbioDeviceInternalException as e:
            print(f"Device Error: {e}")
        except Exception as e:
            print(f"An unexpected error occurred: {e}")

    elif args.command == "doordrvbwd":
        try:
            tool.door_drv_bwd()
        except EnbioDeviceInternalException as e:
            print(f"Device Error: {e}")
        except Exception as e:
            print(f"An unexpected error occurred: {e}")

    elif args.command == "doordrvnone":
        try:
            tool.door_drv_none()
        except EnbioDeviceInternalException as e:
            print(f"Device Error: {e}")
        except Exception as e:
            print(f"An unexpected error occurred: {e}")

    elif args.command == "dtsetnow":
        try:
            tool.set_datetime(datetime.now())
        except EnbioDeviceInternalException as e:
            print(f"Device Error: {e}")
        except Exception as e:
            print(f"An unexpected error occurred: {e}")

    elif args.command == "runmonitor":
        print(f"Run {args.procname}")
        try:
            tool.runmonitor(args.procname)
        except KeyboardInterrupt:
            print("Interrupted")
        except EnbioDeviceInternalException as e:
            print(f"Device Error: {e}")
        except Exception as e:
            print(f"An unexpected error occurred: {e}")

    elif args.command == "monitor":
        try:
            tool.monitor()
        except KeyboardInterrupt:
            print("Stopped")
        except EnbioDeviceInternalException as e:
            print(f"Device Error: {e}")
        except Exception as e:
            print(f"An unexpected error occurred: {e}")

    else:
        parser.print_help()
