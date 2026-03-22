<!-- conversation_id: sample_conversation_123 -->
---
title: "Python Code Review Session"
export_date: "2026-03-21 14:30:00"
message_count: 6
---

# Python Code Review Session

**User:**

Can you review this Python function for best practices?

```python
def get_data(url, params={}):
    response = requests.get(url, params)
    return response.json()
```

**Gemini:**

<small>2026-03-21 14:30:15</small>

I'll review your function for best practices. Here are some suggestions:

## 1. Add Type Hints

```python
import requests
from typing import Any

def get_data(url: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
    if params is None:
        params = {}
    response = requests.get(url, params=params)
    response.raise_for_status()
    return response.json()
```

## 2. Handle Errors Gracefully

Consider catching potential exceptions:

```python
def get_data(url: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
    try:
        response = requests.get(url, params=params or {})
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        raise RuntimeError(f"Failed to fetch data: {e}") from e
```

## 3. Add Docstring

```python
def get_data(url: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
    """Fetch JSON data from a URL.

    Args:
        url: The endpoint URL to request.
        params: Optional query parameters.

    Returns:
        The JSON response as a dictionary.

    Raises:
        RuntimeError: If the request fails.
    """
    ...
```

## Key Improvements Summary

| Issue | Original | Improved |
|-------|----------|----------|
| Mutable default | `params={}` | `params=None` |
| Type hints | Missing | Full type annotations |
| Error handling | None | raise_for_status() + try/except |
| Docstring | None | Google-style docstring |

**User:**

Thanks! What about adding a timeout parameter?

**Gemini:**

<small>2026-03-21 14:31:00</small>

Good idea! Here's the updated version with timeout:

```python
import requests
from typing import Any

def get_data(
    url: str,
    params: dict[str, Any] | None = None,
    timeout: float | tuple[float, float] = 5.0
) -> dict[str, Any]:
    """Fetch JSON data from a URL with timeout support.

    Args:
        url: The endpoint URL to request.
        params: Optional query parameters.
        timeout: Request timeout in seconds. Can be a single value
                 or tuple (connect_timeout, read_timeout).

    Returns:
        The JSON response as a dictionary.

    Raises:
        RuntimeError: If the request fails or times out.
    """
    try:
        response = requests.get(url, params=params or {}, timeout=timeout)
        response.raise_for_status()
        return response.json()
    except requests.Timeout:
        raise RuntimeError(f"Request timed out after {timeout}s") from None
    except requests.RequestException as e:
        raise RuntimeError(f"Failed to fetch data: {e}") from e
```

**Usage Examples:**

```python
# Basic usage
data = get_data("https://api.example.com/users")

# With query params
data = get_data("https://api.example.com/search", {"q": "python"})

# With custom timeout (10 seconds)
data = get_data("https://api.example.com/slow", timeout=10.0)

# With separate connect/read timeouts
data = get_data("https://api.example.com/", timeout=(2.0, 10.0))
```

The timeout parameter prevents your application from hanging indefinitely on slow or unresponsive endpoints.

**User:**

Perfect! One more question - how would you add retry logic with exponential backoff?

**Gemini:**

<small>2026-03-21 14:32:30</small>

Here's an implementation with retry logic using exponential backoff:

```python
import requests
import time
from typing import Any

def get_data_with_retry(
    url: str,
    params: dict[str, Any] | None = None,
    max_retries: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 30.0
) -> dict[str, Any]:
    """Fetch JSON data with automatic retry on failure.

    Args:
        url: The endpoint URL to request.
        params: Optional query parameters.
        max_retries: Maximum number of retry attempts.
        base_delay: Initial delay between retries in seconds.
        max_delay: Maximum delay cap between retries.

    Returns:
        The JSON response as a dictionary.

    Raises:
        RuntimeError: If all retry attempts fail.
    """
    last_exception: Exception | None = None

    for attempt in range(max_retries + 1):
        try:
            response = requests.get(url, params=params or {}, timeout=5.0)
            response.raise_for_status()
            return response.json()
        except (requests.Timeout, requests.ConnectionError) as e:
            last_exception = e
            if attempt < max_retries:
                delay = min(base_delay * (2 ** attempt), max_delay)
                time.sleep(delay)
        except requests.RequestException as e:
            raise RuntimeError(f"Request failed: {e}") from e

    raise RuntimeError(f"All {max_retries} retries exhausted") from last_exception
```

## Retry Strategy Visualization

```
Attempt 1: Immediate
Attempt 2: Wait 1s
Attempt 3: Wait 2s
Attempt 4: Wait 4s
... (capped at max_delay)
```

## When to Use Retries

| Scenario | Retry? | Reason |
|----------|--------|--------|
| Connection error | Yes | Temporary network issue |
| Timeout | Yes | Server may be temporarily busy |
| 404 Not Found | No | Resource doesn't exist |
| 500 Server Error | Yes | Temporary server issue |
| 401 Unauthorized | No | Credentials are invalid |

This pattern is especially useful for:
- Production APIs with reliability requirements
- Batch operations processing many requests
- Microservices communicating over networks
