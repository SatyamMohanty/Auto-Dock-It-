# FINAL ERROR-FREE app.py
import streamlit as st
import subprocess
import json
import os
from pathlib import Path
import datetime

MODEL = "codellama:13b"
PROJECT_ROOT = Path(__file__).resolve().parent.parent
TEST_DIR = PROJECT_ROOT / os.path.normpath("test_cases")
LOG_PATH = PROJECT_ROOT / os.path.normpath("logs/history.json")
LOG_PATH.parent.mkdir(parents=True, exist_ok=True)

st.set_page_config(
    page_title="BuildBuddy DevOps Agent",
    layout="wide",
    page_icon="🛠️",
    menu_items={
        'Get Help': 'https://github.com/your-repo',
        'Report a bug': "https://github.com/your-repo/issues",
    }
)


def list_tests():
    try:
        return sorted([f.name for f in TEST_DIR.glob("test_*.py") if f.is_file()])
    except Exception:
        return []


def run_backend(file_name=None):
    cmd = ["python", "hackathon.py"]
    if file_name:
        cmd.append(file_name)
    try:
        return subprocess.run(
            cmd,
            cwd=PROJECT_ROOT,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=600
        )
    except subprocess.TimeoutExpired:
        return type('', (), {'stdout': '', 'stderr': 'Operation timed out', 'returncode': 1})()


def tail_log(n=10):
    if not LOG_PATH.exists():
        return []
    try:
        with open(LOG_PATH, encoding="utf-8") as f:
            return json.load(f)[-n:][::-1]
    except Exception:
        return []


def clear_logs():
    try:
        LOG_PATH.write_text("[]", encoding="utf-8")
        return True
    except Exception:
        return False


# UI Layout
st.title("🧠 BuildBuddy DevOps Agent")
st.caption("AI-powered test fixing with CodeLlama (Offline)")

left, right = st.columns([1, 1.4])

with left:
    st.header("🔧 Test Operations")
    tests = list_tests()

    if not tests:
        st.error("No test files found in test_cases/")
    else:
        selected = st.selectbox("Select test:", tests)

        col1, col2 = st.columns(2)
        with col1:
            if st.button("🛠️ Fix Selected Test", help="Run AI fix on selected test", use_container_width=True):
                with st.spinner("Fixing..."):
                    result = run_backend(selected)
                    st.session_state.last_output = result.stdout + result.stderr
                st.toast("Fix completed!", icon="✅")

        with col2:
            if st.button("⚡ Fix All Tests", type="primary", use_container_width=True):
                with st.spinner("Fixing all tests..."):
                    result = run_backend()
                    st.session_state.last_output = result.stdout + result.stderr
                st.toast("All tests processed!", icon="✅")

        if st.button("🗑️ Clear Logs", type="secondary"):
            if clear_logs():
                st.toast("Logs cleared!", icon="🗑️")
            else:
                st.error("Failed to clear logs")

with right:
    st.header("📜 Execution Logs")
    logs = tail_log(20)

    if not logs:
        st.info("No logs yet. Run tests to see results")
    else:
        tab1, tab2 = st.tabs(["Latest Fix", "History"])

        with tab1:
            latest = logs[0]
            st.subheader(f"{latest['file']} ({latest['status'].upper()})")
            st.caption(f"🕒 {latest['timestamp']}")
            st.code(latest['summary'], language="diff" if latest['status'] == "fixed" else "text")

        with tab2:
            for entry in logs:
                with st.expander(f"{entry['file']} - {entry['status']} ({entry['timestamp'][:19]})"):
                    st.code(entry['summary'], language="diff" if entry['status'] == "fixed" else "text")

    if 'last_output' in st.session_state:
        with st.expander("🔍 Raw Output"):
            st.code(st.session_state.last_output)