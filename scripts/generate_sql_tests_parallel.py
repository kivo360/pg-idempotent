"""
Parallel PostgreSQL Test Case Generator using Fireworks AI
Optimized for speed with batching, parallelization, and async processing
"""

import os
import json
import asyncio
import aiohttp
import time
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass, field
from enum import Enum
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
import multiprocessing as mp
from functools import partial
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, BarColumn, TextColumn, TimeRemainingColumn
from rich.table import Table
import fireworks.client

console = Console()

# Initialize Fireworks client
FIREWORKS_API_KEY = os.getenv("FIREWORKS_API_KEY")
FIREWORKS_API_BASE = "https://api.fireworks.ai/inference/v1"

class SQLComplexity(Enum):
    SIMPLE = "simple"
    MEDIUM = "medium"
    COMPLEX = "complex"
    EXTREME = "extreme"

@dataclass
class ModelConfig:
    """Configuration for Fireworks AI models"""
    generator_model: str
    critic_model: str
    temperature: float = 0.7
    max_tokens: int = 4000
    
@dataclass
class BatchConfig:
    """Configuration for batch processing"""
    batch_size: int = 5  # Number of prompts per batch
    max_concurrent_requests: int = 10  # Max parallel API calls
    retry_attempts: int = 3
    retry_delay: float = 1.0
    timeout: float = 30.0

# Model configurations
RECOMMENDED_CONFIGS = {
    "performance": ModelConfig(
        generator_model="accounts/fireworks/models/deepseek-v3-0324",
        critic_model="accounts/fireworks/models/deepseek-r1-0528",
        temperature=0.8
    ),
    "balanced": ModelConfig(
        generator_model="accounts/fireworks/models/qwen2p5-vl-32b-instruct",
        critic_model="accounts/fireworks/models/llama-v3p1-8b-instruct",
        temperature=0.7
    ),
    "cost_effective": ModelConfig(
        generator_model="accounts/fireworks/models/llama-v3p1-8b-instruct",
        critic_model="accounts/fireworks/models/llama-v3p1-8b-instruct",
        temperature=0.7
    ),
    "experimental": ModelConfig(
        generator_model="accounts/fireworks/models/qwen3-30b-a3b",
        critic_model="accounts/fireworks/models/qwen2p5-vl-32b-instruct",
        temperature=0.7
    )
}

class AsyncFireworksClient:
    """Async client for Fireworks API with batching support"""
    
    def __init__(self, api_key: str, batch_config: BatchConfig):
        self.api_key = api_key
        self.batch_config = batch_config
        self.session: Optional[aiohttp.ClientSession] = None
        self.semaphore = asyncio.Semaphore(batch_config.max_concurrent_requests)
        
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
            
    async def _make_request(self, messages: List[Dict], model: str, **kwargs) -> Dict:
        """Make a single API request with retry logic"""
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": model,
            "messages": messages,
            **kwargs
        }
        
        for attempt in range(self.batch_config.retry_attempts):
            try:
                async with self.semaphore:  # Rate limiting
                    async with self.session.post(
                        f"{FIREWORKS_API_BASE}/chat/completions",
                        json=payload,
                        headers=headers,
                        timeout=aiohttp.ClientTimeout(total=self.batch_config.timeout)
                    ) as response:
                        if response.status == 200:
                            return await response.json()
                        elif response.status == 429:  # Rate limit
                            await asyncio.sleep(self.batch_config.retry_delay * (attempt + 1))
                            continue
                        else:
                            error_text = await response.text()
                            console.print(f"[red]API Error {response.status}: {error_text}[/red]")
                            
            except asyncio.TimeoutError:
                console.print(f"[yellow]Timeout on attempt {attempt + 1}[/yellow]")
                await asyncio.sleep(self.batch_config.retry_delay)
            except Exception as e:
                console.print(f"[red]Request error: {e}[/red]")
                await asyncio.sleep(self.batch_config.retry_delay)
                
        return None
    
    async def batch_generate(self, prompts: List[str], model: str, **kwargs) -> List[str]:
        """Generate multiple responses in parallel"""
        tasks = []
        for prompt in prompts:
            messages = [{"role": "user", "content": prompt}]
            task = self._make_request(messages, model, **kwargs)
            tasks.append(task)
            
        responses = await asyncio.gather(*tasks, return_exceptions=True)
        
        results = []
        for i, response in enumerate(responses):
            if isinstance(response, Exception):
                console.print(f"[red]Error in batch item {i}: {response}[/red]")
                results.append(None)
            elif response and "choices" in response:
                results.append(response["choices"][0]["message"]["content"])
            else:
                results.append(None)
                
        return results

