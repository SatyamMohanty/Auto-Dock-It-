import streamlit as st
import subprocess
import json
from pathlib import Path
import datetime

# ---------- CONFIG ----------
MODEL = "codellama:13b"
PROJECT_ROOT = Path(__file__).resolve().parent.parent
TEST_DIR = PROJECT_ROOT / "test_cases"
LOG_PATH = PROJECT_ROOT / "logs" / "history.json"

# ---------- STREAMLIT PAGE ----------
st.set_page_config(page_title="Build‑Buddy DevOps Agent", layout="wide", page_icon="🧠")
st.title("🧠 Build‑Buddy DevOps Agent")
st.caption("Offline AI that detects & fixes failing pytest tests with CodeLlama.")

# ---------- HELPERS ----------

def list_tests():
    return sorted([f.name for f in TEST_DIR.glob("test_*.py")])

def run_backend(file_name: str | None = None):
    cmd = ["python", "hackathon.py"]
    if file_name:
        cmd.append(file_name)
    return subprocess.run(cmd, capture_output=True, text=True)

def tail_log(n: int = 10):
    if LOG_PATH.exists():
        with open(LOG_PATH) as f:
            data = json.load(f)
            return data[-n:][::-1]  # newest first
    return []

# ---------- UI LAYOUT ----------
left, right = st.columns([1, 1.3])

with left:
    st.header("📂 Choose / Fix a Test")
    tests = list_tests()
    if not tests:
        st.warning("No test files found in test_cases folder.")
    else:
        test_file = st.selectbox("Select test file", tests, key="test_box")
        run_btn = st.button("🧪 Run & Fix with AI", use_container_width=True)

        if run_btn:
            with st.spinner("Running backend AI fixer …"):
                run_backend(test_file)
            st.success("Backend finished! Check AI Patch Output →")

with right:
    st.header("📜 AI Patch Output & History")
    history = tail_log(20)

    if not history:
        st.info("No logs yet. Run a test from the left panel.")
    else:
        matching_entry = None
        for entry in history:
            if entry["file"] == test_file:
                matching_entry = entry
                break

        if matching_entry:
            st.subheader("🆕 Latest Result")
            st.markdown(f"**File:** `{matching_entry['file']}`  •  **Status:** `{matching_entry['status']}`  •  **Time:** `{matching_entry['timestamp']}`")
            st.code(matching_entry['summary'], language="diff")
        else:
            st.warning(f"No results found for `{test_file}` yet. Please run it from the left panel.")

        with st.expander("📜 Show Last 10 Runs"):
            for entry in history:
                st.markdown(f"**{entry['timestamp']}** — `{entry['file']}` — `{entry['status']}`")
                st.code(entry['summary'][:600], language="diff")
                st.markdown("---")
