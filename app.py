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

    # Validate Babylove token
    auth_header = request.headers.get("Authorization", "")
    if auth_header != f"Bearer {BABYLOVE_TOKEN}":
        return jsonify({"error": "Unauthorized"}), 401

    data = request.json

    # Folosim slug EXACT cum îl trimite Babylove
    slug = data.get("slug") or ""

    # Content HTML generat de Babylove
    content_html = data.get("content_html") or ""

    # Construim payload exact pentru MerchantPro
    payload = {
        "title": data.get("title"),
        "content": content_html,
        "category_id": BLOG_CATEGORY_ID,

        # SEO
        "meta_title": data.get("title"),
        "meta_description": data.get("metaDescription", ""),

        # Slug direct din Babylove
        "slug": slug,

        # MerchantPro cere array pentru tags
        "tags": [],

        # Activăm articolul
        "status": "active"
    }

    # URL final MP
    url = MERCHANTPRO_BASE.rstrip("/") + MERCHANTPRO_ENDPOINT

    # Request către MerchantPro
    response = requests.post(
        url,
        json=payload,
        auth=(MERCHANTPRO_API_USER, MERCHANTPRO_API_PASSWORD)
    )

    # Dacă MP răspunde cu eroare → logăm tot
    if response.status_code not in (200, 201):
        print("=== MERCHANTPRO ERROR ===")
        print("URL:", url)
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
