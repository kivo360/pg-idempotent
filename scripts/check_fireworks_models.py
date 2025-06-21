"""
Check available Fireworks AI models and their capabilities
"""

import os
import requests
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

console = Console()

def get_all_models():
    """Get all available models from Fireworks AI API"""
    api_key = os.getenv("FIREWORKS_API_KEY")
    if not api_key:
        console.print("[red]Error: FIREWORKS_API_KEY environment variable not set[/red]")
        console.print("[yellow]Set it with: export FIREWORKS_API_KEY='your_api_key'[/yellow]")
        return []
    
    headers = {"Authorization": f"Bearer {api_key}"}
    
    try:
        console.print("[cyan]Fetching available models from Fireworks AI...[/cyan]\n")
        
        response = requests.get(
            "https://api.fireworks.ai/inference/v1/models",
            headers=headers,
            timeout=15
        )
        
        if response.status_code == 200:
            data = response.json()
            models = data.get("data", [])
            console.print(f"[green]✓ Found {len(models)} available models[/green]\n")
            return models
        else:
            console.print(f"[red]API Error {response.status_code}: {response.text}[/red]")
            return []
            
    except Exception as e:
        console.print(f"[red]Error fetching models: {e}[/red]")
        return []

def categorize_models(models):
    """Categorize models by type and capability"""
    categories = {
        "chat_instruct": [],
        "code_specialized": [],
        "large_context": [],
        "small_fast": [],
        "other": []
    }
    
    for model in models:
        model_id = model.get("id", "")
        
        # Code-specialized models
        if any(word in model_id.lower() for word in ["code", "coder", "starcoder"]):
            categories["code_specialized"].append(model)
        # Instruction-tuned chat models
        elif "instruct" in model_id.lower() or "chat" in model_id.lower():
            # Categorize by size
            if any(size in model_id for size in ["405b", "70b", "72b", "34b", "32b"]):
                categories["chat_instruct"].append(model)
            elif any(size in model_id for size in ["8b", "7b"]):
                categories["small_fast"].append(model)
            else:
                categories["chat_instruct"].append(model)
        else:
            categories["other"].append(model)
    
    return categories

def suggest_configurations(categories):
    """Suggest optimal configurations based on available models"""
    
    # All instruct models for selection
    all_instruct = categories["chat_instruct"] + categories["code_specialized"]
    
    # Sort by likely capability (rough heuristic based on size)
    def model_score(model):
        model_id = model.get("id", "")
        if "405b" in model_id: return 1000
        if "70b" in model_id or "72b" in model_id: return 700
        if "34b" in model_id or "32b" in model_id: return 340
        if "22b" in model_id: return 220
        if "15b" in model_id: return 150
        if "8b" in model_id: return 80
        if "7b" in model_id: return 70
        return 50
    
    all_instruct.sort(key=model_score, reverse=True)
    small_models = categories["small_fast"]
    small_models.sort(key=model_score, reverse=True)
    
    configs = {}
    
    # Performance config - largest models
    if len(all_instruct) >= 2:
        configs["performance"] = {
            "generator": all_instruct[0]["id"],
            "critic": all_instruct[1]["id"] if len(all_instruct) > 1 else all_instruct[0]["id"]
        }
    
    # Balanced config - mid-size for generator, small for critic
    if all_instruct and small_models:
        mid_models = [m for m in all_instruct if model_score(m) < 700 and model_score(m) > 200]
        if mid_models:
            configs["balanced"] = {
                "generator": mid_models[0]["id"],
                "critic": small_models[0]["id"]
            }
        else:
            configs["balanced"] = {
                "generator": all_instruct[0]["id"],
                "critic": small_models[0]["id"]
            }
    
    # Cost-effective config - small models
    if small_models:
        configs["cost_effective"] = {
            "generator": small_models[0]["id"],
            "critic": small_models[0]["id"]
        }
    
    return configs

def display_models(categories):
    """Display models in a nice table format"""
    
    for category, models in categories.items():
        if not models:
            continue
            
        category_names = {
            "chat_instruct": "💬 Chat & Instruction Models",
            "code_specialized": "🔧 Code-Specialized Models", 
            "small_fast": "⚡ Small & Fast Models",
            "large_context": "📚 Large Context Models",
            "other": "📦 Other Models"
        }
        
        console.print(f"\n[bold cyan]{category_names.get(category, category)}[/bold cyan]")
        
        table = Table()
        table.add_column("Model ID", style="green")
        table.add_column("Object", style="blue") 
        table.add_column("Created", style="yellow")
        
        for model in models:
            table.add_row(
                model.get("id", ""),
                model.get("object", ""),
                str(model.get("created", ""))
            )
        
        console.print(table)

def main():
    """Main function"""
    
    # Get all models
    models = get_all_models()
    if not models:
        return
    
    # Categorize them
    categories = categorize_models(models)
    
    # Display models
    display_models(categories)
    
    # Suggest configurations
    configs = suggest_configurations(categories)
    
    if configs:
        console.print(f"\n[bold green]🎯 Suggested Configurations[/bold green]")
        
        for config_name, config in configs.items():
            console.print(f"\n[bold]{config_name.title()}:[/bold]")
            console.print(f"  Generator: [green]{config['generator']}[/green]")
            console.print(f"  Critic: [blue]{config['critic']}[/blue]")
        
        # Show how to update the script
        console.print(f"\n[bold cyan]💡 To use these models:[/bold cyan]")
        console.print("Edit scripts/generate_sql_tests_parallel.py and update RECOMMENDED_CONFIGS:")
        console.print()
        
        for config_name, config in configs.items():
            console.print(f'    "{config_name}": ModelConfig(')
            console.print(f'        generator_model="{config["generator"]}",')
            console.print(f'        critic_model="{config["critic"]}",')
            console.print(f'        temperature=0.7')
            console.print(f'    ),')
    
    # Summary stats
    total_models = len(models)
    instruct_models = len(categories["chat_instruct"])
    code_models = len(categories["code_specialized"]) 
    
    console.print(f"\n[bold green]📊 Summary:[/bold green]")
    console.print(f"  Total models: {total_models}")
    console.print(f"  Chat/Instruct: {instruct_models}")
    console.print(f"  Code-specialized: {code_models}")
    console.print(f"  Small/Fast: {len(categories['small_fast'])}")

if __name__ == "__main__":
    main()