class ParallelSQLGenerator:
    """Parallel SQL test case generator"""
    
    def __init__(self, config: ModelConfig, batch_config: BatchConfig = BatchConfig()):
        self.config = config
        self.batch_config = batch_config
        self.generated_examples = []
        
    def generate_batch_prompt(self, complexity: SQLComplexity, count: int = 5) -> str:
        """Generate a prompt that creates multiple SQL examples at once"""
        
        complexity_specs = {
            SQLComplexity.SIMPLE: "basic CREATE TABLE, INDEX, and simple constraints",
            SQLComplexity.MEDIUM: "custom types, functions with dollar quotes, triggers, basic RLS",
            SQLComplexity.COMPLEX: "nested dollar quotes, DO blocks, complex RLS, GRANT/REVOKE, recursive CTEs",
            SQLComplexity.EXTREME: "deeply nested structures, circular dependencies, dynamic SQL, polymorphic functions"
        }
        
        prompt = f"""Generate {count} DIFFERENT PostgreSQL migration examples with {complexity.value} complexity.

Each example should:
1. Be NON-IDEMPOTENT (fail if run twice)
2. Test different PostgreSQL features
3. Be separated by: -- EXAMPLE_SEPARATOR --

Complexity: {complexity_specs[complexity]}

Generate {count} complete, runnable SQL migration examples:"""
        
        return prompt
    
    def split_batch_response(self, response: str) -> List[str]:
        """Split batch response into individual SQL examples"""
        if not response:
            return []
            
        # Split by separator
        examples = response.split("-- EXAMPLE_SEPARATOR --")
        
        # Clean up each example
        cleaned = []
        for example in examples:
            example = example.strip()
            if example and len(example) > 50:  # Minimum viable SQL
                cleaned.append(example)
                
        return cleaned
    
    async def generate_complexity_batch(
        self, 
        client: AsyncFireworksClient,
        complexity: SQLComplexity, 
        total_count: int,
        progress_callback=None
    ) -> List[Dict]:
        """Generate all examples for a specific complexity level"""
        
        results = []
        batch_size = self.batch_config.batch_size
        
        # Calculate how many batches we need
        num_batches = (total_count + batch_size - 1) // batch_size
        
        # Generate prompts for all batches
        prompts = []
        for i in range(num_batches):
            count = min(batch_size, total_count - i * batch_size)
            prompt = self.generate_batch_prompt(complexity, count)
            prompts.append((prompt, count))
        
        # Process in chunks to avoid overwhelming the API
        chunk_size = self.batch_config.max_concurrent_requests
        
        for chunk_start in range(0, len(prompts), chunk_size):
            chunk_end = min(chunk_start + chunk_size, len(prompts))
            chunk_prompts = prompts[chunk_start:chunk_end]
            
            # Generate SQL in parallel
            batch_prompts = [p[0] for p in chunk_prompts]
            responses = await client.batch_generate(
                batch_prompts,
                self.config.generator_model,
                temperature=self.config.temperature,
                max_tokens=self.config.max_tokens
            )
            
            # Process responses
            for (prompt, expected_count), response in zip(chunk_prompts, responses):
                if response:
                    examples = self.split_batch_response(response)
                    
                    for j, sql in enumerate(examples[:expected_count]):
                        result = {
                            "id": f"{complexity.value}_{len(results) + 1}",
                            "complexity": complexity.value,
                            "sql": sql,
                            "is_generated": True
                        }
                        results.append(result)
                        
                        if progress_callback:
                            progress_callback(1)
                            
        return results
    
    def critique_batch(self, sql_examples: List[str]) -> List[Dict]:
        """Critique multiple SQL examples using synchronous API"""
        
        # Create a batch critique prompt
        batch_prompt = "Analyze these PostgreSQL migration scripts. For each, provide a JSON analysis.\n\n"
        
        for i, sql in enumerate(sql_examples):
            batch_prompt += f"=== EXAMPLE {i+1} ===\n```sql\n{sql}\n```\n\n"
            
        batch_prompt += """
For each example, evaluate:
1. is_valid: Will it execute without errors?
2. is_non_idempotent: Will it fail if run twice?
3. complexity_score: Rate 1-10
4. main_features: List key PostgreSQL features used

Respond with a JSON array where each element corresponds to an example:
[{"is_valid": true, "is_non_idempotent": true, "complexity_score": 7, "main_features": ["triggers", "RLS"]}, ...]
"""
        
        try:
            response = fireworks.client.ChatCompletion.create(
                model=self.config.critic_model,
                messages=[{"role": "user", "content": batch_prompt}],
                temperature=0.3,
                max_tokens=2000
            )
            
            content = response.choices[0].message.content
            
            # Extract JSON array
            import re
            json_match = re.search(r'\[.*\]', content, re.DOTALL)
            if json_match:
                critiques = json.loads(json_match.group())
                return critiques
            else:
                return [{"error": "Could not parse critique"} for _ in sql_examples]
                
        except Exception as e:
            console.print(f"[red]Critique error: {e}[/red]")
            return [{"error": str(e)} for _ in sql_examples]
    
    async def generate_test_suite_parallel(self, num_examples: int = 100) -> List[Dict]:
        """Generate test suite using parallel processing"""
        
        start_time = time.time()
        
        # Distribution of complexity
        distribution = {
            SQLComplexity.SIMPLE: int(num_examples * 0.2),
            SQLComplexity.MEDIUM: int(num_examples * 0.3),
            SQLComplexity.COMPLEX: int(num_examples * 0.3),
            SQLComplexity.EXTREME: int(num_examples * 0.2),
        }
        
        all_results = []
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            TimeRemainingColumn(),
            console=console
        ) as progress:
            
            total_task = progress.add_task("[cyan]Generating SQL examples...", total=num_examples)
            
            async with AsyncFireworksClient(FIREWORKS_API_KEY, self.batch_config) as client:
                
                # Generate for each complexity level in parallel
                tasks = []
                for complexity, count in distribution.items():
                    task = self.generate_complexity_batch(
                        client, 
                        complexity, 
                        count,
                        lambda n: progress.update(total_task, advance=n)
                    )
                    tasks.append(task)
                
                # Wait for all generation to complete
                complexity_results = await asyncio.gather(*tasks)
                
                # Flatten results
                for results in complexity_results:
                    all_results.extend(results)
            
            # Now critique in batches using thread pool
            critique_task = progress.add_task("[yellow]Critiquing examples...", total=len(all_results))
            
            # Process critiques in parallel batches
            critique_batch_size = 10
            with ThreadPoolExecutor(max_workers=5) as executor:
                
                futures = []
                for i in range(0, len(all_results), critique_batch_size):
                    batch = all_results[i:i + critique_batch_size]
                    sql_batch = [r["sql"] for r in batch]
                    
                    future = executor.submit(self.critique_batch, sql_batch)
                    futures.append((i, future))
                
                # Collect critique results
                for batch_start, future in futures:
                    critiques = future.result()
                    
                    for j, critique in enumerate(critiques):
                        if batch_start + j < len(all_results):
                            all_results[batch_start + j]["critique"] = critique
                            progress.update(critique_task, advance=1)
        
        elapsed = time.time() - start_time
        
        # Summary statistics
        valid_count = sum(1 for r in all_results if r.get("critique", {}).get("is_valid", False))
        non_idempotent = sum(1 for r in all_results if r.get("critique", {}).get("is_non_idempotent", False))
        
        # Display summary
        table = Table(title="Generation Summary")
        table.add_column("Metric", style="cyan")
        table.add_column("Value", style="green")
        
        table.add_row("Total Generated", str(len(all_results)))
        table.add_row("Valid SQL", f"{valid_count} ({valid_count/len(all_results)*100:.1f}%)")
        table.add_row("Non-Idempotent", f"{non_idempotent} ({non_idempotent/len(all_results)*100:.1f}%)")
        table.add_row("Generation Time", f"{elapsed:.2f} seconds")
        table.add_row("Examples per Second", f"{len(all_results) / elapsed:.2f}")
        
        console.print(table)
        
        return all_results
    
    def save_results(self, results: List[Dict]):
        """Save all results to disk"""
        
        for result in results:
            complexity = result["complexity"]
            id = result["id"]
            
            # Create directory
            dir_path = f"examples/generated/{complexity}"
            os.makedirs(dir_path, exist_ok=True)
            
            # Save SQL
            sql_path = f"{dir_path}/{id}.sql"
            with open(sql_path, "w") as f:
                critique = result.get("critique", {})
                f.write(f"-- Generated Test Case: {id}\n")
                f.write(f"-- Complexity: {complexity}\n")
                f.write(f"-- Valid: {critique.get('is_valid', 'Unknown')}\n")
                f.write(f"-- Non-Idempotent: {critique.get('is_non_idempotent', 'Unknown')}\n")
                if "main_features" in critique:
                    f.write(f"-- Features: {', '.join(critique['main_features'])}\n")
                f.write("\n")
                f.write(result["sql"])
            
            # Save critique
            if "critique" in result:
                critique_path = f"{dir_path}/{id}_critique.json"
                with open(critique_path, "w") as f:
                    json.dump(result["critique"], f, indent=2)

