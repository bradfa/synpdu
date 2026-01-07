"""Unit tests for synpdu PDU control module."""

import pytest
from unittest.mock import MagicMock, patch
from synpdu.pdu import _parse_host, set_outlet, get_outlet, get_all_status


class TestParseHost:
    """Tests for _parse_host function."""

    @pytest.mark.parametrize(
        'host,expected_base,expected_user,expected_pass',
        (
            ('192.168.1.100', 'http://192.168.1.100', 'admin', 'admin'),
            ('http://192.168.1.100', 'http://192.168.1.100', 'admin', 'admin'),
            ('https://192.168.1.100', 'https://192.168.1.100', 'admin', 'admin'),
            ('http://user:pass@192.168.1.100', 'http://192.168.1.100', 'user', 'pass'),
            ('https://admin:secret@192.168.1.100:8080', 'https://192.168.1.100:8080', 'admin', 'secret'),
        )
    )
    def test_parse_host(self, host, expected_base, expected_user, expected_pass):
        """Test URL parsing with various formats."""
        base_url, (username, password) = _parse_host(host)
        assert base_url == expected_base
        assert username == expected_user
        assert password == expected_pass


class TestSetOutlet:
    """Tests for set_outlet function."""

    def test_set_outlet_on(self, mocker):
        """Test turning outlet on."""
        # Mock the response
        mock_response = MagicMock()
        mock_response.read.return_value = b'$A0'
        mock_response.__enter__.return_value = mock_response
        mock_response.__exit__.return_value = None

        mock_urlopen = mocker.patch('urllib.request.urlopen', return_value=mock_response)
        mock_request = mocker.patch('urllib.request.Request')

        set_outlet('192.168.1.100', 1, True, 'admin', 'admin')

        # Verify Request was created with correct URL (URL-encoded)
        mock_request.assert_called_once()
        call_args = mock_request.call_args[0]
        assert call_args[0] == 'http://192.168.1.100/cmd.cgi?%24A3%201%201'

        # Verify urlopen was called with timeout
        mock_urlopen.assert_called_once()
        assert mock_urlopen.call_args[1]['timeout'] == 5

    def test_set_outlet_off(self, mocker):
        """Test turning outlet off."""
        # Mock the response
        mock_response = MagicMock()
        mock_response.read.return_value = b'$A0'
        mock_response.__enter__.return_value = mock_response
        mock_response.__exit__.return_value = None

        mock_urlopen = mocker.patch('urllib.request.urlopen', return_value=mock_response)
        mock_request = mocker.patch('urllib.request.Request')

        set_outlet('192.168.1.100', 1, False, 'admin', 'admin')

        # Verify Request was created with correct URL (URL-encoded)
        mock_request.assert_called_once()
        call_args = mock_request.call_args[0]
        assert call_args[0] == 'http://192.168.1.100/cmd.cgi?%24A3%201%200'

    def test_set_outlet_failure(self, mocker):
        """Test PDU command failure response."""
        # Mock the response with failure
        mock_response = MagicMock()
        mock_response.read.return_value = b'$AF'  # Failure response
        mock_response.__enter__.return_value = mock_response
        mock_response.__exit__.return_value = None

        mocker.patch('urllib.request.urlopen', return_value=mock_response)
        mocker.patch('urllib.request.Request')

        with pytest.raises(RuntimeError, match='PDU command failed'):
            set_outlet('192.168.1.100', 1, True, 'admin', 'admin')


class TestGetOutlet:
    """Tests for get_outlet function."""

    def test_get_outlet_on(self, mocker):
        """Test reading outlet state when ON."""
        # Mock the response - outlet 1 is ON, outlet 2 is OFF
        mock_response = MagicMock()
        mock_response.read.return_value = b'$A0,01,0.05,XX'
        mock_response.__enter__.return_value = mock_response
        mock_response.__exit__.return_value = None

        mock_urlopen = mocker.patch('urllib.request.urlopen', return_value=mock_response)
        mock_request = mocker.patch('urllib.request.Request')

        state = get_outlet('192.168.1.100', 1, 'admin', 'admin')

        assert state is True

        # Verify Request was created with correct URL
        mock_request.assert_called_once()
        call_args = mock_request.call_args[0]
        assert call_args[0] == 'http://192.168.1.100/cmd.cgi?$A5'

        # Verify urlopen was called with timeout
        mock_urlopen.assert_called_once()
        assert mock_urlopen.call_args[1]['timeout'] == 5

    def test_get_outlet_off(self, mocker):
        """Test reading outlet state when OFF."""
        # Mock the response - both outlets OFF
        mock_response = MagicMock()
        mock_response.read.return_value = b'$A0,00,0.00,XX'
        mock_response.__enter__.return_value = mock_response
        mock_response.__exit__.return_value = None

        mocker.patch('urllib.request.urlopen', return_value=mock_response)
        mocker.patch('urllib.request.Request')

        state = get_outlet('http://user:secret@192.168.1.100', 2, 'user', 'secret')

        assert state is False

    def test_get_outlet_invalid_outlet(self, mocker):
        """Test invalid outlet number."""
        # Mock the response
        mock_response = MagicMock()
        mock_response.read.return_value = b'$A0,01,0.05,XX'
        mock_response.__enter__.return_value = mock_response
        mock_response.__exit__.return_value = None

        mocker.patch('urllib.request.urlopen', return_value=mock_response)
        mocker.patch('urllib.request.Request')

        # Test outlet 0 (too low)
        with pytest.raises(ValueError, match='Invalid outlet number'):
            get_outlet('192.168.1.100', 0, 'admin', 'admin')

        # Test outlet 3 (too high for 2-outlet PDU)
        with pytest.raises(ValueError, match='Invalid outlet number'):
            get_outlet('192.168.1.100', 3, 'admin', 'admin')


