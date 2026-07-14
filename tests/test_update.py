"""
Tests for the HiveOS Update Checker (CL-03).

Tests cover:
- UpdateInfo data class & properties
- Version parsing (_parse_version)
- UpdateChecker with mocked GitHub API responses
- Network error handling
- Bad JSON / missing fields
"""

from __future__ import annotations

import json
from unittest.mock import patch, MagicMock
from urllib.error import URLError

import pytest

from hiveos.update import UpdateChecker, UpdateInfo
from hiveos.update.checker import _parse_version


# ═══════════════════════════════════════════════════════════════════════
# _parse_version
# ═══════════════════════════════════════════════════════════════════════

class TestParseVersion:
    def test_simple_semver(self):
        assert _parse_version("0.9.1") == (0, 9, 1, 999, 0)

    def test_major_minor_patch(self):
        assert _parse_version("1.2.3") == (1, 2, 3, 999, 0)

    def test_with_alpha(self):
        assert _parse_version("0.10.0-alpha.1") == (0, 10, 0, 0, 1)

    def test_with_beta(self):
        assert _parse_version("1.0.0-beta.2") == (1, 0, 0, 1, 2)

    def test_with_rc(self):
        assert _parse_version("2.0.0-rc.3") == (2, 0, 0, 2, 3)

    def test_invalid_raises(self):
        with pytest.raises(ValueError):
            _parse_version("not-a-version")
        with pytest.raises(ValueError):
            _parse_version("abc")

    def test_comparison_upgrade(self):
        assert _parse_version("0.10.0") > _parse_version("0.9.1")
        assert _parse_version("1.0.0") > _parse_version("0.99.99")
        assert _parse_version("0.9.2") > _parse_version("0.9.1")

    def test_pre_release_lower_than_release(self):
        assert _parse_version("0.10.0") > _parse_version("0.10.0-alpha.1")
        assert _parse_version("0.10.0-rc.1") < _parse_version("0.10.0")


# ═══════════════════════════════════════════════════════════════════════
# UpdateInfo
# ═══════════════════════════════════════════════════════════════════════

class TestUpdateInfo:
    def test_no_update_available(self):
        info = UpdateInfo(current_version="0.9.1", latest_version="0.9.1")
        assert not info.update_available
        assert info.is_current

    def test_update_available(self):
        info = UpdateInfo(current_version="0.9.1", latest_version="0.10.0")
        assert info.update_available
        assert not info.is_current

    def test_newer_is_not_update(self):
        info = UpdateInfo(current_version="0.10.0", latest_version="0.9.1")
        assert not info.update_available
        # is_current should be True when local version >= latest (dev scenario)
        assert info.is_current

    def test_error_no_update_available(self):
        info = UpdateInfo(current_version="0.9.1", error="Network error")
        assert not info.update_available
        assert not info.is_current

    def test_none_latest_no_update(self):
        info = UpdateInfo(current_version="0.9.1", latest_version=None)
        assert not info.update_available


# ═══════════════════════════════════════════════════════════════════════
# UpdateChecker — mocked
# ═══════════════════════════════════════════════════════════════════════

def _mock_github_response(tag_name: str, body: str = "Bug fixes.") -> bytes:
    """Simulate GitHub API JSON response bytes."""
    return json.dumps({
        "tag_name": tag_name,
        "html_url": f"https://github.com/hossein1377mobini/hiveos-financial-brain/releases/tag/{tag_name}",
        "body": body,
    }).encode("utf-8")


def _make_mock_response(data: bytes) -> MagicMock:
    """Create a MagicMock that works as a context manager for urlopen."""
    mock = MagicMock()
    mock.__enter__.return_value = mock
    mock.read.return_value = data
    return mock


