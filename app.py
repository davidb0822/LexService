from flask import Flask, request, jsonify
import requests
import os

app = Flask(__name__)

# -------------------------------------------------------
# Config
# -------------------------------------------------------
BABYLOVE_TOKEN = os.environ.get("BABYLOVE_TOKEN")
MERCHANTPRO_API_USER = os.environ.get("MP_USER")
MERCHANTPRO_API_PASSWORD = os.environ.get("MP_PASSWORD")
MERCHANTPRO_BASE = os.environ.get("MP_BASE")
MERCHANTPRO_ENDPOINT = os.environ.get("MP_ENDPOINT")  # /api/v2/articles

# -------------------------------------------------------
# Home route
# -------------------------------------------------------
@app.route("/")
def home():
    return "MerchantPro Webhook OK", 200

# -------------------------------------------------------
# Webhook route
# -------------------------------------------------------
@app.route("/webhook", methods=["POST"])
def webhook():
    # Validate token
    auth_header = request.headers.get("Authorization", "")
    if auth_header != f"Bearer {BABYLOVE_TOKEN}":
        return jsonify({"error": "Unauthorized"}), 401

    data = request.json

    # ---------------------------------------------------
    # IMPORTANT: category_id TREBUIE să fie valid în MP
    # ---------------------------------------------------
    # Pune aici ID-ul categoriei tale de blog din MerchantPro
    BLOG_CATEGORY_ID = 4  # <-- modifică cu ID-ul tău real

    payload = {
        "title": data.get("title"),
        "content": data.get("content_html") or data.get("content"),
        "category_id": BLOG_CATEGORY_ID,

        # SEO
        "meta_title": data.get("title"),
        "meta_description": data.get("meta_description", ""),

        # Slug
        "slug": data.get("slug") or data.get("title").replace(" ", "-").lower(),

        # Tags
        "tags": data.get("tags") or [],

        # Status
        "status": "active"
    }

    # URL final
    url = MERCHANTPRO_BASE.rstrip("/") + MERCHANTPRO_ENDPOINT

    # Request către MerchantPro
    response = requests.post(
        url,
        json=payload,
        auth=(MERCHANTPRO_API_USER, MERCHANTPRO_API_PASSWORD)
    )

    # Dacă MP răspunde cu eroare, o trimitem ca debug
    if response.status_code not in (200, 201):
        return jsonify({
            "error": "MerchantPro API error",
            "mp_status_code": response.status_code,
            "mp_response": response.text,
            "sent_payload": payload
        }), 500

    # Succes
    return jsonify({
        "status": "ok",
        "merchantpro": response.json()
    })
