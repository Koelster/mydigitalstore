from flask import Flask, render_template, request, jsonify, abort, redirect, url_for, session, send_file
import json
import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import time
import uuid

app = Flask(__name__)
app.secret_key = 'replace-with-your-secret-key'  # Needed for sessions

# === CONFIG ===
PRODUCTS_FILE = 'products.json'
PAYFAST_MERCHANT_ID = '22604292'
PAYFAST_MERCHANT_KEY = 'ooocizvxbulxm'
PAYFAST_RETURN_URL = 'http://127.0.0.1:5000/payment/success'
PAYFAST_CANCEL_URL = 'http://127.0.0.1:5000/payment/cancel'
PAYFAST_NOTIFY_URL = 'http://127.0.0.1:5000/payment/notify'
USD_TO_ZAR = 18.0
TOKEN_EXPIRY_SECONDS = 3600  # 1 hour

# === TEMP DOWNLOAD TOKEN STORE ===
token_store = {}

# === Load product data ===
try:
    with open(PRODUCTS_FILE, 'r', encoding='utf-8') as f:
        products = json.load(f)
except Exception as e:
    print(f"❌ Error loading products.json: {e}")
    products = []

# === ROUTES ===

@app.route('/')
def index():
    categories = sorted(set(p['category'] for p in products if 'category' in p))
    return render_template('index.html', products=products, categories=categories)

@app.route('/products')
def product_list():
    categories = sorted(set(p['category'] for p in products if 'category' in p))
    return render_template('products.html', products=products, categories=categories)

@app.route('/product.html')
def product_detail():
    slug = request.args.get('slug')
    if not slug:
        abort(404)
    product = next((p for p in products if p['slug'] == slug), None)
    if not product:
        abort(404)
    return render_template('product.html', product=product)

@app.route('/products.json')
def get_products_json():
    return jsonify(products)

# === Payment Flow ===

@app.route('/payfast', methods=['POST'])
def payfast_payment():
    item_name = request.form.get('item_name')
    slug = request.form.get('slug')
    email = request.form.get('email')

    product = next((p for p in products if p['slug'] == slug), None)
    if not product:
        abort(404)

    session['email'] = email
    session['slug'] = slug

    usd_price = float(product['price'])
    zar_price = round(usd_price * USD_TO_ZAR, 2)

    payment_data = {
        'merchant_id': PAYFAST_MERCHANT_ID,
        'merchant_key': PAYFAST_MERCHANT_KEY,
        'return_url': PAYFAST_RETURN_URL,
        'cancel_url': PAYFAST_CANCEL_URL,
        'notify_url': PAYFAST_NOTIFY_URL,
        'amount': zar_price,
        'item_name': item_name,
        'item_description': f"Download for {item_name}",
        'custom_str1': slug
    }

    return render_template('payfast_form.html', payment=payment_data, product=product)

@app.route('/payment/success')
def payment_success():
    email = session.get('email')
    slug = session.get('slug')

    if not email or not slug:
        return "<h1>✅ Payment Successful!</h1><p>But we couldn't get your email or download link.</p>"

    product = next((p for p in products if p['slug'] == slug), None)
    if not product:
        return "<h1>✅ Payment Successful!</h1><p>Product not found.</p>"

    # Generate download token
    token = str(uuid.uuid4())
    token_store[token] = {
        'slug': slug,
        'expires': time.time() + TOKEN_EXPIRY_SECONDS
    }

    download_link = url_for('secure_download', slug=slug, token=token, _external=True)
    send_download_email(email, product['name'], download_link)

    return render_template("payment_success.html", email=email, download_link=download_link)

@app.route('/download')
def secure_download():
    slug = request.args.get('slug')
    token = request.args.get('token')

    if not slug or not token:
        return "Invalid download link.", 400

    token_data = token_store.get(token)
    if not token_data:
        return "Download link has expired or is invalid.", 403

    if time.time() > token_data['expires']:
        del token_store[token]
        return "Download link has expired.", 403

    if token_data['slug'] != slug:
        return "Invalid file access.", 403

    product = next((p for p in products if p['slug'] == slug), None)
    if not product:
        return "Product not found.", 404

    file_path = os.path.join("static", "images", "products", product["category"], product["filename"])
    return send_file(file_path, as_attachment=True)

@app.route('/payment/cancel')
def payment_cancel():
    return "<h1>❌ Payment Cancelled</h1><p>You were not charged.</p>"

@app.route('/payment/notify', methods=['POST'])
def payment_notify():
    return "OK", 200

@app.errorhandler(404)
def not_found(e):
    return render_template('404.html'), 404

# === EMAIL FUNCTION ===

def send_download_email(to_email, product_name, download_link):
    sender_email = "info@mydigitalstore.co.za"
    sender_password = "N01KnowsmyW@gw00rd@123"
    smtp_server = "s33.registerdomain.net.za"
    smtp_port = 465

    subject = f"Your download link for {product_name}"
    body = f"""
    Thank you for your purchase from MyDigitalStore!

    Your product: {product_name}
    Secure Download link (valid for 1 hour): {download_link}

    Enjoy your design!
    """

    message = MIMEMultipart()
    message["From"] = sender_email
    message["To"] = to_email
    message["Subject"] = subject
    message.attach(MIMEText(body, "plain"))

    try:
        with smtplib.SMTP_SSL(smtp_server, smtp_port) as server:
            server.login(sender_email, sender_password)
            server.send_message(message)
        print(f"✅ Email sent to {to_email}")
    except Exception as e:
        print(f"❌ Failed to send email: {e}")

# === RUN SERVER ===

if __name__ == '__main__':
    app.run(debug=True)
