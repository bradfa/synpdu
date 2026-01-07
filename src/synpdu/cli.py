"""Command line interface for synpdu."""

import argparse
import sys
from synpdu import __version__
from synpdu.pdu import set_outlet, get_outlet, get_all_status


def main():
    """Main entry point for the CLI."""
    parser = argparse.ArgumentParser(
        description='Control Synaccess Netbooter NP-0201DU PDU outlets',
        prog='synpdu'
    )
    parser.add_argument(
        'outlet',
        type=int,
        choices=[1, 2],
        nargs='?',
        help='Outlet number (1 or 2) - optional for status command'
    )
    parser.add_argument(
        'command',
        choices=['on', 'off', 'status'],
        help='Command to execute'
    )
    parser.add_argument(
        '--host',
        default='192.168.1.100',
        help='PDU IP address or URL (default: 192.168.1.100)'
    )
    parser.add_argument(
        '--username',
        default='admin',
        help='PDU username (default: admin)'
    )
    parser.add_argument(
        '--password',
        default='admin',
        help='PDU password (default: admin)'
    )
    parser.add_argument(
        '--version',
        action='version',
        version=f'%(prog)s {__version__}'
    )

    args = parser.parse_args()

    # Validate that outlet is provided for on/off commands
    if args.command in ['on', 'off'] and args.outlet is None:
        parser.error(f"outlet is required for '{args.command}' command")

    try:
        if args.command == 'on':
            set_outlet(args.host, args.outlet, True, args.username, args.password)
            print(f"Outlet {args.outlet} turned ON")
        elif args.command == 'off':
            set_outlet(args.host, args.outlet, False, args.username, args.password)
            print(f"Outlet {args.outlet} turned OFF")
        elif args.command == 'status':
            if args.outlet is None:
                # Show all outlets and current measurement
                status = get_all_status(args.host, args.username, args.password)
                print(f"Outlet 1 is {'ON' if status['outlet1'] else 'OFF'}")
                print(f"Outlet 2 is {'ON' if status['outlet2'] else 'OFF'}")
                print(f"Current: {status['current']} A")
            else:
                # Show single outlet status
                state = get_outlet(args.host, args.outlet, args.username, args.password)
                if state:
                    print(f"Outlet {args.outlet} is ON")
                else:
                    print(f"Outlet {args.outlet} is OFF")
        sys.exit(0)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
