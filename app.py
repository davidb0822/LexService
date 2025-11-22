from flask import Flask, request, jsonify
import requests
import os
import threading

app = Flask(__name__)

# -------------------------------------------------------
# Config din Render -> Environment Variables
# -------------------------------------------------------
BABYLOVE_TOKEN = os.environ.get("BABYLOVE_TOKEN")
MERCHANTPRO_API_USER = os.environ.get("MP_USER")
MERCHANTPRO_API_PASSWORD = os.environ.get("MP_PASSWORD")
MERCHANTPRO_BASE = os.environ.get("MP_BASE")
MERCHANTPRO_ENDPOINT = os.environ.get("MP_ENDPOINT")

BLOG_CATEGORY_ID = 4  # modifică dacă e alt ID la tine


# -------------------------------------------------------
# Funcția care procesează în background
# -------------------------------------------------------
def process_webhook(data):
    try:
        print("=== Webhook received, processing in background ===")

        slug = data.get("slug") or ""

        payload = {
            "title": data.get("title"),
            "content": data.get("content_html"),
            "category_id": BLOG_CATEGORY_ID,
            "meta_title": data.get("title"),
            "meta_description": data.get("metaDescription", ""),
            "slug": slug,
            "tags": [],
            "status": "active"
        }

        url = MERCHANTPRO_BASE.rstrip("/") + MERCHANTPRO_ENDPOINT

        print("Payload for MerchantPro:", payload)

        response = requests.post(
            url,
            json=payload,
            auth=(MERCHANTPRO_API_USER, MERCHANTPRO_API_PASSWORD)
        )

        if response.status_code not in (200, 201):
            print("=== MERCHANTPRO ERROR ===")
            print("Status:", response.status_code)
            print("Response:", response.text)
            print("=========================")
        else:
            print("=== Article successfully created in MerchantPro ===")
            print(response.json())

    except Exception as e:
        print("=== EXCEPTION IN BACKGROUND ===")
        print(str(e))
        print("===============================")


# -------------------------------------------------------
# Home — health check
# -------------------------------------------------------
@app.route("/")
def home():
    return "MerchantPro Webhook OK", 200


# -------------------------------------------------------
# Webhook — răspundem instant, procesăm după
# -------------------------------------------------------
@app.route("/webhook", methods=["POST"])
def webhook():

    # verificăm Bearer Token
    auth_header = request.headers.get("Authorization", "")
    if auth_header != f"Bearer {BABYLOVE_TOKEN}":
        return jsonify({"error": "Unauthorized"}), 401

    data = request.json

    # răspuns instant → BabyLove primește 200 imediat
    response = jsonify({"status": "received"})
    response.status_code = 200

    # procesăm în background
    threading.Thread(target=process_webhook, args=(data,)).start()

    return response


# -------------------------------------------------------
# Run local (optional)
# -------------------------------------------------------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
