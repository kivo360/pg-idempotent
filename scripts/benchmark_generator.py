"""
Benchmark script to find optimal batch and concurrency settings
"""

import asyncio
import time
import os
from rich.console import Console
from rich.table import Table
from typing import List, Tuple

console = Console()

async def benchmark_settings(
    total_examples: int = 20,
    batch_sizes: List[int] = [1, 3, 5, 10],
    concurrency_levels: List[int] = [5, 10, 15, 20]
) -> None:
    """Run benchmarks to find optimal settings"""
    
    from generate_sql_tests_parallel import (
        ParallelSQLGenerator, 
        RECOMMENDED_CONFIGS, 
        BatchConfig,
        AsyncFireworksClient,
        SQLComplexity
    )
    
    # Use cost-effective model for benchmarking
    config = RECOMMENDED_CONFIGS["cost_effective"]
    
    results = []
    
    console.print("[bold cyan]Running benchmark tests...[/bold cyan]\n")
    
    for batch_size in batch_sizes:
        for max_concurrent in concurrency_levels:
            console.print(f"Testing batch_size={batch_size}, max_concurrent={max_concurrent}")
            
            batch_config = BatchConfig(
                batch_size=batch_size,
                max_concurrent_requests=max_concurrent
            )
            
            generator = ParallelSQLGenerator(config, batch_config)
            
            # Time the generation
            start_time = time.time()
            
            try:
                async with AsyncFireworksClient(os.getenv("FIREWORKS_API_KEY"), batch_config) as client:
                    # Generate a small batch
                    test_results = await generator.generate_complexity_batch(
                        client,
                        SQLComplexity.MEDIUM,
                        total_examples
                    )
                
                elapsed = time.time() - start_time
                success_rate = len([r for r in test_results if r.get("is_generated", False)]) / total_examples
                examples_per_second = len(test_results) / elapsed
                
                results.append({
                    "batch_size": batch_size,
                    "max_concurrent": max_concurrent,
                    "elapsed": elapsed,
                    "success_rate": success_rate,
                    "examples_per_second": examples_per_second,
                    "total_generated": len(test_results)
                })
                
                console.print(f"  ✓ Completed in {elapsed:.2f}s ({examples_per_second:.2f} examples/sec)")
                
            except Exception as e:
                console.print(f"  ✗ Error: {e}")
                results.append({
                    "batch_size": batch_size,
                    "max_concurrent": max_concurrent,
                    "elapsed": -1,
                    "success_rate": 0,
                    "examples_per_second": 0,
                    "total_generated": 0
                })
            
            # Small delay between tests
            await asyncio.sleep(2)
    
    # Display results
    console.print("\n[bold green]Benchmark Results[/bold green]\n")
    
    table = Table(title="Performance by Configuration")
    table.add_column("Batch Size", style="cyan")
    table.add_column("Max Concurrent", style="cyan")
    table.add_column("Time (s)", style="yellow")
    table.add_column("Success Rate", style="green")
    table.add_column("Examples/sec", style="magenta")
    
    # Sort by examples per second
    results.sort(key=lambda x: x["examples_per_second"], reverse=True)
    
    for r in results:
        if r["elapsed"] > 0:
            table.add_row(
                str(r["batch_size"]),
                str(r["max_concurrent"]),
                f"{r['elapsed']:.2f}",
                f"{r['success_rate']:.0%}",
                f"{r['examples_per_second']:.2f}"
            )
    
    console.print(table)
    
    # Find optimal settings
    if results:
        best = results[0]
        console.print(f"\n[bold green]Optimal Settings:[/bold green]")
        console.print(f"  Batch Size: {best['batch_size']}")
        console.print(f"  Max Concurrent: {best['max_concurrent']}")
        console.print(f"  Performance: {best['examples_per_second']:.2f} examples/second")

if __name__ == "__main__":
    asyncio.run(benchmark_settings())