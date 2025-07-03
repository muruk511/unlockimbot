from flask import Flask, request, jsonify, render_template, redirect
from firebase_admin import credentials, firestore, initialize_app
import os

app = Flask(__name__)

# Initialize Firebase
cred_path = os.getenv("FIREBASE_CREDENTIALS", "unlockimbot-bffb5-firebase-adminsdk-fbsvc-3939329081.json")
cred = credentials.Certificate(cred_path)
initialize_app(cred)
db = firestore.client()

tools_ref = db.collection("tools")

# Admin Panel (basic password protection)
ADMIN_PASSWORD = os.getenv("ADMIN_PASS", "unlockadmin")

import traceback

@app.route("/")
def home():
    try:
        tools = [doc.to_dict() for doc in tools_ref.stream()]
        return render_template("dashboard.html", tools=tools)
    except Exception as e:
        error_trace = traceback.format_exc()
        print(f"Error loading dashboard: {error_trace}")
        return f"<h1>Error loading dashboard</h1><pre>{error_trace}</pre>", 500

@app.route("/login", methods=["POST"])
def login():
    if request.form.get("password") == ADMIN_PASSWORD:
        return redirect("/")
    return "Access Denied", 403

@app.route("/update_tool", methods=["POST"])
def update_tool():
    try:
        tool = request.form.get("tool")
        status = request.form.get("status")
        price = int(request.form.get("price"))
        duration = int(request.form.get("duration"))
        tools_ref.document(tool).update({
            "status": status,
            "price": price,
            "duration": duration
        })
        return redirect("/")
    except Exception as e:
        print(f"Error updating tool: {e}")
        return "Failed to update", 500

@app.route("/api/tool_rental")
def tool_rental():
    try:
        tools = [doc.to_dict() for doc in tools_ref.stream()]
        msg = "\ud83d\udee0\ufe0f Available Tools for Rent:\n"
        for tool in tools:
            duration_hr = round(tool['duration'] / 60, 1)
            msg += f"{tool['name']}: {'✅' if tool['status'] == 'available' else '❌ In Use'} - PGK {tool['price']} / {duration_hr} hours\n"

        return jsonify({"response": msg})
    except Exception as e:
        print(f"Error fetching tools: {e}")
        return jsonify({"response": "Failed to fetch tools"}), 500

@app.route("/api/<toolname>_status")
def tool_status(toolname):
    try:
        doc = tools_ref.document(toolname).get()
        if doc.exists:
            tool = doc.to_dict()
            duration_hr = round(tool['duration'] / 60, 1)
            msg = f"🔍 {tool['name']} Status:\nStatus: {'✅ Available' if tool['status']=='available' else '❌ In Use'}\nPrice: PGK {tool['price']}\nDuration: {duration_hr} hours"

            return jsonify({"response": msg})
        return jsonify({"response": "Tool not found."})
    except Exception as e:
        print(f"Error fetching status: {e}")
        return jsonify({"response": "Failed to fetch tool status"}), 500

@app.route("/ping")
def ping():
    return "pong", 200

if __name__ == "__main__":
    import os
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
