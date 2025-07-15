import subprocess
import re
import json
import os
from datetime import datetime
from pathlib import Path

MODEL = "codellama:13b"
TEST_FOLDER = Path("test_cases").resolve()
LOG_FILE = Path("logs/history.json").resolve()
LOG_FILE.parent.mkdir(parents=True, exist_ok=True)


def extract_diff(response: str) -> str | None:
    """
    Extract a unified diff from LLM response.
    Returns only the diff content (not the ```diff fences).
    """
    code_block_match = re.search(r"```diff\s*(.*?)```", response, re.DOTALL)
    if code_block_match:
        return code_block_match.group(1).strip()

    unified_match = re.search(r"(--- a/.*?\n\+\+\+ b/.*?\n@@.*)" , response, re.DOTALL)
    if unified_match:
        return unified_match.group(1).strip()

    return None


def save_log(entry: dict) -> None:
    try:
        logs = []
        if LOG_FILE.exists():
            try:
                logs = json.loads(LOG_FILE.read_text(encoding="utf-8"))
            except (json.JSONDecodeError, FileNotFoundError):
                logs = []
        logs.append(entry)
        LOG_FILE.write_text(json.dumps(logs, indent=2), encoding="utf-8")
    except Exception as exc:
        print(f"[LOG ERROR] Failed to save log: {exc}")


def ask_llm_strict(filename: str, fail_out: str) -> tuple[str, str]:
    try:
        file_path = TEST_FOLDER / filename
        file_content = file_path.read_text(encoding="utf-8")

        prompt = f"""Fix the following **real test file** which is failing. Respond ONLY with:

A unified diff patch starting from line numbers, like:
```diff
--- a/{filename}
+++ b/{filename}
@@ -X,Y +X,Y @@
-<old code>
+<fixed code>
```

Nothing else – no extra explanations.

File content:
{file_content}

Failure Output:
{fail_out}
"""

        result = subprocess.run(
            ["ollama", "run", MODEL],
            input=prompt,
            text=True,
            capture_output=True,
            timeout=300,
            encoding="utf-8",
            errors="replace",
            check=False,
        )
        if result.returncode != 0:
            return (
                f"LLM Error (exit {result.returncode}): {result.stderr[:500]}",
                "error",
            )

        diff = extract_diff(result.stdout)
        if not diff:
            return (
                f"No valid diff found in response. Full output:\n{result.stdout[:800]}",
                "analysis",
            )

        if not (diff.startswith("--- a/") and "+++ b/" in diff):
            return f"Malformed diff received:\n{diff[:500]}", "analysis"

        return diff, "fixed"

    except subprocess.TimeoutExpired:
        return "LLM timeout after 5 minutes", "error"
    except Exception as exc:
        return f"LLM Process Error: {exc}", "error"


def run_test(test_path: Path):
    try:
        return subprocess.run(
            ["pytest", str(test_path), "--tb=short", "-q"],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=60,
        )
    except subprocess.TimeoutExpired:
        return type("Result", (), {"stdout": "", "stderr": "Test timeout", "returncode": 1})()
    except Exception as exc:
        return type("Result", (), {"stdout": "", "stderr": str(exc), "returncode": 1})()


def main() -> None:
    test_files = sorted(TEST_FOLDER.glob("test_*.py"))
    if not test_files:
        print("❌ No test files found in test_cases/")
        return

    for test_path in test_files:
        print(f"\n🔍 Testing {test_path.name}...")
        result = run_test(test_path)
        output = (result.stdout or "") + (result.stderr or "")

        if result.returncode == 0:
            print("✅ Passed")
            save_log({
                "file": test_path.name,
                "status": "passed",
                "summary": output,
                "timestamp": datetime.now().isoformat(),
            })
            continue

        print("❌ Failed – Consulting AI...")
        diff, status = ask_llm_strict(test_path.name, output)

        if status == "fixed":
            print(f"✏️  AI Generated Fix:\n{diff}")
        elif status == "analysis":
            print(f"ℹ️  Analysis:\n{diff[:500]}...")
        else:
            print(f"⚠️  Error: {diff}")

        save_log({
            "file": test_path.name,
            "status": status,
            "summary": diff if status != "fixed" else f"Suggested fix:\n{diff}",
            "timestamp": datetime.now().isoformat(),
        })


if __name__ == "__main__":
    main()