class TestGetAllStatus:
    """Tests for get_all_status function."""

    def test_get_all_status_mixed(self, mocker):
        """Test reading all outlet states when mixed (outlet 1 ON, outlet 2 OFF)."""
        # Mock the response - outlet 1 is ON, outlet 2 is OFF
        mock_response = MagicMock()
        mock_response.read.return_value = b'$A0,01,0.05,XX'
        mock_response.__enter__.return_value = mock_response
        mock_response.__exit__.return_value = None

        mock_urlopen = mocker.patch('urllib.request.urlopen', return_value=mock_response)
        mock_request = mocker.patch('urllib.request.Request')

        status = get_all_status('192.168.1.100', 'admin', 'admin')

        assert status['outlet1'] is True
        assert status['outlet2'] is False
        assert status['current'] == 0.05

        # Verify Request was created with correct URL
        mock_request.assert_called_once()
        call_args = mock_request.call_args[0]
        assert call_args[0] == 'http://192.168.1.100/cmd.cgi?$A5'

        # Verify urlopen was called with timeout
        mock_urlopen.assert_called_once()
        assert mock_urlopen.call_args[1]['timeout'] == 5

    def test_get_all_status_both_on(self, mocker):
        """Test reading all outlet states when both ON."""
        # Mock the response - both outlets ON
        mock_response = MagicMock()
        mock_response.read.return_value = b'$A0,11,1.23,XX'
        mock_response.__enter__.return_value = mock_response
        mock_response.__exit__.return_value = None

        mocker.patch('urllib.request.urlopen', return_value=mock_response)
        mocker.patch('urllib.request.Request')

        status = get_all_status('192.168.1.100', 'admin', 'admin')

        assert status['outlet1'] is True
        assert status['outlet2'] is True
        assert status['current'] == 1.23

    def test_get_all_status_both_off(self, mocker):
        """Test reading all outlet states when both OFF."""
        # Mock the response - both outlets OFF
        mock_response = MagicMock()
        mock_response.read.return_value = b'$A0,00,0.00,XX'
        mock_response.__enter__.return_value = mock_response
        mock_response.__exit__.return_value = None

        mocker.patch('urllib.request.urlopen', return_value=mock_response)
        mocker.patch('urllib.request.Request')

        status = get_all_status('192.168.1.100', 'admin', 'admin')

        assert status['outlet1'] is False
        assert status['outlet2'] is False
        assert status['current'] == 0.0

    def test_get_all_status_http_error(self, mocker):
        """Test HTTP error handling."""
        import urllib.error

        # Mock HTTP error
        mock_urlopen = mocker.patch('urllib.request.urlopen')
        mock_urlopen.side_effect = urllib.error.HTTPError(
            url='http://192.168.1.100/cmd.cgi?$A5',
            code=401,
            msg='Unauthorized',
            hdrs={},
            fp=None
        )
        mocker.patch('urllib.request.Request')

        with pytest.raises(RuntimeError, match='HTTP error 401'):
            get_all_status('192.168.1.100', 'admin', 'admin')

    def test_get_all_status_invalid_format(self, mocker):
        """Test invalid response format handling."""
        # Mock response with too few fields
        mock_response = MagicMock()
        mock_response.read.return_value = b'$A0,01'  # Missing current field
        mock_response.__enter__.return_value = mock_response
        mock_response.__exit__.return_value = None

        mocker.patch('urllib.request.urlopen', return_value=mock_response)
        mocker.patch('urllib.request.Request')

        with pytest.raises(RuntimeError, match='Invalid PDU response format'):
            get_all_status('192.168.1.100', 'admin', 'admin')

    def test_get_all_status_invalid_current(self, mocker):
        """Test handling of invalid current value."""
        # Mock response with non-numeric current field
        mock_response = MagicMock()
        mock_response.read.return_value = b'$A0,01,INVALID,XX'
        mock_response.__enter__.return_value = mock_response
        mock_response.__exit__.return_value = None

        mocker.patch('urllib.request.urlopen', return_value=mock_response)
        mocker.patch('urllib.request.Request')

        status = get_all_status('192.168.1.100', 'admin', 'admin')

        # Should default to 0.0 when current is invalid
        assert status['outlet1'] is True
        assert status['outlet2'] is False
        assert status['current'] == 0.0
