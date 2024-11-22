import argparse
from datetime import datetime
from .machine import EnbioWiFiMachine
from .common import process_labels, EnbioDeviceInternalException, ScaleFactors


def initialize_parser():
    parser = argparse.ArgumentParser(description="CLI tool to set and get device name via Modbus.")
    subparsers = parser.add_subparsers(dest="command")

    # Subcommand for setting device ID
    devidset_parser = subparsers.add_parser("devidset", help="Set the device name.")
    devidset_parser.add_argument("devid", type=str, help="The name to set for the device.")

    # Subcommand for getting device ID
    _ = subparsers.add_parser("devidget", help="Get the current device name.")

    set_presets = subparsers.add_parser("setpresets", help=f"Set presets 'us' or 'eu'")
    set_presets.add_argument("-t", "--target", choices=["us", "eu"], type=str, required=True, help="Target region.")

    # Subcommand for saving all
    _ = subparsers.add_parser("saveall", help="Save all current settings to persistent storage.")

    # Door state commands
    _ = subparsers.add_parser("isdooropen", help="Get door open state, 1 means door is open.")
    _ = subparsers.add_parser("isdoorunlocked", help="Get door lock state, 1 means door is unlocked.")

    # Door control commands
    _ = subparsers.add_parser("doorlock", help="Lock the door.")
    _ = subparsers.add_parser("doorunlock", help="Unlock the door.")
    _ = subparsers.add_parser("doordrvfwd", help="Drive the door forward.")
    _ = subparsers.add_parser("doordrvbwd", help="Drive the door backward.")
    _ = subparsers.add_parser("doordrvnone", help="Stop door driving.")

    _ = subparsers.add_parser("dtsetnow", help="todo.")

    runparser = subparsers.add_parser("run", help=f"Run program {process_labels}, example: run 134f.")
    runparser.add_argument(
        "procname",
        type=str,
        choices=process_labels,
        help=f"Run one of {process_labels}"
    )

    _ = subparsers.add_parser("monitor", help="todo.")

    # Scale factors commands
    scales_get_parser = subparsers.add_parser("scales", help="Manage scale factors.")
    scales_get_parser.add_argument("action", choices=["get", "set"], help="Action to perform: 'get' or 'set'")
    scales_get_parser.add_argument("-f", "--filepath", type=str, required=True, help="File path for scales data.")

    return parser


def main():
    parser = initialize_parser()
    args = parser.parse_args()

    # Initialize the ModbusTool instance
    try:
        tool = EnbioWiFiMachine()
    except EnbioDeviceInternalException as e:
        print(f"Enbio Mosbus failed, reason: {e}")

    if args.command == "devidset":
        try:
            tool.set_device_id(args.devid)
            print(f"Device ID set to: {args.devid} success")
        except EnbioDeviceInternalException as e:
            print(f"Device ID set to: {args.devid} failed : {e}")

    elif args.command == "devidget":
        print(tool.get_device_id())

    elif args.command == "setpresets":
        print(f"Setting presets for {args.target}")
        should_target_us = args.target == "us"
        tool.reset_parameters_with_target(should_target_us)

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

    elif args.command == "run":
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

    elif args.command == "scales":
        if args.action == "get":
            print(f"Loading scales from machine and saving to: {args.filepath}")
            loaded_scales = tool.get_scale_factors()
            with open(args.filepath, "w") as f:
                f.write(loaded_scales.to_json(pretty=True))

        elif args.action == "set":
            print(f"Using scales from: {args.filepath} and saving to machine")
            with open(args.filepath, "r") as f:
                scales_to_be_saved = ScaleFactors.from_json(f.read())
                tool.set_scale_factors(scales_to_be_saved)
            print(f"Saving to FLASH")
            tool.save_all()

    else:
        parser.print_help()


if __name__ == "__main__":
    main()
