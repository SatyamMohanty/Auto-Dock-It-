import streamlit as st
import subprocess
import json
from pathlib import Path
import datetime

# ---------- CONFIG ----------
MODEL = "codellama:13b"
PROJECT_ROOT = Path(__file__).resolve().parent.parent          # .../project
TEST_DIR = PROJECT_ROOT / "test_cases"                        # .../project/test_cases
LOG_PATH = PROJECT_ROOT / "logs" / "history.json"            # .../project/logs/history.json

# Ensure logs file exists
LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
if not LOG_PATH.exists():
    LOG_PATH.write_text("[]", encoding="utf-8")

# ---------- STREAMLIT PAGE ----------
st.set_page_config(page_title="Build‑Buddy DevOps Agent", layout="wide", page_icon="🧠")
st.title("🧠 Build‑Buddy DevOps Agent")
st.caption("Offline AI that detects & fixes failing pytest tests with CodeLlama.")

# ---------- HELPERS ----------

def list_tests() -> list[str]:
    """Return sorted list of test_*.py names in test_cases folder."""
    return sorted([f.name for f in TEST_DIR.glob("test_*.py")])


def run_backend(file_name: str | None = None) -> subprocess.CompletedProcess:
    """Run hackathon.py (always from PROJECT_ROOT) and return CompletedProcess."""
    cmd = ["python", str(PROJECT_ROOT / "hackathon.py")]
    if file_name:
        cmd.append(file_name)

    return subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        cwd=PROJECT_ROOT,
    )


def tail_log(n: int = 10) -> list[dict]:
    """Return last *n* log entries (newest first)."""
    try:
        with open(LOG_PATH, encoding="utf-8") as f:
            data = json.load(f)
            return data[-n:][::-1]
    except Exception as e:
        print("[Log Load Error]", e)
        return []

# ---------- UI LAYOUT ----------
left, right = st.columns([1, 1.3])

with left:
    st.header("📂 Choose / Fix a Test")

    if st.button("🧹 Clear Log History", use_container_width=True):
        LOG_PATH.write_text("[]", encoding="utf-8")
        st.success("Logs cleared!")

    tests = list_tests()
    if not tests:
        st.warning("No test files found in test_cases folder.")
        test_file = None
    else:
        test_file = st.selectbox("Select test file", tests, key="test_box")
        run_btn = st.button("🧪 Run & Fix Selected Test", use_container_width=True)
        run_all_btn = st.button("🚀 Run All Tests", use_container_width=True)

        if run_btn and test_file:
            with st.spinner("Running backend AI fixer on selected test …"):
                result = run_backend(test_file)

            if result.stderr:
                st.error("⚠️ Backend stderr:\n\n" + result.stderr)
                st.code(result.stdout, language="bash")
            else:
                st.success("✅ Backend finished! Check AI Patch Output →")
                st.code(result.stdout, language="bash")

        if run_all_btn:
            with st.spinner("Running backend AI fixer on ALL tests …"):
                result = run_backend()

            if result.stderr:
                st.error("⚠️ Backend stderr:\n\n" + result.stderr)
                st.code(result.stdout, language="bash")
            else:
                st.success("🎉 All tests completed! Check AI Patch Output →")
                st.code(result.stdout, language="bash")

with right:
    st.header("📜 AI Patch Output & History")
    history = tail_log(20)

    if not history:
        st.info("No logs yet. Run a test from the left panel.")
        st.caption(f"(Looking at: {LOG_PATH.resolve()})")
    else:
        matching_entry = None
        if 'test_file' in locals() and test_file:
            for entry in history:
                if entry["file"] == test_file:
                    matching_entry = entry
                    break

        if matching_entry:
            st.subheader("🆕 Latest Result")
            st.markdown(
                f"**File:** `{matching_entry['file']}`  •  **Status:** `{matching_entry['status']}`  •  **Time:** `{matching_entry['timestamp']}`"
            )
            st.code(matching_entry["summary"], language="diff")
        elif 'test_file' in locals() and test_file:
            st.warning(f"No results found for `{test_file}` yet. Please run it from the left panel.")

        with st.expander("📜 Show Last 10 Runs"):
            for entry in history:
                st.markdown(f"**{entry['timestamp']}** — `{entry['file']}` — `{entry['status']}`")
                st.code(entry["summary"][:600], language="diff")
                st.markdown("---")