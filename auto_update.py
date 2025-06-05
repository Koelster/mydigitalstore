import os
import json
from PIL import Image, ImageDraw, ImageFont
from slugify import slugify
from datetime import datetime

# === CONFIGURATION ===
PRODUCTS_DIR = 'static/images/products'
THUMBNAILS_DIR = 'static/images/thumbnails'
PREVIEW_DIR = 'static/images/previews'
OUTPUT_JSON = 'products.json'
THUMBNAIL_SIZE = (300, 300)
PREVIEW_SIZE = (600, 600)
SUPPORTED_EXTS = ['.png', '.jpg', '.jpeg', '.webp']
WATERMARK_TEXT = "MyDigitalStore Preview"

# === PRICING ===
ZAR_PRICE = 25.00        # R25 for display
USD_PRICE = 1.40         # $1.40 for PayFast

# === HELPER FUNCTIONS ===
def create_thumbnail(src, dest):
    try:
        img = Image.open(src)
        img.thumbnail(THUMBNAIL_SIZE)
        os.makedirs(os.path.dirname(dest), exist_ok=True)
        img.save(dest)
    except Exception as e:
        print(f"[❌] Failed thumbnail for {src}: {e}")

def create_preview_with_watermark(src, dest):
    try:
        img = Image.open(src).convert("RGBA")
        img.thumbnail(PREVIEW_SIZE)

        watermark_layer = Image.new("RGBA", img.size, (255, 255, 255, 0))
        draw = ImageDraw.Draw(watermark_layer)

        font_path = "arial.ttf"
        try:
            font = ImageFont.truetype(font_path, 22)
        except:
            font = ImageFont.load_default()

        # Get size of watermark text
        bbox = draw.textbbox((0, 0), WATERMARK_TEXT, font=font)
        text_w = bbox[2] - bbox[0]
        text_h = bbox[3] - bbox[1]

        # Tile the watermark diagonally
        for y in range(0, img.height, text_h + 80):
            for x in range(0, img.width, text_w + 80):
                draw.text((x, y), WATERMARK_TEXT, font=font, fill=(255, 255, 255, 120))

        watermarked = Image.alpha_composite(img, watermark_layer)

        os.makedirs(os.path.dirname(dest), exist_ok=True)
        watermarked.save(dest, format="PNG")  # Preserve transparency
    except Exception as e:
        print(f"[❌] Failed preview for {src}: {e}")

# === MAIN SCRIPT ===
products = []

for category in os.listdir(PRODUCTS_DIR):
    cat_path = os.path.join(PRODUCTS_DIR, category)
    if not os.path.isdir(cat_path):
        continue

    for file in os.listdir(cat_path):
        name, ext = os.path.splitext(file)
        if ext.lower() not in SUPPORTED_EXTS:
            continue

        product_path = os.path.join(cat_path, file)
        thumbnail_path = os.path.join(THUMBNAILS_DIR, file)
        preview_path = os.path.join(PREVIEW_DIR, file)

        create_thumbnail(product_path, thumbnail_path)
        create_preview_with_watermark(product_path, preview_path)

        slug = slugify(name)
        clean_name = name.replace("-", " ").replace("_", " ").title()
        lower_category = category.lower()

        product = {
            "name": clean_name,
            "slug": slug,
            "filename": file,
            "category": lower_category,
            "tags": [lower_category, "print", "digital", "design"],
            "license": "Personal & Commercial Use",
            "date_added": datetime.now().strftime("%Y-%m-%d"),
            "meta_title": f"{clean_name} | MyDigitalStore",
            "meta_desc": f"Download {clean_name} - perfect for mugs, t-shirts, and sublimation designs.",
            "download": f"{category}/{file}",
            "price": round(USD_PRICE, 2),
            "price_zar": round(ZAR_PRICE, 2)
        }
        products.append(product)

# Write to JSON
with open(OUTPUT_JSON, "w", encoding="utf-8") as f:
    json.dump(products, f, indent=2, ensure_ascii=False)

print(f"✅ Created {len(products)} products with previews and thumbnails in {OUTPUT_JSON}")
