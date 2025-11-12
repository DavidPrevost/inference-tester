# Troubleshooting Guide

This guide helps you resolve common issues with the LLM Inference Tester.

## Table of Contents

1. [Installation Issues](#installation-issues)
2. [Configuration Problems](#configuration-problems)
3. [Model Download Issues](#model-download-issues)
4. [Server Start Failures](#server-start-failures)
5. [Test Failures](#test-failures)
6. [Performance Issues](#performance-issues)
7. [Common Error Messages](#common-error-messages)
8. [Getting Help](#getting-help)

---

## Installation Issues

### Missing Dependencies

**Problem**: `ModuleNotFoundError` when running the tool.

**Solution**:
```bash
# Install all required dependencies
pip install -r requirements.txt

# If using development features
pip install -r requirements-dev.txt
```

### Python Version Issues

**Problem**: Syntax errors or compatibility issues.

**Solution**:
- Ensure you're using Python 3.8 or later:
```bash
python --version
```
- If you have multiple Python versions, use:
```bash
python3.8 -m pip install -r requirements.txt
python3.8 src/main.py
```

### Permission Errors

**Problem**: Cannot write to directories or execute llama-server.

**Solution**:
```bash
# Make llama-server executable
chmod +x ./llama-server

# Ensure write permissions for results directory
chmod -R u+w results/
```

---

## Configuration Problems

### Configuration File Not Found

**Problem**: `FileNotFoundError: config.yaml not found`

**Solution**:
```bash
# Copy example configuration
cp config.example.yaml config.yaml
cp models.example.yaml models.yaml

# Edit to match your setup
nano config.yaml  # or your preferred editor
```

### Invalid YAML Syntax

**Problem**: `YAMLError` when loading configuration.

**Solution**:
- Check YAML syntax with online validator
- Common issues:
  - Tabs instead of spaces (use spaces only)
  - Missing colons after keys
  - Incorrect indentation
  - Unquoted special characters

**Example of correct YAML**:
```yaml
test_mode: full  # Use spaces, not tabs
llama_cpp:
  server_path: "./llama-server"
  default_ctx_size: 8192
```

### Model Directory Not Found

**Problem**: Cannot find models directory.

**Solution**:
```bash
# Create models directory
mkdir -p models/

# Or specify custom location in config.yaml
# model_dir: "/path/to/your/models"
```

---

## Model Download Issues

### HuggingFace Authentication

**Problem**: Cannot download models from HuggingFace.

**Solution**:
```bash
# Login to HuggingFace (if required)
huggingface-cli login

# Or set token in environment
export HF_TOKEN="your_token_here"
```

### Network Timeouts

**Problem**: Download times out or fails partway.

**Solution**:
- Check your internet connection
- Try again - the tool should resume partial downloads
- For large models, consider:
  - Downloading manually and placing in `models/` directory
  - Using a download manager for better resumption
  - Increasing timeout in config if on slow connection

### Corrupted Downloads

**Problem**: Model file downloaded but server won't load it.

**Solution**:
```bash
# Delete corrupted file
rm models/path/to/corrupted-model.gguf

# Re-download
python src/main.py --models "YourModel"
```

### Disk Space

**Problem**: No space left on device.

**Solution**:
- Check available space: `df -h`
- Models can be large (1-20GB each)
- Clean up old test results: `rm -rf results/*`
- Consider using external storage for models
- Update `model_dir` in config.yaml to point to larger drive

---

## Server Start Failures

### llama-server Not Found

**Problem**: `FileNotFoundError: llama-server not found`

**Solution**:
1. Download llama.cpp from: https://github.com/ggerganov/llama.cpp/releases
2. Extract and note the path to `llama-server` (or `server` in older versions)
3. Update config.yaml:
```yaml
llama_cpp:
  server_path: "/full/path/to/llama-server"
```

### Port Already in Use

**Problem**: `Address already in use` error.

**Solution**:
```bash
# Find process using port 8080 (default)
lsof -i :8080

# Kill process if needed
kill <PID>

# Or let the tool find an available port automatically (it should do this)
```

### Server Crashes Immediately

**Problem**: Server starts but crashes before tests begin.

**Solution**:
1. Check server logs in console output
2. Common causes:
   - Insufficient RAM for model
   - Corrupted model file
   - Incompatible llama-server version
3. Try:
   - Smaller model or higher quantization
   - Update llama-server to latest version
   - Run llama-server manually to see detailed errors

### Context Size Too Large

**Problem**: Server fails to start with "context size exceeds maximum".

**Solution**:
- Reduce `default_ctx_size` in config.yaml
- For long context tests, ensure model supports requested context
- Some models have limits (e.g., 4k, 8k, 16k, 32k)

---

## Test Failures

### All Tests Skipped

**Problem**: Every test shows "skipped" status.

**Solution**:
- This usually means insufficient RAM for configured models
- Try:
  - Smaller models (1B-3B instead of 7B+)
  - Higher quantization (Q4_K_M, Q5_K_M instead of Q6_K, Q8_0)
  - Close other applications to free RAM
  - Check available RAM: `free -h`

### Tests Timeout

**Problem**: Tests hang or timeout.

**Solution**:
1. Check system resources:
   ```bash
   top  # Monitor CPU and memory
   ```
2. Possible causes:
   - System swapping to disk (very slow)
   - CPU thermal throttling
   - Model too large for hardware
3. Solutions:
   - Ensure sufficient RAM (models/4 ≈ RAM needed)
   - Improve cooling if CPU throttling
   - Use smaller models

### Quality Tests Fail

**Problem**: Quality profile shows low accuracy.

**Solution**:
- This is expected with high quantization (Q2_K, Q3_K_M)
- Q4_K_M and above should maintain good quality
- Check which categories fail:
  - Math failures: Avoid for financial work
  - Comprehension failures: May work for creative writing
  - Format failures: Not suitable for structured output
- Consider less aggressive quantization

### Stress Tests Abort

**Problem**: Stress test aborts with temperature warning.

**Solution**:
- **This is a safety feature!**
- Your system is overheating
- Solutions:
  - Improve cooling (clean fans, add cooling pad)
  - Reduce ambient temperature
  - Test with smaller/more efficient model
  - Reduce stress test duration in config
  - Ensure adequate airflow around device

---

## Performance Issues

### Very Slow Tokens Per Second (<2 t/s)

**Problem**: Generation is extremely slow.

**Causes & Solutions**:
1. **Swapping**: System using disk instead of RAM
   - Solution: Use smaller model or higher quantization
   - Check: `free -h` and look for swap usage

2. **Thermal Throttling**: CPU reducing speed due to heat
   - Solution: Improve cooling, reduce ambient temperature
   - Check: Monitor temperatures during test

3. **Model Too Large**: Model exceeds efficient processing capability
   - Solution: Try Q4_K_M or Q5_K_M of smaller model
   - Example: Try 3B model instead of 7B

4. **Background Processes**: Other apps using resources
   - Solution: Close unnecessary applications
   - Check: `top` or Task Manager

### High TTFT (Time to First Token)

**Problem**: Long delay before generation starts (>30s).

**Solutions**:
- Expected for large contexts or large models on limited hardware
- To reduce:
  - Use smaller context sizes
  - Choose more efficient model
  - Ensure no swapping occurring
  - Close background applications

### Test Takes Too Long

**Problem**: Tests running for many hours.

**Solutions**:
1. Use `--quick` mode for faster testing:
   ```bash
   python src/main.py --quick
   ```

2. Test fewer models:
   ```bash
   python src/main.py --models "Phi-3.5-mini"
   ```

3. Test fewer profiles:
   ```bash
   python src/main.py --profiles interactive,batch
   ```

4. Skip lengthy tests:
   ```bash
   python src/main.py --skip-stress
   ```

---

## Common Error Messages

### "Insufficient memory: need X.XGB, available Y.YGB"

**Meaning**: Not enough RAM for this model/quantization.

**Solution**:
- Use higher quantization (Q4_K_M instead of Q6_K)
- Test smaller model
- Close other applications
- This is smart skipping working correctly!

### "Failed to start server"

**Meaning**: llama-server couldn't start.

**Debug steps**:
1. Check server_path in config.yaml is correct
2. Verify llama-server is executable: `chmod +x llama-server`
3. Try running server manually to see detailed error
4. Check server version compatibility

### "Model failed earlier"

**Meaning**: Previous test with this model/quant failed, skipping future tests.

**Solution**:
- This is smart skipping working correctly!
- Model is too large or slow for your hardware
- Try higher quantization or smaller model

### "Temperature critical: XX°C - aborting stress test"

**Meaning**: System reached unsafe temperature during stress test.

**Solution**:
- **This is a safety feature!**
- Improve cooling before continuing
- Don't override - risk of hardware damage
- Consider this model configuration too demanding for your hardware

---

## Getting Help

### Check Logs

Detailed logs are saved to `inference-tester.log`:
```bash
# View recent log entries
tail -n 50 inference-tester.log

# Search for errors
grep ERROR inference-tester.log
```

### Gather Information

When asking for help, provide:
1. Operating system and version
2. Python version (`python --version`)
3. Available RAM (`free -h` on Linux, Task Manager on Windows)
4. llama.cpp version
5. Config files (config.yaml, models.yaml)
6. Error message or log excerpt
7. Command you ran

### Common Solutions Checklist

Before asking for help, try:
- [ ] Config files copied from examples
- [ ] llama-server path correct in config
- [ ] llama-server executable (`chmod +x`)
- [ ] Sufficient disk space
- [ ] Sufficient RAM for chosen models
- [ ] All dependencies installed
- [ ] Python 3.8+
- [ ] Latest version of tool

### Report Issues

If you've found a bug:
1. Check existing issues: https://github.com/your-repo/issues
2. Include:
   - Steps to reproduce
   - Expected vs actual behavior
   - System information
   - Relevant logs
   - Config files (remove sensitive info)

---

## Tips for Best Results

### Hardware Recommendations

**Minimum**:
- CPU: 4+ cores
- RAM: 8GB (for 1-3B models with Q4)
- Storage: 50GB free

**Recommended**:
- CPU: 6-8 cores
- RAM: 16GB (for 7B models with Q4-Q5)
- Storage: 100GB+ free
- Good cooling

**Optimal**:
- CPU: 8+ cores, modern architecture
- RAM: 32GB (for 13B models or lower quants)
- SSD: 200GB+ free
- Quality cooling solution

### Model Selection Tips

**First-time testing**:
- Start with Phi-3.5-mini or Qwen2.5-1.5B
- Use Q4_K_M quantization
- Run with `--quick` flag

**For Production use**:
- Test 2-3 models in the size range you need
- Compare Q4_K_M, Q5_K_M, Q6_K
- Run quality profile to ensure accuracy
- Check specific use case profiles

**Memory Rule of Thumb**:
- Model RAM ≈ Model size (GB) × 1.2
- Q4_K_M: ~1.2x model parameters
- Q6_K: ~1.3x model parameters
- Q8_0: ~1.4x model parameters

### Interpreting Results

**Status meanings**:
- **Excellent**: Outstanding performance, use with confidence
- **Good**: Solid performance, suitable for most tasks
- **Acceptable**: Meets minimum requirements, usable
- **Poor**: Below threshold but functional, consider alternatives
- **Failed**: Does not meet requirements, choose different config
- **Skipped**: Smart termination prevented testing (saves time!)

**Focus on**:
- Recommendations in HTML report
- Use-case specific sections
- Memory usage patterns
- Temperature during stress test

---

## Quick Reference

### Essential Commands

```bash
# First run
cp config.example.yaml config.yaml
cp models.example.yaml models.yaml
python src/main.py --quick

# Full test
python src/main.py --full

# Specific model
python src/main.py --models "Llama-3.2-7B"

# Resume interrupted
python src/main.py --resume results/checkpoint.json

# Get help
python src/main.py --help
```

### Essential Config Settings

```yaml
# Most important settings in config.yaml:
model_dir: "models/"                      # Where models are stored
test_mode: "quick"                        # or "full"
llama_cpp:
  server_path: "./llama-server"          # Path to llama-server
  default_ctx_size: 8192                 # Context window size
resource_limits:
  max_memory_gb: 14                      # Max RAM to use (leave 2GB for system)
```

---

**Still having issues?** Check the logs in `inference-tester.log` and GitHub issues for more help!
