# SQL Test Generation Scripts

This directory contains powerful scripts for generating PostgreSQL test cases using Fireworks AI.

## Scripts Overview

### `generate_sql_tests_parallel.py`
High-performance parallel SQL test case generator optimized for speed with:
- **Async/await concurrency** - Multiple API calls in parallel
- **Intelligent batching** - Generate multiple examples per prompt
- **Rate limiting** - Respects API limits with semaphores
- **Retry logic** - Handles failures gracefully
- **Progress tracking** - Rich progress bars and statistics

### `benchmark_generator.py`
Finds optimal batch and concurrency settings for your API limits and performance needs.

## Quick Start

1. **Set up Fireworks API key:**
   ```bash
   export FIREWORKS_API_KEY="your_api_key_here"
   # Or use the justfile command:
   just setup-fireworks your_api_key_here
   ```

2. **Generate test cases:**
   ```bash
   # Fast parallel generation (recommended)
   just generate-tests-fast 100
   
   # Or run directly
   python scripts/generate_sql_tests_parallel.py --count 100 --config balanced
   ```

3. **Find optimal settings:**
   ```bash
   just benchmark-generation
   ```

## Configuration Presets

### Performance (Best Quality)
- **Generator:** deepseek-v3-0324 (latest DeepSeek reasoning model)
- **Critic:** deepseek-r1-0528 (specialized reasoning critic)
- **Use case:** Highest quality test generation, advanced reasoning

### Balanced (Recommended)
- **Generator:** qwen2p5-vl-32b-instruct (strong code understanding)
- **Critic:** llama-v3p1-8b-instruct (fast validation)
- **Use case:** Good balance of speed, quality, and cost

### Cost Effective
- **Generator:** llama-v3p1-8b-instruct
- **Critic:** llama-v3p1-8b-instruct
- **Use case:** Budget-conscious, still good quality

### Experimental
- **Generator:** qwen3-30b-a3b (cutting-edge Qwen model)
- **Critic:** qwen2p5-vl-32b-instruct (advanced validation)
- **Use case:** Testing newest model capabilities

## Advanced Usage

### Custom Configuration
```bash
python scripts/generate_sql_tests_parallel.py \
    --count 200 \
    --config performance \
    --batch-size 10 \
    --max-concurrent 15
```

### Complexity Distribution
By default, generates:
- 20% Simple (basic tables, indexes)
- 30% Medium (types, functions, triggers)
- 30% Complex (RLS, grants, CTEs)
- 20% Extreme (circular deps, dynamic SQL)

## Output Structure

Generated files are saved to:
```
examples/generated/
├── simple/
│   ├── simple_1.sql
│   ├── simple_1_critique.json
│   └── ...
├── medium/
├── complex/
├── extreme/
└── summary.json
```

Each SQL file includes:
- Complexity rating
- Validity assessment
- Idempotency status
- Featured PostgreSQL capabilities

## Performance Tips

1. **Start with benchmarking** to find your optimal settings
2. **Use balanced config** for most use cases
3. **Increase batch size** if you have high API limits
4. **Monitor rate limits** - the scripts handle retries but respect limits
5. **Run during off-peak hours** for better API performance

## Troubleshooting

### Rate Limiting
If you hit rate limits, the scripts will:
- Automatically retry with exponential backoff
- Show rate limit warnings in the console
- Continue processing other batches

### API Errors
- Check your FIREWORKS_API_KEY is set correctly
- Verify your account has sufficient credits
- Try reducing --max-concurrent if getting timeouts

### Memory Usage
For very large batches (1000+ examples):
- Use multiple smaller runs instead
- Monitor memory usage during critique phase
- Consider reducing critique batch size in the code

## Integration

These scripts integrate with the main project workflow:
- Generated SQL files work with `just transform`
- Use generated test cases for comprehensive testing
- Critique data helps validate transformation quality