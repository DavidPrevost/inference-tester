"""Tests for shutdown module."""

import pytest
from shutdown import is_shutdown_requested, request_shutdown, reset_shutdown


class TestShutdown:
    """Tests for graceful shutdown functionality."""

    def setup_method(self):
        """Reset shutdown flag before each test."""
        reset_shutdown()

    def teardown_method(self):
        """Reset shutdown flag after each test."""
        reset_shutdown()

    def test_initial_state_is_not_requested(self):
        """Test that initial shutdown state is False."""
        assert is_shutdown_requested() is False

    def test_request_shutdown_sets_flag(self):
        """Test that request_shutdown sets the flag to True."""
        assert is_shutdown_requested() is False

        request_shutdown()

        assert is_shutdown_requested() is True

    def test_reset_shutdown_clears_flag(self):
        """Test that reset_shutdown clears the flag."""
        request_shutdown()
        assert is_shutdown_requested() is True

        reset_shutdown()

        assert is_shutdown_requested() is False

    def test_multiple_requests_remain_true(self):
        """Test that multiple shutdown requests keep flag True."""
        request_shutdown()
        request_shutdown()
        request_shutdown()

        assert is_shutdown_requested() is True
