# backend/config_generator.py

import os
import json
from rich import print

CONFIG_PATH = "data/cloned_repo/config.json"

def generate_config(port=8000, env_vars=None, run_command="python app.py"):
    print("[blue]⚙️ Creating config.json...[/blue]")

    config_data = {
        "port": port,
        "env": env_vars if env_vars else {},
        "command": run_command
    }

    try:
        with open(CONFIG_PATH, "w", encoding="utf-8") as f:
            json.dump(config_data, f, indent=4)
        print(f"[green]✅ config.json created at {CONFIG_PATH}[/green]")
        return True
    except Exception as e:
        print(f"[red]❌ Failed to create config:[/red] {e}")
        return False
