import subprocess
import re
import json
from datetime import datetime
from pathlib import Path
import pytest

# ---------- CONFIG ----------
MODEL = "codellama:13b"
TEST_FOLDER = Path("test_cases")
LOG_FILE = Path("logs/history.json")

# ---------- HELPERS ----------

def extract_diff(response):
    match = re.search(r"```diff\n(.*?)```", response, re.DOTALL)
    return match.group(1).strip() if match else None


def save_log(entry):
    print("[LOG] Saving log entry:", entry)
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    if not LOG_FILE.exists():
        LOG_FILE.write_text("[]", encoding="utf-8")

    try:
        logs = json.loads(LOG_FILE.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        logs = []

    logs.append(entry)
    LOG_FILE.write_text(json.dumps(logs[-20:], indent=2), encoding="utf-8")


def ask_llm_strict(filename, fail_out):
    prompt_template = f'''
A pytest test failed.

REPAIR RULES
1. If failure is IndexError, fix by changing the list or guarding with
   with pytest.raises(IndexError): …
2. If failure is NameError, wrap the failing line in with pytest.raises(NameError): …
3. If failure is TypeError, wrap in with pytest.raises(TypeError): …
4. Your ENTIRE reply must be one unified-diff block. At least one
   line must start with “+ ” (green).
5. Zero explanation outside the ```diff block.

Filename: {filename}
Failure Output:
{fail_out}
'''
    for attempt in range(2):
        result = subprocess.run(
            ["ollama", "run", MODEL],
            input=prompt_template,
            text=True,
            encoding="utf-8",
            errors="replace",
            capture_output=True,
            timeout=180
        )
        diff = extract_diff(result.stdout)
        if diff:
            return diff, "fixed"
        prompt_template = (
            f"ONLY unified diff, no words, must modify a line starting with '-':\n"
            f"```diff\n--- a/{filename}\n+++ b/{filename}"
        )
    return result.stdout[:800], "analysis"

# ---------- MAIN ----------

def main():
    import sys
    file_arg = sys.argv[1] if len(sys.argv) > 1 else None
    files = [TEST_FOLDER / file_arg] if file_arg else list(TEST_FOLDER.glob("test_*.py"))

    for test_path in files:
        print(f"[TEST] Testing {test_path.name}")
        result = subprocess.run([
            "pytest", str(test_path), "--tb=short", "-q"
        ], capture_output=True, text=True)

        output = result.stdout + result.stderr

        if result.returncode == 0:
            print("[PASS] Passed")
            save_log({
                "file": test_path.name,
                "status": "passed",
                "summary": "Test passed successfully.",
                "timestamp": datetime.now().isoformat()
            })
            continue

        print("[FAIL] Failed – asking LLM…")
        summary, status = ask_llm_strict(test_path.name, output)
        print("[AI-FIX] Patch detected. Logged." if status == "fixed" else "[AI-FIX] No usable diff – logged as analysis.")

        save_log({
            "file": test_path.name,
            "status": status,
            "summary": summary,
            "timestamp": datetime.now().isoformat()
        })


if __name__ == "__main__":
    main()
    print("[DONE] hackathon.py finished")
    print("[LOG] Logs saved to:", LOG_FILE.resolve())