# Development Guide

This document outlines development practices, coding standards, and guidelines for contributing to the LLM Inference Tester project.

## Table of Contents

1. [Development Philosophy](#development-philosophy)
2. [Code Organization](#code-organization)
3. [Coding Standards](#coding-standards)
4. [Testing Strategy](#testing-strategy)
5. [Adding New Test Profiles](#adding-new-test-profiles)
6. [Adding New Models](#adding-new-models)
7. [Error Handling](#error-handling)
8. [Logging](#logging)
9. [Performance Considerations](#performance-considerations)
10. [Documentation](#documentation)
11. [Git Workflow](#git-workflow)
12. [Debugging](#debugging)

## Development Philosophy

### Core Values

1. **Clarity over Cleverness**: Write code that's easy to understand and maintain
2. **Fail Gracefully**: Errors should never leave the system in a broken state
3. **User First**: Every feature should make the tool easier to use
4. **Data Integrity**: Never lose test results or corrupt data
5. **Resource Respect**: Don't waste CPU, memory, or time
6. **Modularity**: Components should be independently testable and reusable

### Design Patterns

**Composition over Inheritance**: Prefer composing functionality from smaller components rather than deep inheritance hierarchies.

**Dependency Injection**: Pass dependencies (config, connections) explicitly rather than using globals.

**Interface Segregation**: Each module should have a clear, minimal interface.

## Code Organization

### Directory Structure

```
src/
├── main.py                 # CLI entry point, argument parsing
├── config_manager.py       # Configuration loading and validation
├── model_manager.py        # Model download and management
├── server_manager.py       # llama.cpp server lifecycle
├── matrix_runner.py        # Test matrix execution and orchestration
├── metrics.py              # Metric collection and analysis
├── reporter.py             # Report generation (JSON/CSV/HTML)
├── utils/                  # Shared utilities
│   ├── __init__.py
│   ├── hardware.py         # Hardware detection (RAM, CPU, temp)
│   ├── format.py           # Formatting helpers
│   └── http.py             # HTTP client for server communication
└── test_profiles/          # Test profile implementations
    ├── __init__.py
    ├── base.py             # BaseProfile abstract class
    ├── interactive.py      # Interactive storytelling tests
    ├── long_context.py     # Long context tests
    ├── batch.py            # Batch processing tests
    ├── quality.py          # Quality/accuracy tests
    └── stress.py           # Stress/stability tests
```

### Module Responsibilities

Each module has a single, clear responsibility:

- **main.py**: CLI interface only, no business logic
- **config_manager.py**: Configuration I/O and validation only
- **model_manager.py**: Model file operations only
- **server_manager.py**: Process management only
- **matrix_runner.py**: Test orchestration only
- **metrics.py**: Metric calculation and interpretation only
- **reporter.py**: Output generation only
- **test_profiles/*.py**: Individual test logic only

### Import Structure

**Absolute imports** from src root:
```python
from config_manager import ConfigManager
from test_profiles.interactive import InteractiveProfile
from utils.hardware import get_available_memory
```

**No circular dependencies**: If two modules need each other, extract shared code to a third module.

## Coding Standards

### Python Version

**Minimum**: Python 3.8
**Target**: Python 3.10+

### Style Guide

Follow **PEP 8** with these specifics:

- **Line length**: 100 characters (not 79)
- **Indentation**: 4 spaces (no tabs)
- **Quotes**: Double quotes for strings, single quotes for short identifiers
- **Naming**:
  - `snake_case` for functions, variables, modules
  - `PascalCase` for classes
  - `UPPER_CASE` for constants
  - Descriptive names over abbreviations

### Type Hints

Use type hints for all function signatures:

```python
from typing import Dict, List, Optional, Tuple

def calculate_metrics(
    tokens: List[float],
    start_time: float,
    end_time: float
) -> Dict[str, float]:
    """Calculate performance metrics from token timings."""
    ...
```

Use `Optional[T]` for nullable values:
```python
def find_model(name: str) -> Optional[Path]:
    """Return model path or None if not found."""
    ...
```

### Docstrings

Use **Google-style docstrings** for all public functions and classes:

```python
def run_test(server_url: str, prompt: str, max_tokens: int) -> TestResult:
    """Run a single test against the LLM server.

    Args:
        server_url: Base URL of the llama.cpp server (e.g., "http://localhost:8080")
        prompt: The prompt text to send to the model
        max_tokens: Maximum number of tokens to generate

    Returns:
        TestResult object containing metrics and status

    Raises:
        ServerConnectionError: If server is unreachable
        TimeoutError: If generation exceeds timeout

    Example:
        >>> result = run_test("http://localhost:8080", "Hello", 100)
        >>> print(result.tokens_per_sec)
        15.3
    """
    ...
```

### Code Organization Within Files

Order within a module:
1. Module docstring
2. Imports (stdlib, third-party, local)
3. Constants
4. Classes
5. Functions
6. `if __name__ == "__main__":` block (if applicable)

Example:
```python
"""Module for managing llama.cpp server lifecycle."""

import logging
import subprocess
import time
from pathlib import Path
from typing import Optional

import requests

from utils.hardware import get_available_port

# Constants
DEFAULT_TIMEOUT = 300  # seconds
HEALTH_CHECK_INTERVAL = 2  # seconds

class ServerManager:
    """Manages llama.cpp server process lifecycle."""
    ...

def wait_for_server(url: str, timeout: int = DEFAULT_TIMEOUT) -> bool:
    """Wait for server to become ready."""
    ...
```

## Testing Strategy

### Test Structure

```
tests/
├── unit/                   # Unit tests for individual modules
│   ├── test_config_manager.py
│   ├── test_model_manager.py
│   ├── test_metrics.py
│   └── ...
├── integration/            # Integration tests
│   ├── test_server_lifecycle.py
│   ├── test_profile_execution.py
│   └── ...
├── fixtures/               # Test data
│   ├── sample_config.yaml
│   ├── sample_models.yaml
│   └── mock_responses.json
└── conftest.py             # Pytest configuration
```

### Unit Tests

**Every module should have unit tests** covering:
- Normal operation
- Edge cases
- Error conditions
- Boundary values

Example:
```python
# tests/unit/test_metrics.py
import pytest
from metrics import calculate_tokens_per_sec, classify_performance

def test_calculate_tokens_per_sec_normal():
    """Test token/sec calculation with normal input."""
    result = calculate_tokens_per_sec(
        tokens=100,
        start_time=0.0,
        end_time=10.0
    )
    assert result == 10.0

def test_calculate_tokens_per_sec_zero_time():
    """Test handling of zero elapsed time."""
    with pytest.raises(ValueError, match="Elapsed time must be positive"):
        calculate_tokens_per_sec(100, 0.0, 0.0)

def test_classify_performance_excellent():
    """Test classification of excellent performance."""
    metrics = {"tokens_per_sec": 25.0, "ttft": 1.5}
    result = classify_performance(metrics, profile="interactive")
    assert result == "excellent"
```

### Integration Tests

Test component interactions:
```python
# tests/integration/test_server_lifecycle.py
def test_server_start_stop(tmp_path, sample_model):
    """Test complete server lifecycle."""
    manager = ServerManager(llama_server_path="/path/to/llama-server")

    # Start server
    connection = manager.start(model_path=sample_model)
    assert connection.is_ready()

    # Use server
    response = connection.generate("Test prompt")
    assert len(response) > 0

    # Stop server
    manager.stop()
    assert not connection.is_ready()
```

### Mocking

Use mocks for expensive operations:
```python
from unittest.mock import Mock, patch

@patch('model_manager.download_from_huggingface')
def test_model_download(mock_download):
    """Test model download without actually downloading."""
    mock_download.return_value = Path("/fake/model.gguf")

    manager = ModelManager(model_dir="/tmp/models")
    path = manager.ensure_model("test-model", "Q4_K_M")

    assert path.name == "model.gguf"
    mock_download.assert_called_once()
```

### Test Coverage

**Target**: 80%+ code coverage
- Run with: `pytest --cov=src --cov-report=html`
- Focus on critical paths (matrix runner, server management)
- Don't obsess over 100% - focus on meaningful tests

### Running Tests

```bash
# Run all tests
pytest

# Run specific test file
pytest tests/unit/test_metrics.py

# Run with coverage
pytest --cov=src --cov-report=term-missing

# Run with verbose output
pytest -v

# Run only integration tests
pytest tests/integration/
```

## Adding New Test Profiles

### Profile Template

All test profiles inherit from `BaseProfile`:

```python
# src/test_profiles/my_new_profile.py
"""Test profile for [specific use case]."""

import logging
from typing import Dict, Any

from test_profiles.base import BaseProfile, TestResult

logger = logging.getLogger(__name__)

class MyNewProfile(BaseProfile):
    """Test profile for [describe purpose].

    This profile tests [what it tests] by [how it tests].

    Metrics collected:
    - metric_1: Description
    - metric_2: Description

    Success criteria:
    - metric_1 threshold
    - metric_2 threshold
    """

    name = "my_new_profile"
    description = "Brief description for reports"

    def run(self, server_url: str, config: Dict[str, Any]) -> TestResult:
        """Execute the test profile.

        Args:
            server_url: URL of the llama.cpp server
            config: Profile-specific configuration from config.yaml

        Returns:
            TestResult with metrics and status
        """
        logger.info(f"Running {self.name} profile")

        try:
            # 1. Prepare test
            test_data = self._prepare_test_data(config)

            # 2. Execute test
            raw_metrics = self._execute_test(server_url, test_data)

            # 3. Calculate derived metrics
            metrics = self._calculate_metrics(raw_metrics)

            # 4. Classify result
            status = self._classify_result(metrics, config.get("thresholds", {}))

            return TestResult(
                profile=self.name,
                status=status,
                metrics=metrics,
                passed=status in ["excellent", "good", "acceptable"]
            )

        except Exception as e:
            logger.error(f"Profile {self.name} failed: {e}", exc_info=True)
            return TestResult(
                profile=self.name,
                status="error",
                metrics={},
                passed=False,
                error=str(e)
            )

    def _prepare_test_data(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Prepare test inputs."""
        ...

    def _execute_test(self, server_url: str, test_data: Dict) -> Dict[str, float]:
        """Execute the actual test."""
        ...

    def _calculate_metrics(self, raw_metrics: Dict) -> Dict[str, float]:
        """Calculate final metrics."""
        ...

    def _classify_result(
        self,
        metrics: Dict[str, float],
        thresholds: Dict[str, float]
    ) -> str:
        """Classify as excellent/good/acceptable/poor/failed."""
        ...
```

### BaseProfile Interface

```python
# src/test_profiles/base.py
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Dict, Any, Optional

@dataclass
class TestResult:
    """Result from a test profile execution."""
    profile: str
    status: str  # excellent, good, acceptable, poor, failed, error
    metrics: Dict[str, float]
    passed: bool
    error: Optional[str] = None
    interpretation: Optional[Dict[str, str]] = None

class BaseProfile(ABC):
    """Abstract base class for all test profiles."""

    name: str = "base"
    description: str = "Base profile"

    @abstractmethod
    def run(self, server_url: str, config: Dict[str, Any]) -> TestResult:
        """Execute the test profile."""
        pass

    def validate_config(self, config: Dict[str, Any]) -> bool:
        """Validate profile-specific configuration."""
        return True

    def get_required_context_size(self) -> int:
        """Return minimum context size needed for this profile."""
        return 2048  # Default

    def interpret_metrics(self, metrics: Dict[str, float]) -> Dict[str, str]:
        """Convert metrics to human-readable interpretations."""
        return {}
```

### Registering New Profiles

Add to `test_profiles/__init__.py`:
```python
from test_profiles.interactive import InteractiveProfile
from test_profiles.long_context import LongContextProfile
from test_profiles.batch import BatchProfile
from test_profiles.quality import QualityProfile
from test_profiles.stress import StressProfile
from test_profiles.my_new_profile import MyNewProfile  # Add here

# Registry of all available profiles
PROFILES = {
    "interactive": InteractiveProfile,
    "long_context": LongContextProfile,
    "batch": BatchProfile,
    "quality": QualityProfile,
    "stress": StressProfile,
    "my_new_profile": MyNewProfile,  # Add here
}

def get_profile(name: str) -> BaseProfile:
    """Get profile instance by name."""
    if name not in PROFILES:
        raise ValueError(f"Unknown profile: {name}")
    return PROFILES[name]()
```

### Configuration for New Profile

Add section to `config.yaml`:
```yaml
thresholds:
  # ... existing profiles ...

  my_new_profile:
    metric_1_threshold: 100
    metric_2_threshold: 50
```

## Adding New Models

### Step 1: Identify Model Details

Find on HuggingFace:
- Repository name (e.g., `Qwen/Qwen2.5-1.5B-Instruct-GGUF`)
- Available quantization files
- File naming pattern

### Step 2: Add to models.yaml

```yaml
models:
  # ... existing models ...

  - name: "New-Model-Name"
    size: "7B"  # For categorization: 1B, 3B, 7B, 13B, etc.
    repo: "username/repository-name-GGUF"
    base_filename: "new-model-name"  # Common prefix
    files:
      Q2_K: "new-model-name-q2_k.gguf"
      Q3_K_M: "new-model-name-q3_k_m.gguf"
      Q4_K_M: "new-model-name-q4_k_m.gguf"
      Q5_K_M: "new-model-name-q5_k_m.gguf"
      Q6_K: "new-model-name-q6_k.gguf"
      Q8_0: "new-model-name-q8_0.gguf"
    metadata:  # Optional
      context_length: 8192
      special_notes: "Good for code generation"
```

### Step 3: (Optional) Add Model-Specific Handling

If the model requires special handling (unusual chat template, specific parameters):

```python
# src/model_manager.py

MODEL_SPECIAL_CASES = {
    "New-Model-Name": {
        "chat_template": "custom",
        "default_system_prompt": "You are a helpful assistant.",
        "eos_token": "</s>",
    }
}
```

### Step 4: Test

```bash
# Test that the model can be downloaded and loaded
python src/main.py --models "New-Model-Name" --quants Q4_K_M --quick
```

## Error Handling

### Principles

1. **Catch specific exceptions**, not bare `except:`
2. **Log errors with context** (what were we trying to do?)
3. **Clean up resources** in finally blocks or context managers
4. **Propagate or handle**, don't silently swallow errors
5. **User-friendly messages** in CLI output, technical details in logs

### Exception Hierarchy

```python
# src/exceptions.py
"""Custom exceptions for inference-tester."""

class InferenceTesterError(Exception):
    """Base exception for all inference-tester errors."""
    pass

class ConfigurationError(InferenceTesterError):
    """Configuration is invalid or missing."""
    pass

class ModelError(InferenceTesterError):
    """Model-related error (download, load, etc.)."""
    pass

class ServerError(InferenceTesterError):
    """Server failed to start or respond."""
    pass

class TestError(InferenceTesterError):
    """Test execution failed."""
    pass

class ResourceError(InferenceTesterError):
    """Insufficient resources (memory, disk, etc.)."""
    pass
```

### Error Handling Patterns

**Resource cleanup**:
```python
from contextlib import contextmanager

@contextmanager
def managed_server(model_path: Path):
    """Context manager for server lifecycle."""
    manager = ServerManager()
    connection = None
    try:
        connection = manager.start(model_path)
        yield connection
    finally:
        if connection:
            manager.stop()

# Usage
with managed_server(model_path) as connection:
    run_tests(connection)
# Server automatically stopped even if tests fail
```

**Retry logic**:
```python
import time
from typing import Callable, TypeVar

T = TypeVar('T')

def retry(
    func: Callable[[], T],
    max_attempts: int = 3,
    delay: float = 1.0,
    backoff: float = 2.0
) -> T:
    """Retry a function with exponential backoff."""
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

# Usage
result = retry(lambda: download_model(url), max_attempts=3)
```

**Graceful degradation**:
```python
def run_all_profiles(server_url: str) -> Dict[str, TestResult]:
    """Run all profiles, continuing even if some fail."""
    results = {}

    for profile_name in enabled_profiles:
        try:
            profile = get_profile(profile_name)
            result = profile.run(server_url, config)
            results[profile_name] = result
        except Exception as e:
            logger.error(f"Profile {profile_name} failed: {e}", exc_info=True)
            results[profile_name] = TestResult(
                profile=profile_name,
                status="error",
                metrics={},
                passed=False,
                error=str(e)
            )

    return results
```

## Logging

### Configuration

```python
# src/main.py
import logging
from pathlib import Path

def setup_logging(level: str = "INFO", log_file: Path = None):
    """Configure logging for the application."""
    handlers = [logging.StreamHandler()]  # Console

    if log_file:
        handlers.append(logging.FileHandler(log_file))

    logging.basicConfig(
        level=getattr(logging, level.upper()),
        format="%(asctime)s [%(levelname)8s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        handlers=handlers
    )

    # Reduce noise from third-party libraries
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("requests").setLevel(logging.WARNING)
```

### Usage

```python
import logging

logger = logging.getLogger(__name__)

def some_function():
    logger.debug("Detailed debug information")
    logger.info("Normal operation message")
    logger.warning("Something unexpected but handled")
    logger.error("Error occurred", exc_info=True)  # Include traceback
    logger.critical("Fatal error, cannot continue")
```

### Logging Levels

- **DEBUG**: Detailed diagnostic information (variable values, step-by-step progress)
- **INFO**: Normal operation milestones (test started, model loaded, etc.)
- **WARNING**: Unexpected but handled situations (retrying download, skipping test)
- **ERROR**: Errors that prevent specific operations (test failed, model won't load)
- **CRITICAL**: Fatal errors requiring shutdown (config missing, disk full)

### What to Log

**DO log**:
- Test progress (which model/quant being tested)
- Performance metrics at INFO level
- Configuration loaded
- Server start/stop events
- Errors with context
- Retry attempts
- Resource warnings (high memory, temperature)

**DON'T log**:
- Sensitive data (if any)
- Entire model outputs at INFO level (use DEBUG)
- Every HTTP request (too verbose)
- Redundant information

## Performance Considerations

### Memory Management

**Stream large responses**:
```python
import requests

def stream_generation(url: str, prompt: str):
    """Stream tokens instead of buffering entire response."""
    response = requests.post(
        f"{url}/completion",
        json={"prompt": prompt, "stream": True},
        stream=True
    )

    for line in response.iter_lines():
        if line:
            yield parse_sse_line(line)
```

**Clean up large objects**:
```python
def process_large_results(results: List[Dict]):
    """Process results and free memory incrementally."""
    for result in results:
        process_one_result(result)
        del result  # Explicit cleanup

    import gc
    gc.collect()  # Force garbage collection if needed
```

### I/O Optimization

**Batch file operations**:
```python
def download_models(model_list: List[str]):
    """Download multiple models efficiently."""
    # Download in parallel (but respect rate limits)
    from concurrent.futures import ThreadPoolExecutor

    with ThreadPoolExecutor(max_workers=3) as executor:
        futures = [
            executor.submit(download_one_model, model)
            for model in model_list
        ]

        for future in futures:
            future.result()  # Wait for all downloads
```

**Use generators for large datasets**:
```python
def load_test_prompts(file_path: Path):
    """Load prompts one at a time, not all at once."""
    with open(file_path) as f:
        for line in f:
            yield json.loads(line)

# Usage
for prompt in load_test_prompts(data_file):
    process_prompt(prompt)
# Memory usage stays constant
```

### Profiling

Use profiling to find bottlenecks:

```bash
# Profile with cProfile
python -m cProfile -o profile.stats src/main.py

# View results
python -m pstats profile.stats
>>> sort cumulative
>>> stats 20

# Or use snakeviz for visual profiling
pip install snakeviz
snakeviz profile.stats
```

## Documentation

### Code Comments

**When to comment**:
- Why you made a non-obvious decision
- Workarounds for bugs/limitations
- Complex algorithms
- TODOs and FIXMEs

**When NOT to comment**:
- Obvious code (comment says same thing as code)
- Redundant with docstring
- Outdated information

**Good comments**:
```python
# Using Q4_K_M as baseline because it's most common and well-tested
baseline_quant = "Q4_K_M"

# Workaround: llama.cpp server needs 2s after startup to be fully ready
# even though /health returns 200. See issue #123
time.sleep(2)

# TODO(username): Add support for custom chat templates (issue #456)
```

**Bad comments**:
```python
# Increment counter
counter += 1

# Call the function
result = calculate_metrics()
```

### README Files

Each major component can have a README:
- `src/test_profiles/README.md` - How test profiles work
- `data/README.md` - Description of test data files

### Changelog

Keep `CHANGELOG.md` updated:
```markdown
# Changelog

## [Unreleased]
### Added
- New quality test profile for accuracy evaluation

### Changed
- Improved memory estimation algorithm

### Fixed
- Server shutdown timeout issue

## [0.1.0] - 2024-01-15
### Added
- Initial release
- Basic test profiles (interactive, long_context, batch)
- HTML report generation
```

## Git Workflow

### Branch Strategy

- `main` - Stable, working code
- `develop` - Integration branch for features
- `feature/description` - Individual features
- `fix/description` - Bug fixes

### Commit Messages

Follow conventional commits:

```
type(scope): Short description

Longer explanation if needed.

Fixes #123
```

**Types**:
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code formatting (no logic change)
- `refactor`: Code restructuring (no behavior change)
- `test`: Adding or updating tests
- `chore`: Maintenance tasks

**Examples**:
```
feat(quality): Add math accuracy test profile

Implements basic math word problem testing to evaluate
quantization impact on mathematical reasoning.

Closes #42
```

```
fix(server): Handle graceful shutdown timeout

Server was hanging on shutdown when model was mid-generation.
Now sends SIGTERM, waits 30s, then SIGKILL if needed.

Fixes #67
```

### Pull Request Process

1. Create feature branch from `develop`
2. Implement changes with tests
3. Update documentation
4. Run full test suite
5. Open PR against `develop`
6. Address review feedback
7. Squash commits if needed
8. Merge when approved

## Debugging

### Debug Mode

Run with debug logging:
```bash
python src/main.py --log-level DEBUG
```

### Common Issues

**Server won't start**:
- Check llama-server binary path in config
- Verify port is available (`lsof -i :8080`)
- Check server logs in output directory
- Try running llama-server manually

**Out of memory**:
- Check available RAM before test
- Reduce context size in config
- Skip larger models
- Close other applications

**Tests timing out**:
- Increase timeout in config
- Check CPU isn't thermal throttling
- Verify network (if downloading models)
- Check disk isn't full

**Inconsistent results**:
- CPU throttling between runs
- Other processes competing for resources
- Different random seeds (if applicable)
- Model file corruption (re-download)

### Diagnostic Tools

```bash
# Check system resources
free -h                    # Memory
df -h                      # Disk space
top                        # CPU usage
sensors                    # Temperature (if available)

# Check processes
ps aux | grep llama        # Find llama-server processes
lsof -i :8080             # Check port usage

# Check logs
tail -f inference-tester.log
tail -f results/model_name_stderr.log
```

### Interactive Debugging

Use `pdb` for debugging:
```python
import pdb

def problematic_function():
    result = some_calculation()
    pdb.set_trace()  # Debugger stops here
    return process(result)
```

Or use `breakpoint()` (Python 3.7+):
```python
def problematic_function():
    result = some_calculation()
    breakpoint()  # Debugger stops here
    return process(result)
```

## Development Checklist

Before submitting code:

- [ ] Code follows style guide (run `black` and `flake8`)
- [ ] All functions have type hints
- [ ] All public functions have docstrings
- [ ] Unit tests added for new functionality
- [ ] All tests pass (`pytest`)
- [ ] Documentation updated (README, DESIGN, etc.)
- [ ] CHANGELOG.md updated
- [ ] No debug print statements left in code
- [ ] No commented-out code (use git history instead)
- [ ] Error messages are helpful and actionable
- [ ] Logging is appropriate (level and content)

## Code Review Guidelines

When reviewing PRs:

**Check for**:
- Correctness: Does it work as intended?
- Clarity: Is the code easy to understand?
- Testing: Are there adequate tests?
- Error handling: Are errors handled gracefully?
- Performance: Any obvious inefficiencies?
- Documentation: Is it documented?
- Consistency: Follows project conventions?

**Provide**:
- Specific, actionable feedback
- Suggestions, not just criticism
- Praise for good solutions
- Links to relevant documentation

**Avoid**:
- Nitpicking style (use automated tools)
- Bike-shedding (debating trivial details)
- Blocking on personal preference
- Harsh or dismissive language

## Getting Help

- Check existing documentation (this file, DESIGN.md, README.md)
- Search issues on GitHub
- Review code comments and docstrings
- Ask in discussions or create an issue

---

Happy coding! Remember: **clarity, modularity, and user-first design**.
