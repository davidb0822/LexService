from flask import Flask, request, jsonify
import requests
import os
import re
import unicodedata

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
# Slug generator (fara diacritice, fara caractere speciale)
# -------------------------------------------------------
def generate_slug(text):
    if not text:
        return "articol"
    
    # 1. normalize unicode → ASCII
    text = unicodedata.normalize('NFKD', text)
    text = text.encode('ascii', 'ignore').decode('ascii')

    # 2. lowercase
    text = text.lower()

    # 3. înlocuiește caracterele nepermise cu "-"
    text = re.sub(r'[^a-z0-9]+', '-', text)

    # 4. elimină '-' de la început/sfârșit
    text = text.strip('-')

    return text

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

    title = data.get("title", "")
    content_html = data.get("content_html", "")
    meta_desc = data.get("metaDescription", "")

    # Construim SLUG corect
    slug = generate_slug(title)

    # Construim payload exact pentru MerchantPro
    payload = {
        "title": title,
        "content": content_html,
        "category_id": BLOG_CATEGORY_ID,

        # SEO
        "meta_title": title,
        "meta_description": meta_desc,

        # Slug curat
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
