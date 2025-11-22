from flask import Flask, request, jsonify
import requests
import os
import re

app = Flask(__name__)

BABYLOVE_TOKEN = os.environ.get("BABYLOVE_TOKEN")
MP_USER = os.environ.get("MP_USER")
MP_PASSWORD = os.environ.get("MP_PASSWORD")
MP_BASE = os.environ.get("MP_BASE")            # ex: https://flex.merchantpro.com
MP_ENDPOINT = os.environ.get("MP_ENDPOINT")    # ex: /api/v2/articles
BLOG_CATEGORY_ID = 4


# ---------------------------------------------------------
# CLEAN HTML (MerchantPro nu acceptă <script>, <style>, SVG, JS inline)
# ---------------------------------------------------------
def sanitize_html(html):
    if not html:
        return ""
    # remove script/style
    html = re.sub(r"<script[\s\S]*?</script>", "", html, flags=re.IGNORECASE)
    html = re.sub(r"<style[\s\S]*?</style>", "", html, flags=re.IGNORECASE)
    # remove svg
    html = re.sub(r"<svg[\s\S]*?</svg>", "", html, flags=re.IGNORECASE)
    # remove on*="" handlers (onclick, onload etc)
    html = re.sub(r'on\w+="[^"]*"', "", html)
    # remove iframes (MP nu acceptă)
    html = re.sub(r"<iframe[\s\S]*?</iframe>", "", html, flags=re.IGNORECASE)
    return html.strip()


# ---------------------------------------------------------
# HEALTH CHECK
# ---------------------------------------------------------
@app.route("/")
def home():
    return "OK", 200


# ---------------------------------------------------------
# BABYLOVE → returnează instant
# ---------------------------------------------------------
@app.route("/webhook", methods=["POST"])
def webhook():
    auth = request.headers.get("Authorization", "")
    if auth != f"Bearer {BABYLOVE_TOKEN}":
        return jsonify({"error": "Unauthorized"}), 401

    data = request.json

    try:
        requests.post(
            request.url_root.rstrip("/") + "/process",
            json=data,
            timeout=1
        )
    except:
        pass

    return jsonify({"status": "received"}), 200


# ---------------------------------------------------------
# PROCESARE REALĂ FĂRĂ LIMITĂ DE TIMP
# ---------------------------------------------------------
@app.route("/process", methods=["POST"])
def process_article():
    data = request.json
    print("\n=== Processing article ===")

    title = data.get("title", "")
    slug = data.get("slug", "")
    meta_desc = data.get("metaDescription", "")
    html = sanitize_html(data.get("content_html", ""))

    payload = {
        "title": title,
        "content": html,
        "category_id": BLOG_CATEGORY_ID,
        "status": "active",
        "meta_title": title,
        "meta_description": meta_desc,
        "slug": slug,
        "tags": [],
        "author": "BabyLoveGPT"   # opțional
    }

    print("Payload:", payload)

    url = MP_BASE.rstrip("/") + MP_ENDPOINT

    resp = requests.post(
        url,
        json=payload,
        auth=(MP_USER, MP_PASSWORD),
        headers={"Content-Type": "application/json"}
    )

    print("MerchantPro status:", resp.status_code)
    print("MerchantPro response:", resp.text)

    if resp.status_code >= 400:
        return jsonify({"error": "MerchantPro rejected request", "mp": resp.text}), 400

    return jsonify({"status": "done"}), 200


if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
