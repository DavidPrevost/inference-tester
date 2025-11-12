"""Server lifecycle management for llama.cpp server.

This module handles spawning, monitoring, and terminating llama.cpp server
instances. It manages server configuration, health checks, and cleanup.
"""

import logging
import os
import signal
import socket
import subprocess
import time
from pathlib import Path
from typing import Optional

from utils.http import check_health

logger = logging.getLogger(__name__)


class ServerConnection:
    """Represents a connection to a running llama.cpp server."""

    def __init__(self, url: str, port: int, process: subprocess.Popen):
        """Initialize server connection.

        Args:
            url: Base URL of the server
            port: Port number
            process: Server process handle

        """
        self.url = url
        self.port = port
        self.process = process

    def is_ready(self) -> bool:
        """Check if server is ready to accept requests.

        Returns:
            True if server is responsive, False otherwise

        """
        if not self.is_running():
            return False

        return check_health(self.url, timeout=2)

    def is_running(self) -> bool:
        """Check if server process is still running.

        Returns:
            True if process is alive, False otherwise

        """
        return self.process.poll() is None


class ServerManager:
    """Manages llama.cpp server process lifecycle.

    Handles starting servers with appropriate configuration, monitoring
    their health, and ensuring clean shutdown.
    """

    def __init__(self, server_path: Path, default_ctx_size: int = 8192):
        """Initialize the ServerManager.

        Args:
            server_path: Path to llama-server binary
            default_ctx_size: Default context size for servers

        """
        self.server_path = Path(server_path)
        self.default_ctx_size = default_ctx_size
        self.current_connection: Optional[ServerConnection] = None

    def start(
        self,
        model_path: Path,
        ctx_size: Optional[int] = None,
        threads: Optional[int] = None,
        port: Optional[int] = None
    ) -> ServerConnection:
        """Start a llama.cpp server instance.

        Args:
            model_path: Path to GGUF model file
            ctx_size: Context size (uses default if None)
            threads: Number of threads (auto-detect if None)
            port: Port number (find available if None)

        Returns:
            ServerConnection to the running server

        Raises:
            RuntimeError: If server fails to start
            FileNotFoundError: If server binary or model not found

        """
        logger.info("Starting llama.cpp server with model: %s", model_path)

        # Stop any existing server
        if self.current_connection:
            logger.info("Stopping existing server first")
            self.stop()

        # Verify server binary exists
        if not self.server_path.exists():
            raise FileNotFoundError(f"Server binary not found: {self.server_path}")

        # Verify model exists
        model_path = Path(model_path)
        if not model_path.exists():
            raise FileNotFoundError(f"Model file not found: {model_path}")

        # Get port
        if port is None:
            port = self.get_available_port()

        # Get context size
        if ctx_size is None:
            ctx_size = self.default_ctx_size

        # Get threads (None means auto-detect)
        thread_args = []
        if threads is not None:
            thread_args = ["--threads", str(threads)]

        # Build command
        cmd = [
            str(self.server_path),
            "--model", str(model_path),
            "--ctx-size", str(ctx_size),
            "--port", str(port),
            "--host", "127.0.0.1",  # Localhost only for security
            *thread_args
        ]

        logger.debug("Server command: %s", " ".join(cmd))

        # Start process
        try:
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1
            )

            url = f"http://127.0.0.1:{port}"
            connection = ServerConnection(url, port, process)

            # Wait for server to be ready
            logger.info("Waiting for server to become ready...")
            if not self.wait_for_ready(connection, timeout=300):
                # Kill the process if it didn't start
                process.kill()
                process.wait()
                raise RuntimeError("Server failed to become ready within timeout")

            self.current_connection = connection
            logger.info("Server started successfully on port %d", port)
            return connection

        except Exception as e:
            logger.error("Failed to start server: %s", e)
            raise RuntimeError(f"Server startup failed: {e}")

    def stop(self, timeout: int = 30):
        """Stop the current server instance.

        Args:
            timeout: Maximum time to wait for graceful shutdown (seconds)

        """
        if not self.current_connection:
            logger.warning("No server to stop")
            return

        connection = self.current_connection
        logger.info("Stopping server on port %d", connection.port)

        if not connection.is_running():
            logger.info("Server process already terminated")
            self.current_connection = None
            return

        try:
            # Try graceful shutdown first (SIGTERM)
            logger.debug("Sending SIGTERM to server process")
            connection.process.terminate()

            # Wait for graceful shutdown
            start_time = time.time()
            while connection.is_running() and (time.time() - start_time) < timeout:
                time.sleep(0.5)

            # Force kill if still running
            if connection.is_running():
                logger.warning("Server didn't stop gracefully, sending SIGKILL")
                connection.process.kill()
                connection.process.wait(timeout=5)

            logger.info("Server stopped successfully")

        except Exception as e:
            logger.error("Error stopping server: %s", e)
            # Try force kill as last resort
            try:
                connection.process.kill()
                connection.process.wait(timeout=5)
            except:
                pass

        finally:
            self.current_connection = None

    def wait_for_ready(self, connection: ServerConnection, timeout: int = 300) -> bool:
        """Wait for server to become ready.

        Args:
            connection: Server connection to wait for
            timeout: Maximum time to wait (seconds)

        Returns:
            True if server became ready, False if timeout

        """
        logger.debug("Waiting for server to be ready (timeout: %ds)", timeout)

        start_time = time.time()
        check_interval = 2  # seconds

        while (time.time() - start_time) < timeout:
            # Check if process died
            if not connection.is_running():
                logger.error("Server process died during startup")
                return False

            # Check if server responds to health check
            if connection.is_ready():
                # Give it a moment to fully initialize
                time.sleep(2)
                logger.info("Server is ready!")
                return True

            # Wait before next check
            time.sleep(check_interval)

        logger.error("Server did not become ready within %d seconds", timeout)
        return False

    def get_available_port(self, start: int = 8080, end: int = 8180) -> int:
        """Find an available port in the given range.

        Args:
            start: Start of port range
            end: End of port range

        Returns:
            Available port number

        Raises:
            RuntimeError: If no available port found

        """
        for port in range(start, end + 1):
            try:
                # Try to bind to the port
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                    s.bind(('127.0.0.1', port))
                    logger.debug("Found available port: %d", port)
                    return port
            except OSError:
                # Port is in use, try next one
                continue

        raise RuntimeError(f"No available port found in range {start}-{end}")
