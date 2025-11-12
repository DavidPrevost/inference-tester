# LLM Inference Tester

A comprehensive testing tool for evaluating the **practical performance limits** of LLM inference on mini PCs and edge devices. Unlike theoretical benchmarks, this tool measures real-world usability across different use cases.

## Purpose

When running LLMs locally on resource-constrained hardware, there's often a significant gap between what *technically runs* and what's *actually usable*. This tool bridges that gap by:

- Testing multiple model sizes and quantization levels systematically
- Measuring performance across diverse real-world use cases
- Providing clear interpretations of technical metrics
- Identifying the practical limits of your hardware
- Recommending optimal configurations for specific workflows

## Target Hardware

Designed for testing mini PCs and edge devices. Reference configuration:
- **CPU**: Intel N100 (or similar low-power processors)
- **RAM**: 16GB
- **Storage**: 512GB SSD

The tool adapts its testing based on available resources and provides actionable insights for your specific hardware.

## Key Features

### Smart Testing Matrix
- Tests combinations of model sizes (1B-13B+) and quantization levels (Q2-Q8)
- Automatically skips impossible configurations (memory constraints)
- Intelligently terminates testing paths that won't meet usability thresholds
- Continues exploring promising configurations more deeply

### Real-World Use Case Profiles

1. **Interactive Storytelling** - Streaming speed and responsiveness for creative work
2. **Long Context Management** - Large context handling for complex workflows
3. **Batch Document Processing** - Throughput and stability for bulk operations
4. **Accuracy/Quality** - Model capability preservation across quantizations
5. **System Stress** - Sustained load and thermal behavior

### Practical Metrics Translation

Goes beyond raw numbers to explain real-world implications:
- "10 tokens/sec = comfortable reading speed"
- "60s context load = coffee break territory"
- "14GB memory usage = system will struggle with other apps"

### Comprehensive Reporting
- **JSON/CSV** - Machine-readable detailed metrics
- **HTML Report** - Human-friendly visualizations and recommendations
- **Progress Tracking** - Resume interrupted tests
- **Comparison Data** - Understand tradeoffs between configurations

## Use Cases This Tool Supports

This tool helps you determine if your hardware can handle:

- **Long-form text generation** (novella/novel-length storytelling)
- **Context-aware story management** (lorebooks, character rosters, plot tracking)
- **Document parsing and tagging** (multi-format document processing)
- **Document generation** (exportable content creation)
- **Financial analysis** (accuracy-critical computations)
- **Image generation prompting** (context-aware image integration)

## Quick Start

### Prerequisites

- Python 3.8+
- llama.cpp server binary ([installation guide](https://github.com/ggerganov/llama.cpp))
- Sufficient disk space for models (~5-50GB depending on configuration)

### Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/inference-tester.git
cd inference-tester

# Install dependencies
pip install -r requirements.txt

# Configure your environment
cp config.example.yaml config.yaml
# Edit config.yaml with your llama.cpp path and preferences
```

### Basic Usage

```bash
# Quick test (Q4/Q5 quantizations only, ~1 hour)
python src/main.py --quick

# Full test (all quantizations, ~2-4 hours)
python src/main.py --full

# Resume an interrupted test
python src/main.py --resume results/20240115_120000_results.json

# Test specific profiles only
python src/main.py --profiles interactive,long_context
```

### View Results

Results are saved in the `results/` directory:
- `{timestamp}_results.json` - Complete raw data
- `{timestamp}_results.csv` - Tabular metrics
- `{timestamp}_report.html` - Open in browser for visual report

## Configuration

The tool uses two main configuration files:

### `config.yaml` - Test Settings

Control test behavior, thresholds, and output preferences:

```yaml
llama_cpp:
  server_path: "./llama-server"

test_mode: "full"  # or "quick"

thresholds:
  interactive:
    min_tokens_per_sec: 2
    max_time_to_first_token: 30
  long_context:
    max_initial_load_time: 60
```

See [config.example.yaml](config.example.yaml) for full options.

### `models.yaml` - Model Selection

Specify which models and quantizations to test:

```yaml
models:
  - name: "Qwen2.5-1.5B-Instruct"
    size: "1B"
    repo: "Qwen/Qwen2.5-1.5B-Instruct-GGUF"
    files:
      Q4_K_M: "qwen2.5-1.5b-instruct-q4_k_m.gguf"
```

See [models.example.yaml](models.example.yaml) for complete examples.

## Understanding Results

### Performance Classifications

Each configuration is rated based on measured performance:

- **Excellent** ⭐⭐⭐ - Exceeds all thresholds, highly responsive
- **Good** ⭐⭐ - Meets thresholds comfortably, fully usable
- **Acceptable** ⭐ - Meets minimum thresholds, usable with patience
- **Poor** ❌ - Below thresholds, frustrating to use
- **Failed** 💥 - Unable to load or run

### Key Metrics Explained

**Tokens per Second (t/s)**:
- `2-5 t/s`: Slow but readable, like careful dictation
- `10-15 t/s`: Comfortable reading speed
- `20-30 t/s`: Fast, feels very responsive
- `40+ t/s`: Nearly instant for most prompts

**Time to First Token (TTFT)**:
- `<2s`: Feels instant
- `2-10s`: Noticeable pause but acceptable
- `10-30s`: Significant wait, breaks flow
- `>30s`: Unusable for interactive work

**Context Load Time**:
- `<5s`: Smooth workflow
- `5-30s`: Brief pause, manageable
- `30-60s`: Coffee break territory
- `>60s`: Too slow for practical use

**Memory Usage**:
- `<8GB`: Room for other applications
- `8-12GB`: Dedicated inference, some headroom
- `12-14GB`: Most of system RAM, limited multitasking
- `>14GB`: Swapping likely, severe performance degradation

## Development

See [DEVELOPMENT.md](DEVELOPMENT.md) for:
- Development practices and guidelines
- How to add new test profiles
- How to extend the tool
- Testing and contribution guidelines

## Architecture

See [DESIGN.md](DESIGN.md) for:
- Detailed architecture overview
- Design decisions and rationale
- Component interactions
- Testing strategy details

## Roadmap

See [ROADMAP.md](ROADMAP.md) for:
- Implementation phases
- Current status
- Planned features
- Future enhancements

## License

MIT License - see [LICENSE](LICENSE) for details

## Acknowledgments

- Built for testing with [llama.cpp](https://github.com/ggerganov/llama.cpp)
- Inspired by practical needs in real-world edge deployment scenarios
- Focused on bridging the gap between theoretical and practical performance

## Support

- **Issues**: Report bugs or request features via GitHub Issues
- **Discussions**: Share results and discuss configurations
- **Pull Requests**: Contributions welcome! See DEVELOPMENT.md

---

**Note**: This tool is designed to help you find your hardware's sweet spot. Results will vary based on your specific hardware, models tested, and use case requirements. The goal is to provide actionable data for informed decision-making.
