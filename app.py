from flask import Flask, request, jsonify
import requests
import os

app = Flask(__name__)

# -------------------------------------------------------
# Config din variabile de mediu
# -------------------------------------------------------
BABYLOVE_TOKEN = os.environ.get("BABYLOVE_TOKEN")  # webhook secret
MERCHANTPRO_API_USER = os.environ.get("MP_USER")
MERCHANTPRO_API_PASSWORD = os.environ.get("MP_PASSWORD")
MERCHANTPRO_BASE = os.environ.get("MP_BASE")  # ex: https://lexservice.ro
MERCHANTPRO_ENDPOINT = os.environ.get("MP_ENDPOINT")  # ex: /api/v2/articles

BLOG_CATEGORY_ID = 4  # categoria blogului din MerchantPro


# -------------------------------------------------------
# Health check
# -------------------------------------------------------
@app.route("/")
def home():
    return "MerchantPro Webhook OK", 200


# -------------------------------------------------------
# Webhook BabyLoveGrowth → MerchantPro
# -------------------------------------------------------
@app.route("/webhook", methods=["POST"])
def webhook():

    # 1. SECURITY CHECK
    auth_header = request.headers.get("Authorization", "")
    if auth_header != f"Bearer {BABYLOVE_TOKEN}":
        return jsonify({"error": "Unauthorized"}), 401

    data = request.json or {}

    # 2. Folosim SLUG trimis de BabyLoveGrowth
    slug = data.get("slug") or ""

    # 3. Content HTML
    content_html = data.get("content_html") or ""

    # 4. Trimitem către MerchantPro
    payload = {
        "title": data.get("title"),
        "content": content_html,
        "category_id": BLOG_CATEGORY_ID,

        # SEO
        "meta_title": data.get("title"),
        "meta_description": data.get("metaDescription", ""),

        # SLUG FINAL
        "slug": slug,

        # MerchantPro cere array
        "tags": [],

        # Publicat
        "status": "active",
    }

    url = MERCHANTPRO_BASE.rstrip("/") + MERCHANTPRO_ENDPOINT

    response = requests.post(
        url,
        json=payload,
        auth=(MERCHANTPRO_API_USER, MERCHANTPRO_API_PASSWORD)
    )

    # 5. Error logging
    if response.status_code not in (200, 201):
        print("=== MERCHANTPRO ERROR ===")
        print("Status:", response.status_code)
        print("Response text:", response.text)
        print("Payload:", payload)
        print("==========================")

        return jsonify({
            "error": "MerchantPro API error",
            "mp_status": response.status_code,
            "mp_response": response.text
        }), 500

    # 6. Succes
    return jsonify({
        "status": "ok",
        "merchantpro_response": response.json()
    })
