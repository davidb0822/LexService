from flask import Flask, request, jsonify
import requests
import os

app = Flask(__name__)

# ------------------------
# CONFIG
# ------------------------

BABYLOVE_TOKEN = os.environ.get("BABYLOVE_TOKEN") 
MERCHANTPRO_API_USER = os.environ.get("MP_USER")
MERCHANTPRO_API_PASSWORD = os.environ.get("MP_PASSWORD")
MERCHANTPRO_BASE = os.environ.get("MP_BASE")
MERCHANTPRO_ENDPOINT = os.environ.get("MP_ENDPOINT") 

# ------------------------

@app.route("/")
def home():
    return "MerchantPro Webhook OK", 200

@app.route("/webhook", methods=["POST"])
def webhook():
    # validate token
    auth_header = request.headers.get("Authorization", "")
    if auth_header != f"Bearer {BABYLOVE_TOKEN}":
        return jsonify({"error": "Unauthorized"}), 401

    data = request.json

    title = data.get("title")
    content = data.get("content_html") or data.get("content")
    tags = data.get("tags", [])

    mp_url = MERCHANTPRO_BASE + MERCHANTPRO_ENDPOINT

    payload = {
        "title": title,
        "content": content,
        "tags": tags,
        "status": "published"
    }

    response = requests.post(
        mp_url,
        json=payload,
        auth=(MERCHANTPRO_API_USER, MERCHANTPRO_API_PASSWORD)
    )

    if response.status_code not in [200, 201]:
        return jsonify({
            "error": "MerchantPro API error",
            "details": response.text
        }), 500

    return jsonify({"status": "ok", "merchantpro": response.json()})
