from flask import Flask, request, jsonify
import requests
import os

app = Flask(__name__)

BABYLOVE_TOKEN = os.environ.get("BABYLOVE_TOKEN")
MP_USER = os.environ.get("MP_USER")
MP_PASSWORD = os.environ.get("MP_PASSWORD")
MP_BASE = os.environ.get("MP_BASE")
MP_ENDPOINT = os.environ.get("MP_ENDPOINT")
BLOG_CATEGORY_ID = 4


# ---------------------------------------------------------
# HEALTH CHECK
# ---------------------------------------------------------
@app.route("/")
def home():
    return "OK", 200


# ---------------------------------------------------------
# BABYLOVE WEBHOOK → răspunde instant și pasează jobul
# ---------------------------------------------------------
@app.route("/webhook", methods=["POST"])
def webhook():
    auth = request.headers.get("Authorization", "")
    if auth != f"Bearer {BABYLOVE_TOKEN}":
        return jsonify({"error": "Unauthorized"}), 401

    data = request.json

    # Trimitem payload-ul la endpoint-ul nostru intern
    try:
        requests.post(
            request.url_root.rstrip("/") + "/process",
            json=data,
            timeout=1  # foarte scurt, să nu blocheze
        )
    except:
        pass  # ignorăm timeout-ul

    return jsonify({"status": "received"}), 200


# ---------------------------------------------------------
# ENDPOINT INTERN CARE PROCSEAZĂ FĂRĂ LIMITĂ
# ---------------------------------------------------------
@app.route("/process", methods=["POST"])
def process_article():
    data = request.json
    print("=== Processing article in /process ===")

    slug = data.get("slug", "")

    payload = {
        "title": data.get("title"),
        "content": data.get("content_html"),
        "category_id": BLOG_CATEGORY_ID,
        "meta_title": data.get("title"),
        "meta_description": data.get("metaDescription", ""),
        "slug": slug,
        "tags": [],
        "status": "active",
    }

    url = MP_BASE.rstrip("/") + MP_ENDPOINT
    print("Sending to MerchantPro:", payload)

    resp = requests.post(
        url,
        json=payload,
        auth=(MP_USER, MP_PASSWORD)
    )

    print("MerchantPro status:", resp.status_code)
    print("MerchantPro response:", resp.text)

    return jsonify({"status": "done"}), 200


if __name__ == "__main__":
    app.run()
