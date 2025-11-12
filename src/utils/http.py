"""HTTP utilities for communicating with llama.cpp server.

This module provides utilities for making HTTP requests to llama.cpp server,
handling streaming responses, and implementing retry logic.
"""

import json
import logging
import time
from typing import Any, Dict, Iterator, Optional

logger = logging.getLogger(__name__)


def send_completion_request(
    server_url: str,
    prompt: str,
    max_tokens: int = 512,
    temperature: float = 0.7,
    stream: bool = False,
    timeout: int = 300
) -> Dict[str, Any]:
    """Send a completion request to llama.cpp server.

    Args:
        server_url: Base URL of the server
        prompt: Prompt text
        max_tokens: Maximum tokens to generate
        temperature: Sampling temperature
        stream: Whether to stream the response
        timeout: Request timeout in seconds

    Returns:
        Response dictionary

    Raises:
        RuntimeError: If request fails

    """
    try:
        import requests

        endpoint = f"{server_url}/completion"
        payload = {
            "prompt": prompt,
            "n_predict": max_tokens,
            "temperature": temperature,
            "stream": stream
        }

        response = requests.post(
            endpoint,
            json=payload,
            timeout=timeout,
            stream=stream
        )
        response.raise_for_status()

        if stream:
            return {"response": response}
        else:
            return response.json()

    except ImportError:
        logger.error("requests library not available")
        raise RuntimeError("requests library required")
    except Exception as e:
        logger.error("Completion request failed: %s", e)
        raise RuntimeError(f"Request failed: {e}")


def stream_completion(
    server_url: str,
    prompt: str,
    max_tokens: int = 512,
    temperature: float = 0.7,
    timeout: int = 300
) -> Iterator[Dict[str, Any]]:
    """Stream completion tokens from llama.cpp server.

    Args:
        server_url: Base URL of the server
        prompt: Prompt text
        max_tokens: Maximum tokens to generate
        temperature: Sampling temperature
        timeout: Request timeout in seconds

    Yields:
        Dictionaries with token data

    """
    try:
        import requests

        endpoint = f"{server_url}/completion"
        payload = {
            "prompt": prompt,
            "n_predict": max_tokens,
            "temperature": temperature,
            "stream": True
        }

        response = requests.post(
            endpoint,
            json=payload,
            timeout=timeout,
            stream=True
        )
        response.raise_for_status()

        for line in response.iter_lines():
            if line:
                # Parse SSE format: "data: {json}"
                line_str = line.decode('utf-8')
                if line_str.startswith('data: '):
                    data_str = line_str[6:]  # Remove 'data: ' prefix
                    try:
                        data = json.loads(data_str)
                        yield data
                    except json.JSONDecodeError:
                        logger.warning("Failed to parse SSE data: %s", data_str)

    except ImportError:
        logger.error("requests library not available")
        raise RuntimeError("requests library required")
    except Exception as e:
        logger.error("Streaming request failed: %s", e)
        raise RuntimeError(f"Streaming failed: {e}")


def check_health(server_url: str, timeout: int = 5) -> bool:
    """Check if server is healthy and responsive.

    Args:
        server_url: Base URL of the server
        timeout: Request timeout in seconds

    Returns:
        True if server is healthy, False otherwise

    """
    try:
        import requests

        endpoint = f"{server_url}/health"
        response = requests.get(endpoint, timeout=timeout)
        return response.status_code == 200
    except ImportError:
        logger.error("requests library not available")
        return False
    except Exception as e:
        logger.debug("Health check failed: %s", e)
        return False


def retry_request(
    func,
    max_attempts: int = 3,
    delay: float = 1.0,
    backoff: float = 2.0
):
    """Retry a function with exponential backoff.

    Args:
        func: Function to retry (should take no arguments)
        max_attempts: Maximum number of attempts
        delay: Initial delay in seconds
        backoff: Backoff multiplier

    Returns:
        Result from successful function call

    Raises:
        Exception from last failed attempt

    """
    last_error = None
    current_delay = delay

    for attempt in range(max_attempts):
        try:
            return func()
        except Exception as e:
            last_error = e
            if attempt < max_attempts - 1:
                logger.warning(
                    f"Attempt {attempt + 1} failed: {e}. "
                    f"Retrying in {current_delay}s..."
                )
                time.sleep(current_delay)
                current_delay *= backoff

    raise last_error