async def main():
    """Main async function"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Generate PostgreSQL test cases in parallel")
    parser.add_argument("--config", choices=["performance", "balanced", "cost_effective", "experimental"], 
                       default="balanced", help="Model configuration preset")
    parser.add_argument("--count", type=int, default=100, 
                       help="Number of test cases to generate")
    parser.add_argument("--batch-size", type=int, default=5,
                       help="Number of examples per batch prompt")
    parser.add_argument("--max-concurrent", type=int, default=10,
                       help="Maximum concurrent API requests")
    
    args = parser.parse_args()
    
    # Check API key
    if not FIREWORKS_API_KEY:
        console.print("[red]Error: FIREWORKS_API_KEY environment variable not set[/red]")
        return
    
    # Configure
    model_config = RECOMMENDED_CONFIGS[args.config]
    batch_config = BatchConfig(
        batch_size=args.batch_size,
        max_concurrent_requests=args.max_concurrent
    )
    
    console.print(f"[green]Configuration:[/green]")
    console.print(f"  Model preset: {args.config}")
    console.print(f"  Generator: {model_config.generator_model}")
    console.print(f"  Critic: {model_config.critic_model}")
    console.print(f"  Batch size: {batch_config.batch_size}")
    console.print(f"  Max concurrent: {batch_config.max_concurrent_requests}")
    console.print("")
    
    # Generate
    generator = ParallelSQLGenerator(model_config, batch_config)
    results = await generator.generate_test_suite_parallel(args.count)
    
    # Save results
    console.print("\n[cyan]Saving results...[/cyan]")
    generator.save_results(results)
    
    # Save summary
    summary_path = "examples/generated/summary.json"
    with open(summary_path, "w") as f:
        summary = {
            "total": len(results),
            "config": args.config,
            "batch_size": batch_config.batch_size,
            "by_complexity": {},
            "features_used": {}
        }
        
        # Aggregate by complexity
        for result in results:
            comp = result["complexity"]
            summary["by_complexity"][comp] = summary["by_complexity"].get(comp, 0) + 1
            
            # Track features
            features = result.get("critique", {}).get("main_features", [])
            for feature in features:
                summary["features_used"][feature] = summary["features_used"].get(feature, 0) + 1
        
        json.dump(summary, f, indent=2)
    
    console.print(f"\n[green]✓ Results saved to examples/generated/[/green]")
    console.print(f"[green]✓ Summary saved to {summary_path}[/green]")

if __name__ == "__main__":
    asyncio.run(main())