import os
import subprocess

def analyze_repo(clone_path, model_name="llama3"):
    try:
        print(f"\n🛠️ Starting analysis using: {model_name}")

        # Construct absolute paths
        base_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
        readme_path = os.path.join(base_path, "data/cloned_repo/README.md")
        requirements_path = os.path.join(base_path, "data/cloned_repo/requirements.txt")
        pyproject_path = os.path.join(base_path, "data/cloned_repo/pyproject.toml")

        # Read files if they exist
        def safe_read(file_path, label):
            if os.path.exists(file_path):
                with open(file_path, "r", encoding="utf-8") as f:
                    return f.read()
            else:
                print(f"⚠️ {label} not found!")
                return ""

        readme = safe_read(readme_path, "README.md")
        requirements = safe_read(requirements_path, "requirements.txt")
        pyproject = safe_read(pyproject_path, "pyproject.toml")

        # Create prompt
        prompt = f"""
You are an AI DevOps assistant.

Analyze this project and answer:

1. What does this project do?
2. What tech stack is used?
3. Which frameworks, APIs, or databases are involved?
4. What Docker base image should be used?
5. What is the likely run/start command?

README:
{readme[:1500]}

requirements.txt:
{requirements[:1000]}

pyproject.toml:
{pyproject[:1000]}
"""

        print("📤 Prompt ready. Launching Ollama with model:", model_name)

        result = subprocess.run(
            ["ollama", "run", model_name],
            input=prompt.encode("utf-8"),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=120,
        )

        output = result.stdout.decode("utf-8").strip()
        stderr_output = result.stderr.decode("utf-8").strip()

        print("\n✅ LLM Output:\n", output if output else "[Empty Output]")
        if stderr_output:
            print("\n🚨 LLM Errors:\n", stderr_output)

        return output if output else "❌ LLM returned an empty response."

    except subprocess.TimeoutExpired:
        print("⏱️ LLM Timeout: Took too long to respond.")
        return "❌ LLaMA took too long to respond."

    except FileNotFoundError as fe:
        print("❌ Ollama not found or model missing:", fe)
        return f"❌ Ollama not found or not installed. Details: {fe}"

    except Exception as e:
        print("❌ Exception in analyze_repo():", e)
        return f"❌ Error analyzing the repository: {str(e)}"
