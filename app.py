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
MERCHANTPRO_ENDPOINT = os.environ.get("MP_ENDPOINT")  # ex: /api/v2/articles

BLOG_CATEGORY_ID = 4  # schimbă dacă ai altă categorie

# -------------------------------------------------------
# Home route (health check)
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

    # Construim SLUG corect
    slug = (data.get("title") or "").lower().strip().replace(" ", "-")

    # Construim payload exact pentru MerchantPro
    payload = {
        "title": data.get("title"),
        "content": data.get("content_html"),  # BABYLOVE trimite doar content_html
        "category_id": BLOG_CATEGORY_ID,

        # SEO
        "meta_title": data.get("title"),
        "meta_description": data.get("metaDescription", ""),

        # Slug
        "slug": slug,

        # Tags goale (MerchantPro cere array)
        "tags": [],

        # Activăm articolul
        "status": "active"
    }

    # URL MerchantPro
    url = MERCHANTPRO_BASE.rstrip("/") + MERCHANTPRO_ENDPOINT

    # Request către MerchantPro
    response = requests.post(
        url,
        json=payload,
        auth=(MERCHANTPRO_API_USER, MERCHANTPRO_API_PASSWORD)
    )

    # Dacă răspunsul nu este OK
    if response.status_code not in (200, 201):
        print("=== MERCHANTPRO ERROR ===")
        print("Status:", response.status_code)
        print("Response text:", response.text)
        print("Payload sent:", payload)
        print("==========================")

        return jsonify({
            "error": "MerchantPro API error",
            "mp_status": response.status_code,
            "mp_response": response.text,
            "payload": payload
        }), 500

    # Succes
    return jsonify({
        "status": "ok",
        "merchantpro": response.json()
    })
