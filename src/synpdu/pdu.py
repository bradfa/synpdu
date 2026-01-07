"""
Synaccess Netbooter DU series PDU control via HTTP CGI interface.

Tested with: NP-0201DU
"""

import base64
import urllib.request
import urllib.error
from urllib.parse import urlparse, quote


def _parse_host(host: str) -> tuple[str, tuple[str, str]]:
    """
    Parse host URL to extract base URL and credentials.

    Args:
        host: Either 'IP' or 'http://user:pass@IP'

    Returns:
        (base_url, (username, password))
    """
    # If no scheme, assume http://
    if not host.startswith('http://') and not host.startswith('https://'):
        host = f'http://{host}'

    parsed = urlparse(host)

    # Extract credentials or use defaults
    username = parsed.username or 'admin'
    password = parsed.password or 'admin'

    # Reconstruct URL without credentials
    if parsed.username:
        # Remove credentials from netloc
        netloc = parsed.hostname
        if parsed.port:
            netloc = f'{netloc}:{parsed.port}'
        base_url = f'{parsed.scheme}://{netloc}{parsed.path}'
    else:
        base_url = host

    return base_url.rstrip('/'), (username, password)


def set_outlet(host: str, outlet: int, state: bool, username: str, password: str) -> None:
    """Set power state via HTTP CGI interface."""
    base_url, (default_user, default_pass) = _parse_host(host)

    # Use provided credentials or defaults from URL
    auth_user = username if username != 'admin' else default_user
    auth_pass = password if password != 'admin' else default_pass

    state_val = 1 if state else 0
    url = f"{base_url}/cmd.cgi?{quote(f'$A3 {outlet} {state_val}')}"

    # Create request with Basic Auth
    req = urllib.request.Request(url)
    credentials = base64.b64encode(f'{auth_user}:{auth_pass}'.encode()).decode()
    req.add_header('Authorization', f'Basic {credentials}')

    try:
        with urllib.request.urlopen(req, timeout=5) as response:
            text = response.read().decode()

            # Check for success response ($A0)
            if "$A0" not in text:
                raise RuntimeError(f"PDU command failed: {text}")
    except urllib.error.HTTPError as e:
        raise RuntimeError(f"HTTP error {e.code}: {e.reason}")
    except urllib.error.URLError as e:
        raise RuntimeError(f"URL error: {e.reason}")


def get_outlet(host: str, outlet: int, username: str, password: str) -> bool:
    """Get power state via HTTP CGI interface."""
    base_url, (default_user, default_pass) = _parse_host(host)

    # Use provided credentials or defaults from URL
    auth_user = username if username != 'admin' else default_user
    auth_pass = password if password != 'admin' else default_pass

    url = f"{base_url}/cmd.cgi?$A5"

    # Create request with Basic Auth
    req = urllib.request.Request(url)
    credentials = base64.b64encode(f'{auth_user}:{auth_pass}'.encode()).decode()
    req.add_header('Authorization', f'Basic {credentials}')

    try:
        with urllib.request.urlopen(req, timeout=5) as response:
            text = response.read().decode()

            # Response format: "$A0,xx,cccc,tt"
            # where $A0 = success, xx = outlet states (1=ON, 0=OFF), rightmost is outlet 1
            response_text = text.strip()
            fields = response_text.split(',')
            states = fields[1]  # Get the outlet states part (second field)

            # Reverse because rightmost character is outlet 1
            states_reversed = states[::-1]

            # Validate outlet number
            if outlet < 1 or outlet > len(states_reversed):
                raise ValueError(f"Invalid outlet number: {outlet}")

            # Return True if ON (1), False if OFF (0)
            return states_reversed[outlet - 1] == '1'
    except urllib.error.HTTPError as e:
        raise RuntimeError(f"HTTP error {e.code}: {e.reason}")
    except urllib.error.URLError as e:
        raise RuntimeError(f"URL error: {e.reason}")


def get_all_status(host: str, username: str, password: str) -> dict[str, bool | float]:
    """Get status of all outlets and current measurement via HTTP CGI interface.

    Args:
        host: PDU IP address or URL
        username: Authentication username
        password: Authentication password

    Returns:
        Dictionary with keys 'outlet1' (bool), 'outlet2' (bool), 'current' (float)

    Raises:
        RuntimeError: If HTTP request fails or response format is invalid
    """
    base_url, (default_user, default_pass) = _parse_host(host)

    # Use provided credentials or defaults from URL
    auth_user = username if username != 'admin' else default_user
    auth_pass = password if password != 'admin' else default_pass

    url = f"{base_url}/cmd.cgi?$A5"

    # Create request with Basic Auth
    req = urllib.request.Request(url)
    credentials = base64.b64encode(f'{auth_user}:{auth_pass}'.encode()).decode()
    req.add_header('Authorization', f'Basic {credentials}')

    try:
        with urllib.request.urlopen(req, timeout=5) as response:
            text = response.read().decode()

            # Response format: "$A0,xx,cccc,tt"
            # where $A0 = success, xx = outlet states (1=ON, 0=OFF), rightmost is outlet 1
            # cccc = current consumption in amps
            response_text = text.strip()
            fields = response_text.split(',')

            if len(fields) < 3:
                raise RuntimeError(f"Invalid PDU response format: {response_text}")

            states = fields[1]
            current_str = fields[2]

            # Reverse because rightmost character is outlet 1
            states_reversed = states[::-1]

            # Validate we have at least 2 outlets in response
            if len(states_reversed) < 2:
                raise RuntimeError(f"Invalid outlet states in response: {states}")

            outlet1 = states_reversed[0] == '1'
            outlet2 = states_reversed[1] == '1'

            # Parse current measurement, default to 0.0 if invalid
            try:
                current = float(current_str)
            except ValueError:
                current = 0.0

            return {
                'outlet1': outlet1,
                'outlet2': outlet2,
                'current': current
            }
    except urllib.error.HTTPError as e:
        raise RuntimeError(f"HTTP error {e.code}: {e.reason}")
    except urllib.error.URLError as e:
        raise RuntimeError(f"URL error: {e.reason}")
