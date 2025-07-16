from flask import Flask, request, jsonify, send_file
import os
from repo_cloner import clone_repository
from analyzer import analyze_repo
from flask_cors import CORS



app = Flask(__name__)
CORS(app)


@app.route('/analyze', methods=['POST'])
def analyze():
    data = request.get_json()
    repo_url = data.get("repo_url")
    model = data.get("model", "llama3")  # <-- ✅ Get model from frontend, default to llama3

    if not repo_url:
        return jsonify({"error": "Repository URL is required"}), 400

    clone_path = clone_repository(repo_url)
    if not clone_path:
        return jsonify({"error": "Failed to clone repository"}), 500

    result = analyze_repo(clone_path, model_name=model)  # ✅ Pass model to analyzer

    return jsonify({"analysis": result})


@app.route('/download-dockerfile', methods=['GET'])
def download_dockerfile():
    path = "data/cloned_repo/Dockerfile"
    if os.path.exists(path):
        return send_file(path, as_attachment=True)
    return jsonify({"error": "Dockerfile not found."}), 404

import zipfile
from flask import send_file

@app.route('/', methods=['GET'])
def home():
    return "👋 Hello from BuildBuddy Backend! Use /analyze or /chat APIs.", 200


@app.route('/download-all', methods=['GET'])
def download_all():
    base_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))  # Go one level up from /backend
    data_path = os.path.join(base_path, 'data', 'cloned_repo')
    dockerfile = os.path.join(data_path, 'Dockerfile')
    configfile = os.path.join(data_path, 'config.json')
    zip_path = os.path.join(data_path, 'project_bundle.zip')

    # Ensure the directory exists before zipping
    if not os.path.exists(data_path):
        return jsonify({"error": "Cloned repository folder not found."}), 404

    try:
        with zipfile.ZipFile(zip_path, 'w') as zipf:
            if os.path.exists(dockerfile):
                zipf.write(dockerfile, arcname="Dockerfile")
            if os.path.exists(configfile):
                zipf.write(configfile, arcname="config.json")
    except Exception as e:
        return jsonify({"error": str(e)}), 500

    return send_file(zip_path, as_attachment=True)

from flask import request, jsonify
import subprocess

@app.route('/chat', methods=['POST'])
def chat():
    data = request.get_json()
    message = data.get("message")
    model = data.get("model", "llama3")

    if not message:
        return jsonify({"reply": "❌ No message provided."})

    prompt = f"You are BuildBuddy, an AI DevOps assistant. Answer the question clearly:\n\n{message}"

    try:
        result = subprocess.run(
            ["ollama", "run", model],
            input=prompt.encode("utf-8"),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=60,
        )

        output = result.stdout.decode("utf-8")
        return jsonify({"reply": output.strip()})

    except subprocess.TimeoutExpired:
        return jsonify({"reply": "⚠️ LLM timed out. Please try again."})

    except FileNotFoundError:
        return jsonify({"reply": "❌ Ollama is not installed or the model is missing."})

    except Exception as e:
        return jsonify({"reply": f"❌ Error: {str(e)}"})


if __name__ == '__main__':
    app.run(port=8000, debug=True)