class TestUpdateChecker:
    def test_up_to_date(self):
        """Current version matches latest release."""
        mock_resp = _make_mock_response(_mock_github_response("v0.9.1"))

        with patch("hiveos.update.checker.urlopen", return_value=mock_resp) as mock_urlopen:
            checker = UpdateChecker(current_version="0.9.1")
            info = checker.check()

            mock_urlopen.assert_called_once()
            assert info.current_version == "0.9.1"
            assert info.latest_version == "0.9.1"
            assert not info.update_available
            assert info.is_current
            assert info.error is None

    def test_update_available(self):
        """A newer version exists on GitHub."""
        mock_resp = _make_mock_response(_mock_github_response("v0.10.0", "Lots of new stuff!"))

        with patch("hiveos.update.checker.urlopen", return_value=mock_resp):
            checker = UpdateChecker(current_version="0.9.1", api_url="https://example.com/api")
            info = checker.check()

            assert info.current_version == "0.9.1"
            assert info.latest_version == "0.10.0"
            assert info.update_available
            assert info.download_url is not None
            assert "0.10.0" in info.download_url
            assert info.release_notes == "Lots of new stuff!"
            assert info.error is None

    def test_patch_version_behind(self):
        """Minor patch behind still counts as update."""
        mock_resp = _make_mock_response(_mock_github_response("v0.9.2"))

        with patch("hiveos.update.checker.urlopen", return_value=mock_resp):
            checker = UpdateChecker(current_version="0.9.1")
            info = checker.check()

            assert info.update_available
            assert info.latest_version == "0.9.2"

    def test_network_error(self):
        """URLError produces an UpdateInfo with error message, not an exception."""
        with patch("hiveos.update.checker.urlopen", side_effect=URLError("Connection refused")):
            checker = UpdateChecker(current_version="0.9.1")
            info = checker.check()

            assert info.error is not None
            assert "Connection refused" in info.error
            assert not info.update_available
            assert info.latest_version is None

    def test_bad_json_response(self):
        """Non-JSON response handled gracefully."""
        mock_resp = _make_mock_response(b"not json at all")

        with patch("hiveos.update.checker.urlopen", return_value=mock_resp):
            checker = UpdateChecker(current_version="0.9.1")
            info = checker.check()

            assert info.error is not None
            assert "JSON" in info.error or "error" in info.error
            assert not info.update_available

    def test_missing_tag_name(self):
        """API response without tag_name field is handled."""
        mock_resp = _make_mock_response(json.dumps({"html_url": "/releases"}).encode("utf-8"))

        with patch("hiveos.update.checker.urlopen", return_value=mock_resp):
            checker = UpdateChecker(current_version="0.9.1")
            info = checker.check()

            assert info.latest_version is None
            assert not info.update_available

    def test_timeout_applied(self):
        """Checker passes timeout to urlopen."""
        mock_resp = _make_mock_response(_mock_github_response("v0.10.0"))

        with patch("hiveos.update.checker.urlopen", return_value=mock_resp) as mock_urlopen:
            checker = UpdateChecker(current_version="0.9.1", timeout=3)
            checker.check()

            _call_timeout = mock_urlopen.call_args[1].get("timeout")
            assert _call_timeout == 3

    def test_format_message_up_to_date(self):
        """check_and_notify returns 'up-to-date' message."""
        mock_resp = _make_mock_response(_mock_github_response("v0.9.1"))

        with patch("hiveos.update.checker.urlopen", return_value=mock_resp):
            checker = UpdateChecker(current_version="0.9.1")
            msg = checker.check_and_notify()
            assert "up-to-date" in msg.lower() or "0.9.1" in msg

    def test_format_message_update_available(self):
        """check_and_notify returns upgrade message."""
        mock_resp = _make_mock_response(_mock_github_response("v0.10.0"))

        with patch("hiveos.update.checker.urlopen", return_value=mock_resp):
            checker = UpdateChecker(current_version="0.9.1")
            msg = checker.check_and_notify()
            assert "update" in msg.lower() or "0.10.0" in msg

    def test_format_message_error(self):
        """check_and_notify returns error message."""
        with patch("hiveos.update.checker.urlopen", side_effect=URLError("timeout")):
            checker = UpdateChecker(current_version="0.9.1")
            msg = checker.check_and_notify()
            assert "timeout" in msg or "error" in msg.lower() or "fail" in msg.lower()
