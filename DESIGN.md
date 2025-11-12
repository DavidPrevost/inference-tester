# Design Document

This document outlines the architecture, design decisions, and technical approach for the LLM Inference Tester.

## Table of Contents

1. [Design Philosophy](#design-philosophy)
2. [Architecture Overview](#architecture-overview)
3. [Use Case Profiles](#use-case-profiles)
4. [Testing Matrix Strategy](#testing-matrix-strategy)
5. [Smart Termination Logic](#smart-termination-logic)
6. [Metrics and Translations](#metrics-and-translations)
7. [Configuration System](#configuration-system)
8. [Model Management](#model-management)
9. [Server Lifecycle](#server-lifecycle)
10. [Reporting System](#reporting-system)
11. [Data Flow](#data-flow)

## Design Philosophy

### Core Principles

1. **Practical Over Theoretical**: Measure real-world usability, not just technical capability
2. **Intelligent Testing**: Avoid wasting time on configurations that won't work
3. **User-Friendly**: Translate technical metrics into understandable implications
4. **Modular**: Easy to add new tests, models, or metrics
5. **Safe**: Never damage hardware or push systems past safe limits
6. **Resumable**: Long tests should be interruptible and resumable
7. **Configurable**: Users control thresholds and priorities

### Goals

- Identify the **sweet spot** for different use cases on specific hardware
- Provide **actionable recommendations** rather than raw data dumps
- Enable **informed decision-making** about model selection and quantization
- **Save time** by avoiding futile testing paths

## Architecture Overview

### Component Structure

```
┌─────────────────────────────────────────────────────────────┐
│                         CLI Entry                           │
│                       (main.py)                             │
└──────────────────┬──────────────────────────────────────────┘
                   │
                   ├─► ConfigManager ──► Load config.yaml, models.yaml
                   │
                   ├─► ModelManager ──► Download, verify, manage models
                   │
                   ├─► MatrixRunner ──┐
                   │                  │
                   │    ┌─────────────┴─────────────┐
                   │    │ For each model/quant:     │
                   │    │  1. Memory pre-check      │
                   │    │  2. Start ServerManager   │
                   │    │  3. Run test profiles     │
                   │    │  4. Collect metrics       │
                   │    │  5. Early termination?    │
                   │    │  6. Stop server           │
                   │    └───────────────────────────┘
                   │                  │
                   │    ┌─────────────▼─────────────┐
                   │    │ Test Profiles:            │
                   │    │  - InteractiveProfile     │
                   │    │  - LongContextProfile     │
                   │    │  - BatchProfile           │
                   │    │  - QualityProfile         │
                   │    │  - StressProfile          │
                   │    └───────────────────────────┘
                   │                  │
                   └─► MetricsCollector ◄───────────┘
                                     │
                                     ▼
                   ┌─────────────────────────────────┐
                   │         Reporter                │
                   │  - JSON output                  │
                   │  - CSV output                   │
                   │  - HTML report                  │
                   └─────────────────────────────────┘
```

### Module Responsibilities

#### `main.py`
- CLI argument parsing
- Orchestrate overall test flow
- Handle interruptions and resume logic
- Display progress to user

#### `config_manager.py`
- Load and validate configuration files
- Provide default values
- Merge user config with defaults
- Validate threshold values

#### `model_manager.py`
- Track which models are already downloaded
- Download models from HuggingFace when needed
- Verify model file integrity
- Provide model metadata (size, path, etc.)

#### `server_manager.py`
- Spawn llama.cpp server instances
- Configure server parameters (context size, threads, etc.)
- Health check server availability
- Gracefully terminate servers
- Capture server logs for debugging

#### `matrix_runner.py`
- Implement smart testing matrix
- Memory pre-checks before loading models
- Early termination logic
- Manage test progression through matrix
- Aggregate results across all tests

#### `test_profiles/base.py`
- Abstract base class for all test profiles
- Common interface: `run()`, `validate()`, `get_metrics()`
- Shared utility methods
- Metric collection helpers

#### `test_profiles/interactive.py`
- Test TTFT (Time to First Token)
- Measure streaming speed (tokens/sec)
- Short-form generation tests
- User-facing responsiveness metrics

#### `test_profiles/long_context.py`
- Test initial context load time
- Measure context processing speed
- Test behavior at max context
- Detect context-related performance degradation

#### `test_profiles/batch.py`
- Sequential document processing simulation
- Measure throughput (items/hour)
- Detect performance consistency (variance)
- Monitor for memory leaks or degradation
- Long-running stability

#### `test_profiles/quality.py`
- Run standardized test prompts
- Compare accuracy across quantizations
- Test math, reasoning, comprehension, formatting
- Flag significant quality degradation

#### `test_profiles/stress.py`
- Sustained load testing (30+ minutes)
- Monitor system temperature
- Detect thermal throttling
- Track swap usage
- Ensure system stability

#### `metrics.py`
- Collect performance metrics
- Calculate derived metrics
- Translate to real-world interpretations
- Classify performance levels
- Generate recommendations

#### `reporter.py`
- Format results as JSON
- Format results as CSV
- Generate HTML report with visualizations
- Create comparison tables
- Provide recommendations summary

## Use Case Profiles

Each profile tests different aspects of LLM performance relevant to specific use cases.

### 1. Interactive Storytelling Profile

**Purpose**: Test responsiveness for creative writing workflows

**Metrics**:
- Time to First Token (TTFT)
- Streaming speed (tokens/sec)
- Consistency of streaming speed

**Test Procedure**:
1. Send prompt requesting 500-token story continuation
2. Measure time until first token arrives
3. Measure average tokens/sec during generation
4. Measure variance in token timing

**Success Criteria**:
- TTFT ≤ 30 seconds
- Streaming ≥ 2 tokens/sec
- Consistent timing (low variance)

**Real-World Interpretation**:
- 2-5 t/s: "Slow but readable, like careful dictation"
- 10-15 t/s: "Comfortable reading speed"
- 20-30 t/s: "Fast reading, feels responsive"
- 40+ t/s: "Nearly instant for most prompts"

### 2. Long Context Management Profile

**Purpose**: Test ability to handle large context windows (lorebooks, character rosters, etc.)

**Metrics**:
- Initial context load time
- Maximum usable context size
- Memory usage
- Processing speed at various context sizes

**Test Procedure**:
1. Load progressively larger contexts: 4k, 8k, 16k, 32k, 64k tokens
2. Measure initial processing time for each
3. Attempt generation with each context size
4. Monitor memory usage and swap activity

**Success Criteria**:
- Initial load ≤ 60 seconds
- No swapping to disk
- Successful generation at target context size

**Real-World Interpretation**:
- <5s for 8k: "Smooth workflow"
- 10-30s for 16k: "Brief pause, manageable"
- 30-60s for 32k: "Coffee break territory"
- >60s: "Too slow for interactive work"

**Context Notes**:
- Context is loaded once per conversation in llama.cpp
- Subsequent generations just append tokens (fast)
- Exceeding max context requires reprocessing (expensive)

### 3. Batch Document Processing Profile

**Purpose**: Test throughput and stability for bulk operations

**Metrics**:
- Average time per document
- Standard deviation (consistency)
- Throughput (documents/hour)
- Memory usage over time
- Performance degradation (first 10 vs last 10)

**Test Procedure**:
1. Process 30 simulated documents sequentially
2. Each document is 200-500 token summary task
3. Measure time for each individual document
4. Track memory usage throughout
5. Compare early vs late performance

**Success Criteria**:
- Variance < 20% (consistent performance)
- No significant degradation over time
- No memory leaks
- Stable memory usage

**Real-World Interpretation**:
- 10 docs/hour: "Overnight batch jobs only"
- 30 docs/hour: "Reasonable for moderate batches"
- 60+ docs/hour: "Efficient bulk processing"

### 4. Accuracy/Quality Profile

**Purpose**: Ensure quantization doesn't unacceptably degrade model capabilities

**Metrics**:
- Accuracy on math problems (critical for financial work)
- Reading comprehension scores
- Logical reasoning ability
- Format-following compliance

**Test Procedure**:
1. Run 10-15 standardized test prompts covering:
   - Math word problems (3-4 questions)
   - Reading comprehension (3-4 questions)
   - Logical reasoning (3-4 questions)
   - Format following (2-3 questions)
2. Score responses automatically where possible
3. Compare scores across quantization levels

**Success Criteria**:
- Math: ≥80% correct (financial accuracy critical)
- Comprehension: ≥75% correct
- Reasoning: ≥75% correct
- Format: ≥90% compliance

**Real-World Interpretation**:
- "Q4 maintains 95% accuracy - safe for all uses"
- "Q3 drops to 70% on math - avoid for financial work"
- "Q2 shows significant degradation - creative use only"

**Implementation Notes**:
- This profile is OPTIONAL (can skip for performance-only testing)
- Test prompts bundled in `data/quality_tests.json`
- Quick to run (~5 min per model)
- Helps make quantization tradeoff decisions

### 5. System Stress Profile

**Purpose**: Ensure sustained operation doesn't cause thermal or stability issues

**Metrics**:
- CPU temperature over time
- Thermal throttling events
- Swap usage
- System responsiveness
- Sustained tokens/sec consistency

**Test Procedure**:
1. Select model based on earlier benchmark results (see below)
2. Run continuous generation for 30 minutes
3. Monitor system vitals every 30 seconds:
   - CPU temperature
   - CPU frequency (detect throttling)
   - Memory usage
   - Swap usage
4. Measure tokens/sec throughout
5. Check for performance degradation

**Model Selection for Stress Testing**:
- Use models that passed benchmark tests
- Prefer "next-to-last" or "last" passing configuration
- This ensures we stress the system without guaranteed failure
- Avoid testing models that already failed benchmarks

**Success Criteria**:
- Temperature ≤ 85°C
- No thermal throttling
- No swap usage
- Stable performance throughout
- System remains responsive

**Real-World Interpretation**:
- "System stays cool, suitable for 24/7 operation"
- "Temp hits 80°C but stable - ensure good airflow"
- "Thermal throttling after 15min - reduce load"

**Safety Notes**:
- Monitor temperature carefully
- Abort if temperature exceeds 90°C
- Abort if system becomes unresponsive
- This test runs LAST to avoid impacting other tests

## Testing Matrix Strategy

### The Matrix

We test combinations of model sizes and quantization levels:

```
         Q2_K   Q3_K_M  Q4_K_M  Q5_K_M  Q6_K   Q8_0
1B       [test] [test]  [test]  [test]  [test] [test]
3B       [test] [test]  [test]  [test]  [test] [test]
7B       [test] [test]  [test]  [test]  [skip] [skip]
13B      [skip] [test]  [test]  [skip]  [skip] [skip]
```

### Testing Order

**Traverse by quantization level** (test each quant level independently):

1. Test all viable model sizes at Q4_K_M first (baseline)
2. Then test all viable sizes at Q5_K_M
3. Then Q6_K, Q3_K_M, Q2_K, Q8_0

**Rationale**:
- Q4 is most common "sweet spot" - get this data first
- Testing all sizes at one quant level reveals trends
- Can identify "7B Q6 better than 3B Q8" patterns

### Example Test Sequence

```
1. Qwen2.5-1.5B Q4_K_M
2. Phi-3.5-mini Q4_K_M
3. Llama-3.2-7B Q4_K_M
4. Llama-2-13B Q4_K_M  (might fail memory check)
5. Qwen2.5-1.5B Q5_K_M
6. Phi-3.5-mini Q5_K_M
7. Llama-3.2-7B Q5_K_M
... and so on
```

## Smart Termination Logic

To avoid wasting hours on futile tests, implement multiple levels of early termination:

### 1. Pre-Flight Memory Check

**Before loading model**:
- Calculate estimated memory requirement
- Check available RAM
- If `model_size * 1.2 > available_ram`: SKIP

**Example**:
```
Llama-2-13B Q8_0 = ~13GB model
Estimated requirement: 13GB * 1.2 = 15.6GB
Available RAM: 14GB
Result: SKIP (would cause swapping)
```

### 2. Load Failure Detection

**During model loading**:
- Timeout after 5 minutes
- If load fails: SKIP remaining tests for this model
- Mark entire model as "too large" for this hardware

### 3. Performance Threshold Termination

**After initial test**:
- If TTFT > 30s: Mark as "failed"
- If tokens/sec < 2: Mark as "failed"
- Still run all profiles (to get complete data)
- Don't test larger models at same quant level

**Example**:
```
Llama-3.2-7B Q2_K: TTFT=45s, 1.5 t/s
Result: Mark as failed, skip Llama-2-13B Q2_K
```

### 4. Quantization Path Termination

**Pattern recognition**:
- If Q4, Q5, Q6 all fail for a model size
- SKIP Q8 (will definitely fail)
- If Q2, Q3 both fail for interactive profile
- Continue testing (might work for batch use)

### 5. Memory Trend Analysis

**Cross-test learning**:
- Track memory usage across tests
- Build model: `memory_used = f(model_size, quant_level)`
- Predict which future tests will fail
- SKIP predicted failures

**Example**:
```
Observed:
  7B Q4 → 5GB
  7B Q6 → 7GB
  13B Q4 → 9GB
Prediction:
  13B Q6 → ~11GB (OK)
  13B Q8 → ~15GB (SKIP)
```

### 6. Stress Test Model Selection

**Special logic for stress testing**:
- Don't stress test configurations that failed benchmarks
- Select from models that passed with "acceptable" or better ratings
- Prefer "next-to-last" passing config (stress without certain failure)

**Example**:
```
Results:
  3B Q4: Excellent
  3B Q6: Good
  7B Q4: Acceptable
  7B Q6: Failed

Stress test: Use 7B Q4 (last passing config)
```

### Termination Decision Tree

```
Load Model
    ├─► Pre-flight memory check fails → SKIP
    ├─► Load timeout (5min) → SKIP, mark model as too large
    └─► Loaded successfully
            ├─► Run all test profiles
            ├─► Collect metrics
            ├─► If all metrics below threshold → Mark FAILED
            ├─► If some metrics acceptable → Mark PARTIAL
            └─► If metrics good → Mark PASSED
                    └─► Continue testing matrix
```

## Metrics and Translations

### Raw Metrics Collected

**Performance Metrics**:
- Time to First Token (TTFT) - seconds
- Tokens per Second (t/s) - during streaming
- Token timing variance - standard deviation
- Context load time - seconds per token count
- Batch throughput - documents/hour
- Batch consistency - variance percentage

**Resource Metrics**:
- Model loading time - seconds
- Memory usage - GB (RSS, VSZ)
- Swap usage - GB
- CPU temperature - Celsius
- CPU frequency - MHz (detect throttling)
- Disk I/O - MB/s (during loading)

**Quality Metrics**:
- Accuracy scores - percentage per category
- Format compliance - pass/fail
- Response correctness - scored
- Degradation vs baseline - percentage

### Derived Metrics

**Efficiency Score** = `(tokens_per_sec * context_size) / memory_gb`
- Measures overall resource efficiency
- Higher is better
- Helps compare different configurations

**Usability Rating** = Categorical based on thresholds
- Excellent: All metrics exceed thresholds by 50%+
- Good: All metrics exceed thresholds by 20%+
- Acceptable: All metrics meet minimum thresholds
- Poor: Some metrics below threshold but functional
- Failed: Critical metrics below threshold

**Cost-Benefit Score** = `quality_score * performance_score / memory_score`
- Helps identify best tradeoffs
- Accounts for accuracy degradation
- Normalized 0-100

### Real-World Translation Table

| Metric | Value | Interpretation |
|--------|-------|----------------|
| **Tokens/sec** | | |
| | 2-5 t/s | Slow but readable, like careful dictation |
| | 5-10 t/s | Moderate pace, acceptable for patient users |
| | 10-15 t/s | Comfortable reading speed |
| | 15-20 t/s | Fast reading, feels responsive |
| | 20-30 t/s | Very fast, excellent UX |
| | 40+ t/s | Nearly instant for most prompts |
| **TTFT** | | |
| | <2s | Feels instant, excellent UX |
| | 2-5s | Barely noticeable pause |
| | 5-10s | Noticeable but acceptable |
| | 10-30s | Significant wait, breaks flow |
| | >30s | Frustrating, unusable for interactive |
| **Context Load** | | |
| | <5s | Smooth workflow |
| | 5-15s | Brief pause, manageable |
| | 15-30s | Noticeable delay |
| | 30-60s | Coffee break territory |
| | >60s | Too slow for practical use |
| **Memory** | | |
| | <6GB | Plenty of headroom |
| | 6-8GB | Room for other apps |
| | 8-12GB | Dedicated inference, some headroom |
| | 12-14GB | Most of system RAM |
| | >14GB | Swapping likely, severe degradation |
| **Batch Throughput** | | |
| | <10 docs/hour | Only for small batches |
| | 10-30 docs/hour | Overnight batch jobs |
| | 30-60 docs/hour | Reasonable for moderate batches |
| | 60-120 docs/hour | Efficient bulk processing |
| | >120 docs/hour | Excellent throughput |
| **Temperature** | | |
| | <70°C | Cool, no concerns |
| | 70-80°C | Warm but safe |
| | 80-85°C | Hot, ensure good airflow |
| | 85-90°C | Thermal limit approaching |
| | >90°C | Too hot, reduce load |

### Recommendation Generator

Based on collected metrics, generate specific recommendations:

**Example Output**:
```
RECOMMENDED CONFIGURATIONS:

Interactive Storytelling:
  ✓ Llama-3.2-7B Q4_K_M - Excellent (18 t/s, 2s TTFT)
  ✓ Phi-3.5-mini Q6_K - Good (22 t/s, 1.5s TTFT, better quality)
  ⚠ Qwen2.5-3B Q8_0 - Acceptable but slower (8 t/s)

Long Context Work (32k tokens):
  ✓ Phi-3.5-mini Q4_K_M - 25s load time, 9GB RAM
  ⚠ Llama-3.2-7B Q4_K_M - 45s load time, 12GB RAM (borderline)
  ✗ Any 13B model - Exceeds memory capacity

Document Processing (batch):
  ✓ Qwen2.5-3B Q4_K_M - 45 docs/hour, very stable
  ✓ Llama-3.2-7B Q4_K_M - 30 docs/hour, good quality

Financial Analysis (accuracy critical):
  ✓ Phi-3.5-mini Q6_K - 95% math accuracy
  ⚠ Phi-3.5-mini Q4_K_M - 88% math accuracy (acceptable)
  ✗ Any Q2 - Below 70% accuracy

Overall Best: Phi-3.5-mini Q4_K_M
  - Balanced performance across all use cases
  - 8GB RAM (allows multitasking)
  - Good accuracy retention
  - 15 t/s average, 2s TTFT
```

## Configuration System

### Two-File Approach

**`config.yaml`** - Test behavior and thresholds
**`models.yaml`** - Model definitions and selection

### config.yaml Structure

```yaml
# Where to find llama.cpp
llama_cpp:
  server_path: "./llama-server"  # Path to binary
  default_ctx_size: 8192          # Default context window
  default_threads: null           # null = auto-detect
  gpu_layers: 0                   # For GPU offloading (future)

# Test execution mode
test_mode: "full"  # Options: "quick", "full"
resume_from: null  # Path to results JSON to resume

# Which test profiles to run
profiles:
  - interactive
  - long_context
  - batch
  - quality      # Optional
  - stress       # Optional

# Performance thresholds (adjust for your needs)
thresholds:
  interactive:
    min_tokens_per_sec: 2
    max_time_to_first_token: 30
    max_variance: 20  # percent

  long_context:
    max_initial_load_time: 60
    test_sizes: [4096, 8192, 16384, 32768]

  batch:
    max_variance: 20  # percent
    num_documents: 30

  quality:
    min_math_score: 80  # percent
    min_comprehension_score: 75
    min_reasoning_score: 75
    min_format_compliance: 90

  stress:
    duration: 30  # minutes
    max_temperature: 85  # celsius
    sample_interval: 30  # seconds

# Resource limits
limits:
  max_memory_gb: 14  # Skip tests exceeding this
  max_load_time: 300  # Seconds (5 min)
  allow_swap: false   # Abort if swapping detected

# Model storage
model_dir: "./models"

# Output configuration
output:
  dir: "./results"
  formats: ["json", "csv", "html"]
  include_logs: true  # Include server logs in output

# Logging
logging:
  level: "INFO"  # DEBUG, INFO, WARNING, ERROR
  file: "inference-tester.log"
```

### models.yaml Structure

```yaml
# Model definitions
# Format: HuggingFace repo + specific GGUF files

models:
  - name: "Qwen2.5-1.5B-Instruct"
    size: "1B"  # For categorization
    repo: "Qwen/Qwen2.5-1.5B-Instruct-GGUF"
    base_filename: "qwen2.5-1.5b-instruct"
    files:
      Q2_K: "qwen2.5-1.5b-instruct-q2_k.gguf"
      Q3_K_M: "qwen2.5-1.5b-instruct-q3_k_m.gguf"
      Q4_K_M: "qwen2.5-1.5b-instruct-q4_k_m.gguf"
      Q5_K_M: "qwen2.5-1.5b-instruct-q5_k_m.gguf"
      Q6_K: "qwen2.5-1.5b-instruct-q6_k.gguf"
      Q8_0: "qwen2.5-1.5b-instruct-q8_0.gguf"

  - name: "Phi-3.5-mini-instruct"
    size: "3B"
    repo: "microsoft/Phi-3.5-mini-instruct-gguf"
    base_filename: "Phi-3.5-mini-instruct"
    files:
      Q4_K_M: "Phi-3.5-mini-instruct-q4.gguf"
      # ... etc

  - name: "Llama-3.2-3B-Instruct"
    size: "3B"
    repo: "lmstudio-community/Llama-3.2-3B-Instruct-GGUF"
    files:
      Q4_K_M: "Llama-3.2-3B-Instruct-Q4_K_M.gguf"
      # ... etc

  - name: "Llama-3.2-7B-Instruct"
    size: "7B"
    repo: "lmstudio-community/Llama-3.2-7B-Instruct-GGUF"
    files:
      Q4_K_M: "Llama-3.2-7B-Instruct-Q4_K_M.gguf"
      # ... etc

  - name: "Llama-2-13B-Chat"
    size: "13B"
    repo: "TheBloke/Llama-2-13B-Chat-GGUF"
    files:
      Q4_K_M: "llama-2-13b-chat.Q4_K_M.gguf"
      # ... etc

# Quick mode: only test these
quick_mode_quants: ["Q4_K_M", "Q5_K_M"]

# Full mode: test all defined quantizations
full_mode_quants: ["Q2_K", "Q3_K_M", "Q4_K_M", "Q5_K_M", "Q6_K", "Q8_0"]
```

### Configuration Validation

The `ConfigManager` validates:
- All paths exist and are accessible
- Threshold values are reasonable (positive, in expected ranges)
- Model files exist or can be downloaded
- Output directory is writable
- llama.cpp server binary exists and is executable

### Default Values

Sensible defaults are provided for all optional settings. Users only need to specify:
- `llama_cpp.server_path` (required)
- Any thresholds they want to customize
- Which models to test (or use built-in defaults)

## Model Management

### Model Discovery

On startup, `ModelManager`:
1. Scans `model_dir` for existing .gguf files
2. Matches found files against `models.yaml` definitions
3. Reports which models are available vs. need downloading

### Model Downloading

When a model is needed but not found:
1. Use HuggingFace Hub API to download specific file
2. Show progress bar during download
3. Verify file size after download
4. Calculate and store checksum
5. Move to final location in `model_dir`

**Download Priority**:
- Only download models actually needed for current test run
- In `--quick` mode, only download Q4/Q5 quants
- Allow `--dry-run` to preview what would be downloaded

### Model Metadata

Track for each model file:
- File path
- File size (MB)
- Estimated RAM requirement
- Quantization level
- Model family and size
- Download date
- Last tested date

### Storage Organization

```
models/
├── 1B/
│   ├── qwen2.5-1.5b-instruct-q4_k_m.gguf
│   └── qwen2.5-1.5b-instruct-q6_k.gguf
├── 3B/
│   ├── phi-3.5-mini-instruct-q4.gguf
│   └── llama-3.2-3b-instruct-q4_k_m.gguf
├── 7B/
│   └── llama-3.2-7b-instruct-q4_k_m.gguf
└── metadata.json
```

## Server Lifecycle

### Server Configuration

For each test, `ServerManager` spawns llama.cpp server with appropriate parameters:

```bash
./llama-server \
  --model {model_path} \
  --ctx-size {context_size} \
  --threads {num_threads} \
  --port {random_port} \
  --log-format text
```

### Server Startup

1. Select random available port (8080-8180 range)
2. Spawn server process
3. Wait for server to be ready (poll /health endpoint)
4. Timeout after 5 minutes if not ready
5. Return connection details to test profiles

### Server Health Checks

Periodically verify server is responsive:
- GET `/health` - should return 200 OK
- Check process is still running
- Monitor stderr for error messages

### Server Shutdown

After tests complete:
1. Send graceful shutdown signal (SIGTERM)
2. Wait up to 30 seconds for clean shutdown
3. If still running, force kill (SIGKILL)
4. Verify process terminated
5. Clean up any temp files

### Server Logs

Capture all server output:
- STDOUT → `{model}_{quant}_stdout.log`
- STDERR → `{model}_{quant}_stderr.log`
- Include in final report if `config.output.include_logs = true`
- Useful for debugging failures

## Reporting System

### Output Formats

#### JSON Output
Complete raw data structure:
```json
{
  "metadata": {
    "timestamp": "2024-01-15T14:30:00Z",
    "hostname": "mini-pc-01",
    "hardware": {
      "cpu": "Intel N100",
      "ram_gb": 16,
      "os": "Ubuntu 22.04"
    },
    "config": { ... },
    "test_duration_seconds": 7200
  },
  "results": [
    {
      "model": "Llama-3.2-7B-Instruct",
      "quantization": "Q4_K_M",
      "model_size_gb": 4.2,
      "profiles": {
        "interactive": {
          "status": "passed",
          "metrics": {
            "ttft_seconds": 2.3,
            "tokens_per_second": 18.5,
            "variance_percent": 8.2
          },
          "rating": "excellent"
        },
        ...
      }
    },
    ...
  ],
  "recommendations": { ... }
}
```

#### CSV Output
Flattened tabular format for spreadsheet analysis:
```csv
model,quant,size_gb,memory_gb,interactive_ttft,interactive_tps,interactive_rating,long_context_load,long_context_max,batch_throughput,...
Llama-3.2-7B,Q4_K_M,4.2,5.8,2.3,18.5,excellent,25.0,32768,28.5,...
```

#### HTML Report
Visual, interactive report with:
- Executive summary with top recommendations
- Performance comparison charts (bar/line graphs)
- Detailed tables for each model tested
- Color-coded ratings
- Tooltips with real-world interpretations
- Exportable/printable format

### Report Sections

**Executive Summary**:
- Hardware tested
- Test duration
- Models evaluated
- Top recommendations per use case
- Key findings

**Performance Overview**:
- Matrix view: all models × quants tested
- Color-coded heat map of performance
- Quick visual identification of sweet spots

**Detailed Results**:
- Per-model breakdown
- All metrics with interpretations
- Comparison to thresholds
- Specific recommendations

**Resource Analysis**:
- Memory usage patterns
- Temperature behavior
- Stability assessment

**Quality Analysis** (if quality tests run):
- Accuracy scores across quants
- Degradation patterns
- Safe quantization levels

**Appendices**:
- Full configuration used
- Server logs (if included)
- Raw metric dump

### Visualization Ideas

**Charts to include**:
- Tokens/sec vs Model Size (grouped by quant)
- Memory Usage vs Model Size
- Quality Score vs Quantization Level
- Temperature over Time (stress test)
- Context Size vs Load Time

**Interactive Elements** (HTML):
- Hover tooltips with interpretations
- Sortable tables
- Filterable views (by use case, rating, etc.)
- Expandable detail sections

## Data Flow

### Complete Test Flow

```
1. User runs: python src/main.py --full

2. main.py:
   ├─► Parse arguments
   ├─► ConfigManager.load_config()
   └─► ConfigManager.load_models()

3. ModelManager:
   ├─► Scan for existing models
   ├─► Determine what needs downloading
   ├─► Download missing models
   └─► Return model inventory

4. MatrixRunner.run():
   ├─► Generate test matrix
   ├─► For each (model, quant) combination:
   │   ├─► Pre-flight memory check
   │   │   └─► SKIP if insufficient RAM
   │   ├─► ServerManager.start(model, quant)
   │   │   ├─► Spawn llama-server
   │   │   ├─► Wait for ready
   │   │   └─► Return connection info
   │   ├─► For each enabled test profile:
   │   │   ├─► InteractiveProfile.run(connection)
   │   │   │   ├─► Send test prompts
   │   │   │   ├─► Measure TTFT, t/s
   │   │   │   └─► Return metrics
   │   │   ├─► LongContextProfile.run(connection)
   │   │   │   ├─► Test multiple context sizes
   │   │   │   ├─► Measure load times
   │   │   │   └─► Return metrics
   │   │   ├─► BatchProfile.run(connection)
   │   │   │   ├─► Process 30 documents
   │   │   │   ├─► Track consistency
   │   │   │   └─► Return metrics
   │   │   ├─► QualityProfile.run(connection)
   │   │   │   ├─► Run test questions
   │   │   │   ├─► Score responses
   │   │   │   └─► Return metrics
   │   │   └─► Collect all metrics
   │   ├─► MetricsCollector.analyze(metrics)
   │   │   ├─► Calculate derived metrics
   │   │   ├─► Classify performance
   │   │   ├─► Generate interpretations
   │   │   └─► Return analysis
   │   ├─► Early termination check
   │   │   └─► Decide if continue testing
   │   ├─► ServerManager.stop()
   │   │   └─► Gracefully shutdown server
   │   └─► Save checkpoint (for resume)
   └─► All tests complete

5. StressProfile (runs last):
   ├─► Select model based on prior results
   ├─► ServerManager.start(selected_model)
   ├─► Run sustained load (30 min)
   ├─► Monitor system vitals
   ├─► Return metrics
   └─► ServerManager.stop()

6. Reporter.generate():
   ├─► Load all collected metrics
   ├─► Generate recommendations
   ├─► Write JSON output
   ├─► Write CSV output
   └─► Write HTML report

7. Display summary to user
   └─► Point to generated reports
```

### State Management

**For resumability**, save state after each model tested:
```json
{
  "checkpoint": {
    "last_completed": "Llama-3.2-7B-Q4_K_M",
    "timestamp": "2024-01-15T14:30:00Z",
    "remaining": [
      "Llama-3.2-7B-Q5_K_M",
      "Llama-3.2-7B-Q6_K",
      ...
    ]
  },
  "results_so_far": [ ... ]
}
```

On `--resume`:
1. Load checkpoint file
2. Validate it matches current config
3. Skip already-tested combinations
4. Continue from next item in matrix

### Error Handling

**Graceful degradation**:
- If one test profile fails, continue with others
- If one model fails to load, continue with next
- Capture errors in results with status="error"
- Include error details in report

**Cleanup on interrupt** (Ctrl+C):
1. Catch SIGINT signal
2. Gracefully stop current server
3. Save checkpoint with current progress
4. Generate partial report from completed tests
5. Exit cleanly

## Security Considerations

### Model Downloads
- Verify HTTPS connections to HuggingFace
- Validate file sizes match expected
- Check file integrity (checksums if available)
- Warn on unexpected file sizes

### Server Execution
- Run llama-server with minimal privileges
- Bind to localhost only (no remote access)
- Use random ports to avoid conflicts
- Clean up processes on exit

### Resource Limits
- Never exceed configured memory limits
- Abort on excessive temperature
- Prevent disk space exhaustion (check before downloads)
- Timeout long-running operations

## Future Enhancements

Design with extensibility in mind for:

1. **GPU Testing**
   - Add GPU memory metrics
   - Test different layer offloading levels
   - Compare CPU vs GPU performance

2. **Additional Backends**
   - Support Ollama, vLLM, etc.
   - Abstract server interface
   - Backend-specific optimizations

3. **Multi-Model Comparisons**
   - Test same size class across families
   - Quality comparison beyond quantization
   - Recommendation by capability area

4. **Advanced Quality Tests**
   - Custom test prompts per use case
   - Fine-tuned model evaluation
   - Subjective quality ratings

5. **Real-Time Monitoring**
   - Web dashboard during testing
   - Live performance graphs
   - Remote progress tracking

6. **Automated Optimization**
   - Try different thread counts
   - Tune context sizes
   - Find optimal server parameters

## Design Validation

This design satisfies our key requirements:
- ✓ Tests practical usability, not just theoretical limits
- ✓ Supports diverse use cases with specific profiles
- ✓ Intelligent testing avoids wasting time
- ✓ Provides actionable recommendations
- ✓ Safe (won't damage hardware)
- ✓ Modular and extensible
- ✓ User-friendly configuration
- ✓ Comprehensive reporting

Ready for implementation!
