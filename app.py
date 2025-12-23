import os
import subprocess
import socket
from flask import Flask, render_template, redirect, url_for, send_from_directory, jsonify, request
from dotenv import load_dotenv

# Load variables from .env
load_dotenv()

app = Flask(__name__)

# --- CONFIG ---
DEV_MODE = os.getenv("DEV_MODE", "True").lower() == "true"
PC_MAC = os.getenv("PC_MAC")
PC_IP = os.getenv("PC_IP")
PC_USER = os.getenv("PC_USER")

def pc_online():
    """Checks if the PC is reachable via network (Port 445 for SMB)."""
    if DEV_MODE: return True 
    try:
        socket.create_connection((PC_IP, 445), timeout=1.5)
        return True
    except:
        return False

@app.route("/")
def index():
    return render_template("index.html", online=pc_online())

@app.route("/status")
def status():
    """Endpoint for background JS polling."""
    return jsonify({"online": pc_online()})

@app.route("/on", methods=["POST"])
def turn_on():
    if not DEV_MODE:
        subprocess.run(["wakeonlan", PC_MAC])
    return redirect(url_for("index"))

@app.route("/off", methods=["POST"])
def turn_off():
    pwd = request.form.get("pc_password")
    if not DEV_MODE:
        # Uses sshpass to feed the password to the SSH command
        # StrictHostKeyChecking=no prevents the 'Are you sure?' prompt
        subprocess.run([
            "sshpass", "-p", pwd, 
            "ssh", "-o", "StrictHostKeyChecking=no", 
            f"{PC_USER}@{PC_IP}", "shutdown /s /t 0"
        ], check=False)
    return redirect(url_for("index"))

@app.route("/manifest.json")
def manifest():
    return {
        "name": "PC Controller",
        "short_name": "PC Power",
        "start_url": "/",
        "display": "standalone",
        "background_color": "#1a202c",
        "theme_color": "#1a202c",
        "icons": [{
            "src": "https://cdn-icons-png.flaticon.com/512/1828/1828479.png",
            "sizes": "512x512",
            "type": "image/png"
        }]
    }

@app.route("/sw.js")
def service_worker():
    return send_from_directory('static', 'sw.js')

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
