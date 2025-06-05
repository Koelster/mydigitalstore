import os
import json
from datetime import datetime, timedelta

# Define paths
base_dir = "/mnt/data"
images_dir = os.path.join(base_dir, "images", "products")
json_path = os.path.join(base_dir, "products.json")

# Create directory if missing
os.makedirs(images_dir, exist_ok=True)

# Collect valid image files
image_files = [
    f for f in os.listdir(images_dir)
    if f.lower().endswith(".png") and os.path.isfile(os.path.join(images_dir, f))
]

# Setup data list
products = []
new_cutoff = datetime.now() - timedelta(days=7)

# Rename files and collect metadata
for old_name in image_files:
    name_wo_ext = os.path.splitext(old_name)[0]
    clean_name = name_wo_ext.lower().replace(" ", "-")
    new_name = f"{clean_name}.png"

    old_path = os.path.join(images_dir, old_name)
    new_path = os.path.join(images_dir, new_name)

    # Rename file if needed
    if old_name != new_name:
        os.rename(old_path, new_path)

    # Set 'new' flag based on creation time
    creation_time = datetime.fromtimestamp(os.path.getctime(new_path))
    is_new = creation_time > new_cutoff

    # Build product entry
    products.append({
        "title": name_wo_ext.replace("-", " ").title(),
        "filename": new_name,
        "category": "quotes",  # Default category; can be edited later
        "new": is_new
    })

# Save to products.json
with open(json_path, "w", encoding="utf-8") as f:
    json.dump(products, f, indent=2, ensure_ascii=False)

json_path  # Return path for confirmation
