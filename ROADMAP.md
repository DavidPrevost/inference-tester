# Project Roadmap

This document outlines the implementation plan for the LLM Inference Tester, organized into phases with clear priorities and milestones.

## Table of Contents

1. [Project Phases](#project-phases)
2. [Phase 0: Foundation](#phase-0-foundation)
3. [Phase 1: Core Infrastructure](#phase-1-core-infrastructure)
4. [Phase 2: Basic Testing](#phase-2-basic-testing)
5. [Phase 3: Full Test Suite](#phase-3-full-test-suite)
6. [Phase 4: Smart Testing](#phase-4-smart-testing)
7. [Phase 5: Reporting](#phase-5-reporting)
8. [Phase 6: Polish & Optimization](#phase-6-polish--optimization)
9. [Future Enhancements](#future-enhancements)
10. [Success Criteria](#success-criteria)

## Project Phases

### Overview

```
Phase 0: Foundation (Setup)
   ↓
Phase 1: Core Infrastructure (Config, Models, Server)
   ↓
Phase 2: Basic Testing (One working test profile)
   ↓
Phase 3: Full Test Suite (All test profiles)
   ↓
Phase 4: Smart Testing (Matrix runner, early termination)
   ↓
Phase 5: Reporting (JSON, CSV, HTML output)
   ↓
Phase 6: Polish & Optimization (UX, performance)
```

### Principles

- **Incremental**: Each phase produces working, testable code
- **Vertical Slicing**: Each phase includes a complete feature end-to-end
- **Testing**: Tests written alongside implementation
- **Documentation**: Keep docs current as we build

---

## Phase 0: Foundation

**Goal**: Set up project structure and development environment

**Duration**: 1 session

### Tasks

- [x] Create comprehensive documentation
  - [x] README.md
  - [x] DESIGN.md
  - [x] DEVELOPMENT.md
  - [x] ROADMAP.md
- [ ] Create project structure
  - [ ] Directory layout
  - [ ] Empty module files with docstrings
  - [ ] `__init__.py` files
- [ ] Set up development environment
  - [ ] requirements.txt
  - [ ] requirements-dev.txt (testing tools)
  - [ ] .gitignore
  - [ ] pytest.ini
- [ ] Create example configuration files
  - [ ] config.example.yaml
  - [ ] models.example.yaml
- [ ] Set up git repository
  - [ ] Initial commit
  - [ ] Branch structure

### Deliverables

- ✓ Complete project documentation
- Complete project skeleton
- Development environment ready
- Git repository initialized

### Success Criteria

- All directories and files created
- Can import modules (even if empty)
- Tests run (even if none exist yet)
- Documentation is complete and accurate

---

## Phase 1: Core Infrastructure

**Goal**: Build foundational components for config, models, and server management

**Duration**: 2-3 sessions

### Tasks

#### Configuration Management

- [ ] Implement `ConfigManager` class
  - [ ] Load YAML configuration files
  - [ ] Validate configuration structure
  - [ ] Provide default values
  - [ ] Merge user config with defaults
  - [ ] Export configuration to dict
- [ ] Create `config.example.yaml` with all options
- [ ] Create `models.example.yaml` with sample models
- [ ] Write tests for ConfigManager
  - [ ] Valid config loading
  - [ ] Invalid config detection
  - [ ] Default value handling
  - [ ] Missing file handling

#### Model Management

- [ ] Implement `ModelManager` class
  - [ ] Scan for existing models in model_dir
  - [ ] Parse models.yaml
  - [ ] Match found files to model definitions
  - [ ] Calculate model metadata (size, quant level)
  - [ ] Estimate memory requirements
- [ ] Implement model downloading (basic)
  - [ ] Download from HuggingFace Hub
  - [ ] Show progress bar
  - [ ] Verify file size
  - [ ] Handle download failures
- [ ] Write tests for ModelManager
  - [ ] Model discovery
  - [ ] Metadata extraction
  - [ ] Memory estimation

#### Server Management

- [ ] Implement `ServerManager` class
  - [ ] Spawn llama-server process
  - [ ] Configure with appropriate parameters
  - [ ] Find available port
  - [ ] Wait for server ready
  - [ ] Health check endpoint
  - [ ] Graceful shutdown
  - [ ] Force kill if needed
  - [ ] Capture server logs
- [ ] Write tests for ServerManager
  - [ ] Start/stop lifecycle
  - [ ] Timeout handling
  - [ ] Port conflicts
  - [ ] Server crashes

#### Utilities

- [ ] Implement hardware utilities
  - [ ] Get available memory
  - [ ] Get CPU count
  - [ ] Get CPU temperature (if available)
  - [ ] Detect swap usage
- [ ] Implement HTTP utilities
  - [ ] Send requests to llama-server
  - [ ] Handle streaming responses
  - [ ] Retry logic
  - [ ] Timeout handling

### Deliverables

- Working ConfigManager
- Working ModelManager (scan + download)
- Working ServerManager (start/stop/health)
- Utility functions for hardware and HTTP
- Unit tests for all components
- Example configuration files

### Success Criteria

- Can load configuration from YAML
- Can discover and download models
- Can start and stop llama-server successfully
- Can detect hardware capabilities
- All tests pass
- Can run end-to-end: load config → download model → start server → stop server

---

## Phase 2: Basic Testing

**Goal**: Implement one complete test profile and prove the concept works

**Duration**: 2 sessions

### Tasks

#### Base Profile Class

- [ ] Implement `BaseProfile` abstract class
  - [ ] Abstract `run()` method
  - [ ] `validate_config()` method
  - [ ] `get_required_context_size()` method
  - [ ] `interpret_metrics()` helper
  - [ ] `TestResult` dataclass

#### Interactive Profile

- [ ] Implement `InteractiveProfile`
  - [ ] Generate test prompt
  - [ ] Send to server with streaming
  - [ ] Measure Time to First Token
  - [ ] Measure tokens per second
  - [ ] Calculate variance
  - [ ] Classify performance
  - [ ] Generate interpretations
- [ ] Write tests for InteractiveProfile
  - [ ] Mock server responses
  - [ ] Verify metric calculations
  - [ ] Test classification logic

#### Metrics System

- [ ] Implement basic `MetricsCollector`
  - [ ] Collect raw metrics from profiles
  - [ ] Calculate derived metrics
  - [ ] Classify performance (excellent/good/acceptable/poor/failed)
  - [ ] Generate real-world interpretations
- [ ] Define metric interpretation tables
  - [ ] Tokens/sec interpretations
  - [ ] TTFT interpretations
- [ ] Write tests for metrics
  - [ ] Calculation accuracy
  - [ ] Classification logic
  - [ ] Edge cases

#### Basic CLI

- [ ] Implement `main.py`
  - [ ] Parse command-line arguments
  - [ ] Setup logging
  - [ ] Orchestrate: config → model → server → test → results
  - [ ] Display results to user
  - [ ] Handle Ctrl+C gracefully
- [ ] Command-line arguments
  - [ ] `--config` path
  - [ ] `--models` filter
  - [ ] `--quants` filter
  - [ ] `--log-level`
  - [ ] `--output-dir`

### Deliverables

- Working BaseProfile class
- Working InteractiveProfile implementation
- Basic MetricsCollector
- Minimal CLI that can run one test
- Tests for all components

### Success Criteria

- Can run: `python src/main.py` and it completes one test
- Metrics are calculated correctly
- Results are displayed to user
- Tests pass
- **Proof of concept working end-to-end**

---

## Phase 3: Full Test Suite

**Goal**: Implement all test profiles for comprehensive testing

**Duration**: 3-4 sessions

### Tasks

#### Long Context Profile

- [ ] Implement `LongContextProfile`
  - [ ] Generate test contexts of varying sizes
  - [ ] Measure context processing time
  - [ ] Test multiple context sizes (4k, 8k, 16k, 32k)
  - [ ] Monitor memory usage during context load
  - [ ] Detect swapping
  - [ ] Classify results
- [ ] Write tests for LongContextProfile

#### Batch Profile

- [ ] Implement `BatchProfile`
  - [ ] Generate 30 simulated documents
  - [ ] Process sequentially
  - [ ] Measure time per document
  - [ ] Calculate variance (consistency)
  - [ ] Monitor memory over time
  - [ ] Detect performance degradation
  - [ ] Calculate throughput (docs/hour)
  - [ ] Classify results
- [ ] Write tests for BatchProfile

#### Quality Profile

- [ ] Create test question dataset
  - [ ] Math word problems (3-4)
  - [ ] Reading comprehension (3-4)
  - [ ] Logical reasoning (3-4)
  - [ ] Format following (2-3)
- [ ] Implement `QualityProfile`
  - [ ] Load test questions
  - [ ] Send to model
  - [ ] Score responses (automated where possible)
  - [ ] Calculate accuracy per category
  - [ ] Compare to baseline (Q8 or reference)
  - [ ] Flag significant degradation
  - [ ] Classify results
- [ ] Write tests for QualityProfile
- [ ] Add to `data/quality_tests.json`

#### Stress Profile

- [ ] Implement `StressProfile`
  - [ ] Model selection logic (based on prior results)
  - [ ] Continuous generation for 30 minutes
  - [ ] Monitor system vitals
    - [ ] CPU temperature
    - [ ] CPU frequency (throttling detection)
    - [ ] Memory usage
    - [ ] Swap usage
  - [ ] Measure sustained tokens/sec
  - [ ] Detect performance degradation
  - [ ] Abort on unsafe conditions (>90°C, unresponsive)
  - [ ] Classify results
- [ ] Write tests for StressProfile

#### Profile Integration

- [ ] Update profile registry in `test_profiles/__init__.py`
- [ ] CLI support for selecting profiles
  - [ ] `--profiles interactive,batch`
  - [ ] `--skip-quality` flag
  - [ ] `--skip-stress` flag
- [ ] Configuration for profile-specific thresholds

### Deliverables

- All 5 test profiles implemented
- Quality test dataset
- Profile selection via CLI
- Tests for all profiles

### Success Criteria

- Can run all profiles against a single model
- Each profile produces accurate metrics
- Results are classified appropriately
- All tests pass
- **Complete test coverage for all use cases**

---

## Phase 4: Smart Testing

**Goal**: Implement matrix runner with intelligent early termination

**Duration**: 2-3 sessions

### Tasks

#### Matrix Runner

- [ ] Implement `MatrixRunner` class
  - [ ] Generate test matrix from config
  - [ ] Order tests intelligently (Q4 first, by quant level)
  - [ ] Iterate through matrix
  - [ ] For each (model, quant):
    - [ ] Pre-flight memory check
    - [ ] Load model (via ServerManager)
    - [ ] Run enabled test profiles
    - [ ] Collect results
    - [ ] Evaluate termination criteria
    - [ ] Clean up
  - [ ] Aggregate all results

#### Smart Termination Logic

- [ ] Implement pre-flight checks
  - [ ] Memory estimation vs available RAM
  - [ ] Skip if insufficient memory
- [ ] Implement load timeout
  - [ ] 5-minute timeout for model loading
  - [ ] Skip remaining tests if load fails
- [ ] Implement performance thresholds
  - [ ] If TTFT > 30s, mark as poor
  - [ ] If t/s < 2, mark as poor
  - [ ] Skip larger models at same quant if failed
- [ ] Implement pattern recognition
  - [ ] Build memory usage model
  - [ ] Predict failures
  - [ ] Skip predicted failures
- [ ] Implement stress test model selection
  - [ ] Select from passing configurations
  - [ ] Prefer "next-to-last" passing config

#### Progress Tracking

- [ ] Implement progress display
  - [ ] Current model/quant being tested
  - [ ] Estimated time remaining
  - [ ] Progress bar
  - [ ] Live metrics (if possible)
- [ ] Implement checkpointing
  - [ ] Save progress after each model
  - [ ] Allow resume from checkpoint
  - [ ] `--resume` CLI flag

#### Test Modes

- [ ] Implement quick mode
  - [ ] Test only Q4_K_M and Q5_K_M
  - [ ] Skip stress testing
  - [ ] Estimated 1 hour runtime
- [ ] Implement full mode
  - [ ] Test all quantizations
  - [ ] Include stress testing
  - [ ] Estimated 2-4 hour runtime
- [ ] CLI flags: `--quick` or `--full`

### Deliverables

- Working MatrixRunner
- Smart termination logic
- Progress tracking and checkpointing
- Quick and full test modes
- Tests for matrix logic

### Success Criteria

- Can run full matrix without manual intervention
- Skips impossible configurations automatically
- Terminates futile test paths early
- Progress is saved and resumable
- Quick mode completes in ~1 hour
- **Fully automated, intelligent testing**

---

## Phase 5: Reporting

**Goal**: Generate comprehensive, useful reports in multiple formats

**Duration**: 2-3 sessions

### Tasks

#### Reporter Class

- [ ] Implement `Reporter` class
  - [ ] Load aggregated results
  - [ ] Generate recommendations
  - [ ] Format for different outputs
  - [ ] Write to files

#### JSON Output

- [ ] Implement JSON formatter
  - [ ] Complete data structure
  - [ ] Metadata (hardware, config, timestamp)
  - [ ] All test results
  - [ ] Metrics with interpretations
  - [ ] Recommendations
  - [ ] Pretty-printed (indented)
- [ ] Write to `{timestamp}_results.json`

#### CSV Output

- [ ] Implement CSV formatter
  - [ ] Flatten nested structure
  - [ ] One row per (model, quant) combination
  - [ ] Columns for each metric
  - [ ] Easy to import to spreadsheet
- [ ] Write to `{timestamp}_results.csv`

#### HTML Report

- [ ] Design HTML template
  - [ ] Clean, professional layout
  - [ ] Responsive (works on mobile)
  - [ ] Printable
- [ ] Implement HTML generator
  - [ ] Executive summary
    - [ ] Hardware info
    - [ ] Test duration
    - [ ] Top recommendations
  - [ ] Performance overview
    - [ ] Matrix heatmap
    - [ ] Charts (tokens/sec, memory, etc.)
  - [ ] Detailed results tables
    - [ ] Per-model breakdowns
    - [ ] Color-coded ratings
    - [ ] Tooltips with interpretations
  - [ ] Resource analysis
    - [ ] Memory usage patterns
    - [ ] Temperature behavior
  - [ ] Quality analysis (if run)
    - [ ] Accuracy scores
    - [ ] Degradation warnings
  - [ ] Appendices
    - [ ] Configuration used
    - [ ] Server logs (optional)
- [ ] Embedded CSS (no external dependencies)
- [ ] Embedded JavaScript for interactivity
  - [ ] Sortable tables
  - [ ] Filterable views
  - [ ] Expandable sections
- [ ] Write to `{timestamp}_report.html`

#### Recommendation Engine

- [ ] Implement recommendation logic
  - [ ] Best model for each use case
  - [ ] Overall best balanced model
  - [ ] Warnings about degradation
  - [ ] Specific advice (e.g., "avoid Q2 for financial work")
- [ ] Generate human-readable summaries

#### Charts and Visualizations

- [ ] Implement chart generation
  - [ ] Use Chart.js or similar (embedded)
  - [ ] Tokens/sec vs model size
  - [ ] Memory usage comparison
  - [ ] Quality scores vs quantization
  - [ ] Temperature over time (stress test)

### Deliverables

- Working Reporter class
- JSON output formatter
- CSV output formatter
- HTML report generator with visualizations
- Recommendation engine
- Example output files (from test data)

### Success Criteria

- All three formats generated correctly
- HTML report is attractive and useful
- Charts accurately represent data
- Recommendations are actionable
- Can open HTML in browser and it's readable
- **Professional, comprehensive reporting**

---

## Phase 6: Polish & Optimization

**Goal**: Improve user experience, performance, and robustness

**Duration**: 2-3 sessions

### Tasks

#### User Experience

- [ ] Improve CLI help text
  - [ ] Clear descriptions
  - [ ] Examples
  - [ ] Common workflows
- [ ] Better progress indicators
  - [ ] Colored output (optional, use colorama)
  - [ ] Clear status messages
  - [ ] Estimated time remaining
- [ ] Error messages
  - [ ] User-friendly, actionable
  - [ ] Suggest solutions
  - [ ] Point to documentation
- [ ] Configuration validation
  - [ ] Helpful error messages
  - [ ] Suggest fixes for common mistakes

#### Performance Optimization

- [ ] Profile the code
  - [ ] Identify bottlenecks
  - [ ] Optimize hot paths
- [ ] Optimize model downloads
  - [ ] Resume partial downloads
  - [ ] Parallel downloads (with limits)
- [ ] Optimize memory usage
  - [ ] Stream large responses
  - [ ] Clean up between tests
- [ ] Reduce startup time
  - [ ] Lazy load modules
  - [ ] Cache configuration validation

#### Robustness

- [ ] Handle edge cases
  - [ ] Very slow systems
  - [ ] Very fast systems (< 1s TTFT)
  - [ ] Extremely large models
  - [ ] Network failures during download
  - [ ] Corrupted model files
- [ ] Improve retry logic
  - [ ] Exponential backoff
  - [ ] Max retries
  - [ ] Better error handling
- [ ] Resource cleanup
  - [ ] Ensure servers are always stopped
  - [ ] Clean up temp files
  - [ ] Handle interrupted tests

#### Testing

- [ ] Increase test coverage
  - [ ] Target 80%+ coverage
  - [ ] Integration tests for full workflows
  - [ ] Edge case tests
- [ ] Add integration tests
  - [ ] Full test run (mocked)
  - [ ] Resume functionality
  - [ ] Report generation
- [ ] Add smoke tests
  - [ ] Quick validation of installation
  - [ ] Verify dependencies

#### Documentation

- [ ] Update all documentation
  - [ ] Ensure accuracy
  - [ ] Add examples
  - [ ] Add troubleshooting section
- [ ] Add inline code documentation
  - [ ] Complex algorithms explained
  - [ ] Non-obvious decisions documented
- [ ] Create video/GIF demos (optional)
  - [ ] Quick start
  - [ ] Interpreting results

### Deliverables

- Polished CLI with great UX
- Optimized performance
- Robust error handling
- High test coverage
- Complete, accurate documentation
- Troubleshooting guide

### Success Criteria

- Tool is pleasant to use
- No performance bottlenecks
- Handles errors gracefully
- Tests pass reliably
- Documentation is comprehensive
- **Production-ready quality**

---

## Future Enhancements

Features to consider after initial release:

### v1.1 - Extended Testing

- [ ] GPU support
  - [ ] Test with GPU offloading
  - [ ] Measure GPU memory usage
  - [ ] Compare CPU vs GPU performance
- [ ] Additional backends
  - [ ] Ollama support
  - [ ] vLLM support
  - [ ] LocalAI support
- [ ] Custom test prompts
  - [ ] User-provided test datasets
  - [ ] Domain-specific evaluations

### v1.2 - Advanced Analysis

- [ ] Multi-model family comparison
  - [ ] Compare Llama vs Mistral vs Qwen
  - [ ] Quality-adjusted performance rankings
- [ ] Historical tracking
  - [ ] Track performance over time
  - [ ] Compare hardware upgrades
  - [ ] Regression detection
- [ ] Cost analysis
  - [ ] Performance per watt
  - [ ] Performance per dollar
  - [ ] Optimal config for budget

### v1.3 - Automation

- [ ] Automated optimization
  - [ ] Auto-tune thread count
  - [ ] Find optimal context size
  - [ ] Optimize server parameters
- [ ] Continuous monitoring
  - [ ] Web dashboard
  - [ ] Real-time performance tracking
  - [ ] Alerting on degradation
- [ ] Cloud integration
  - [ ] Upload results to database
  - [ ] Compare against community benchmarks
  - [ ] Collaborative model recommendations

### v2.0 - Enterprise Features

- [ ] Multi-device testing
  - [ ] Test across multiple machines
  - [ ] Distributed testing
  - [ ] Fleet management
- [ ] Advanced reporting
  - [ ] Custom report templates
  - [ ] Interactive dashboards
  - [ ] Export to BI tools
- [ ] CI/CD integration
  - [ ] Automated regression testing
  - [ ] Performance gates
  - [ ] GitHub Actions support

---

## Success Criteria

### Minimum Viable Product (MVP)

After Phase 2, we have:
- ✓ Working configuration system
- ✓ Model download and management
- ✓ Server lifecycle management
- ✓ One complete test profile
- ✓ Basic metrics and reporting
- ✓ Can run end-to-end test

### Feature Complete (v1.0)

After Phase 5, we have:
- ✓ All test profiles implemented
- ✓ Smart matrix testing
- ✓ Early termination logic
- ✓ Comprehensive reporting (JSON/CSV/HTML)
- ✓ Actionable recommendations
- ✓ Resume capability
- ✓ Quick and full test modes

### Production Ready (v1.0 Final)

After Phase 6, we have:
- ✓ Polished user experience
- ✓ Optimized performance
- ✓ Robust error handling
- ✓ High test coverage
- ✓ Complete documentation
- ✓ Ready for public release

### Success Metrics

We'll know we've succeeded when:
- A non-technical user can install and run the tool
- Results clearly indicate which models work for which use cases
- HTML report is understandable without reading code
- Tool completes full test in 2-4 hours on target hardware
- No data loss even if interrupted
- Users can confidently choose optimal configurations based on results

---

## Current Status

**Phase**: Phase 0 - Foundation

**Completed**:
- ✓ README.md created
- ✓ DESIGN.md created
- ✓ DEVELOPMENT.md created
- ✓ ROADMAP.md created

**Next Steps**:
- Create project structure
- Set up development environment
- Create example configuration files
- Initialize git repository

**Estimated Completion**: Phase 0 - Current session

---

## Timeline Estimate

Assuming focused development sessions:

| Phase | Duration | Cumulative |
|-------|----------|------------|
| Phase 0: Foundation | 1 session | 1 session |
| Phase 1: Core Infrastructure | 2-3 sessions | 3-4 sessions |
| Phase 2: Basic Testing | 2 sessions | 5-6 sessions |
| Phase 3: Full Test Suite | 3-4 sessions | 8-10 sessions |
| Phase 4: Smart Testing | 2-3 sessions | 10-13 sessions |
| Phase 5: Reporting | 2-3 sessions | 12-16 sessions |
| Phase 6: Polish | 2-3 sessions | 14-19 sessions |

**Total Estimated Time**: 14-19 focused development sessions

**MVP Available**: After ~6 sessions
**Feature Complete**: After ~16 sessions
**Production Ready**: After ~19 sessions

---

## Notes

- Timeline is flexible and can be adjusted based on complexity encountered
- Each phase should end with working, tested code
- Documentation stays current throughout development
- Testing is not optional - write tests as we build
- User feedback can influence priorities within phases
- We can release after Phase 5 and do Phase 6 based on user feedback

---

**Let's build something great!** 🚀
