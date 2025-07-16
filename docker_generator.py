# backend/docker_generator.py

import os
from rich import print

DOCKERFILE_PATH = "data/cloned_repo/Dockerfile"

def generate_dockerfile(language="python", base_image="python:3.12", run_command="python app.py"):
    print("[blue]⚙️ Generating Dockerfile...[/blue]")

    dockerfile_content = f"""
# Auto-generated Dockerfile by Auto-Dock It
FROM {base_image}

WORKDIR /app
COPY . .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Run the application
CMD ["{run_command.split()[0]}", "{run_command.split()[1]}"]
"""

    try:
        with open(DOCKERFILE_PATH, "w", encoding="utf-8") as file:
            file.write(dockerfile_content.strip())
        print(f"[green]✅ Dockerfile generated at {DOCKERFILE_PATH}[/green]")
        return True
    except Exception as e:
        print(f"[red]❌ Failed to generate Dockerfile:[/red] {e}")
        return False
