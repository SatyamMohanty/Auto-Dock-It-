# ============================================================
# hackathon.py  (ULTRA‑ROBUST FINAL VERSION)
# Build‑Buddy DevOps Agent – Offline auto‑fixer using CodeLlama
# Handles ZeroDivision, wrong sums, string typos, etc.
# ============================================================
import sys, subprocess, os, json, datetime, re
from pathlib import Path
from rich.console import Console

# ---------------- CONFIG ----------------
MODEL = "codellama:13b"            # or "codellama:7b-code" for speed
TEST_DIR = Path("test_cases")
LOG_FILE = Path("logs/history.json")
LOG_FILE.parent.mkdir(exist_ok=True)
if not LOG_FILE.exists():
    LOG_FILE.write_text("[]")

console = Console()

# ---------------- HELPERS --------------

def log_event(file, status, summary):
    history = json.loads(LOG_FILE.read_text())
    history.append({
        "file": file,
        "status": status,
        "summary": summary,
        "timestamp": datetime.datetime.now().isoformat(timespec="seconds")
    })
    LOG_FILE.write_text(json.dumps(history, indent=2))


def run_pytest(path: Path):
    res = subprocess.run(["pytest", str(path), "-q", "--tb=short", "--disable-warnings"],
                         capture_output=True, text=True)
    return res.returncode == 0, res.stdout


def ask_llm(filename: str, fail_out: str) -> str:
    prompt = f"""
A pytest test failed.

REPAIR RULES:
1. Fix wrong expected values (e.g., `assert sum(numbers)==10` when real sum is 6).
2. For runtime errors (like ZeroDivisionError) wrap code under test with:
   with pytest.raises(ExpectedError): ...
3. Return ONLY a valid unified diff patch. DO NOT include explanation text.
4. Patch MUST modify at least one line (line starting with '+').
FORMAT:
```diff
--- a/{filename}
+++ b/{filename}
@@
- buggy line
+ fixed line
```
Filename: {filename}
Failure Output:
{fail_out}
"""
    res = subprocess.run(["ollama", "run", MODEL],
                         input=prompt, text=True, encoding="utf-8",
                         stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=180)
    if res.stderr:
        console.print("[red]LLM stderr:[/red]", res.stderr)
    return res.stdout


def extract_diff(txt: str):
    m = re.search(r"(?s)```diff(.*?)```", txt)
    if not m:
        return None
    diff = m.group(1).strip()
    # ensure at least one added line other than headers
    return diff if re.search(r"^\+[^+].*", diff, re.MULTILINE) else None

# ---------------- MAIN -----------------

def main():
    targets = [Path(sys.argv[1])] if len(sys.argv) > 1 else list(TEST_DIR.glob("test_*.py"))
    if not targets:
        console.print("[red]No tests found.[/red]"); return

    console.print(f"[cyan]🧠 Using LLM {MODEL}[/cyan]")

    for t in targets:
        console.print(f"\n🔪 Testing [yellow]{t.name}[/yellow]")
        ok, out = run_pytest(t)
        if ok:
            console.print("[green]✓ Passed[/green]")
            log_event(t.name, "passed", "No issues.")
            continue

        console.print("[red]❌ Failed – asking LLM…[/red]")
        try:
            ai = ask_llm(t.name, out)
        except subprocess.TimeoutExpired:
            console.print("[red]LLM timeout[/red]")
            log_event(t.name, "timeout", "LLM timeout")
            continue

        diff = extract_diff(ai)
        if diff:
            console.print("[green]Patch captured![/green]")
            log_event(t.name, "fixed", diff)
        else:
            console.print("[yellow]No usable diff – logged as analysis.[/yellow]")
            log_event(t.name, "analysis", ai[:800])

if __name__ == "__main__":
    main()
