# synpdu

A command-line tool to control Synaccess Netbooter NP-0201DU PDU outlets via the HTTP CGI interface.

## Overview

`synpdu` provides simple command-line control of Synaccess Netbooter PDU outlets. It uses the device's built-in HTTP CGI interface to turn outlets on/off and query their status.

**Tested Hardware:**
- Synaccess Netbooter NP-0201DU (2-outlet PDU)

The tool may work with other Synaccess Netbooter models that support the same CGI command interface.

## Installation

### From PyPI

```bash
pip install synpdu
```

### From Source

```bash
git clone https://github.com/bradfa/synpdu.git
cd synpdu
pip install -e .
```

## Requirements

- Python 3.8 or later
- Network access to the PDU
- No external dependencies (uses Python standard library only)

## Usage

### Basic Commands

Turn outlet 1 on:
```bash
synpdu 1 on
```

Turn outlet 2 off:
```bash
synpdu 2 off
```

Check outlet 1 status:
```bash
synpdu 1 status
```

Check all outlets and current measurement:
```bash
synpdu status
```

Example output:
```
Outlet 1 is ON
Outlet 2 is OFF
Current: 0.05 A
```

### Custom PDU Configuration

By default, `synpdu` connects to a PDU at `192.168.1.100` using credentials `admin:admin`. You can override these with command-line flags:

```bash
synpdu 1 on --host 192.168.2.50
synpdu 1 on --host 192.168.2.50 --username myuser --password mypass
```

You can also use HTTPS and custom ports:
```bash
synpdu 1 on --host https://192.168.1.100:8080
```

### Command-Line Options

```
synpdu [-h] [--host HOST] [--username USERNAME] [--password PASSWORD] [--version] [{1,2}] {on,off,status}

Positional arguments:
  {1,2}                 Outlet number (1 or 2) - optional for status command
  {on,off,status}       Command to execute

Options:
  -h, --help            Show this help message and exit
  --host HOST           PDU IP address or URL (default: 192.168.1.100)
  --username USERNAME   PDU username (default: admin)
  --password PASSWORD   PDU password (default: admin)
  --version             Show program's version number and exit
```

**Note:** The outlet number is required for `on` and `off` commands, but optional for `status`.
When no outlet is specified with `status`, all outlets and current measurement are displayed.

## Development

### Running Tests

Install development dependencies:
```bash
pip install -e ".[dev]"
```

Run tests:
```bash
pytest
```

Run tests with coverage:
```bash
pytest --cov=synpdu tests/
```

### Building for Distribution

Install build tools:
```bash
pip install build twine
```

Build the package:
```bash
python -m build
```

This creates distribution files in the `dist/` directory.

## How It Works

The Synaccess Netbooter PDUs provide a simple HTTP CGI interface at `/cmd.cgi`:

- **Set outlet state:** `GET /cmd.cgi?$A3 {outlet} {state}`
  - `outlet`: 1 or 2
  - `state`: 1 = ON, 0 = OFF
  - Success response contains `$A0`

- **Get all outlet states:** `GET /cmd.cgi?$A5`
  - Returns: `$A0,xx,cccc,tt`
  - `xx`: outlet states (rightmost character is outlet 1)
  - `cccc`: current consumption
  - `tt`: temperature or other data

Authentication uses HTTP Basic Auth on every request.

## License

This project is licensed under the GNU General Public License v2.0 - see the LICENSE file for details.
