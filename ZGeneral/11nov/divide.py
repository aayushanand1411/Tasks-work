import os
import random
import shutil

# ---------------- CONFIGURATION ----------------
rgb_folder = r"D:\Virtual_Environment_11\segmentation_lables\rgb_images"
label_folder = r"D:\Virtual_Environment_11\segmentation_lables\seg_labels"
output_base = r"D:\Virtual_Environment_11\segmentation_lables\data_split"

train_ratio = 0.75
val_ratio = 0.23
test_ratio = 0.02
# ------------------------------------------------

# Create output directories
splits = {
    "train": ("train", "train_labels"),
    "val": ("val", "val_labels"),
    "test": ("test", "test_labels")
}

for img_dir, lbl_dir in splits.values():
    os.makedirs(os.path.join(output_base, img_dir), exist_ok=True)
    os.makedirs(os.path.join(output_base, lbl_dir), exist_ok=True)

# Collect all image files
images = [f for f in os.listdir(rgb_folder) if f.lower().endswith((".png", ".jpg", ".jpeg"))]
random.shuffle(images)

total = len(images)
train_count = int(total * train_ratio)
val_count = int(total * val_ratio)
test_count = total - train_count - val_count

train_files = images[:train_count]
val_files = images[train_count:train_count + val_count]
test_files = images[train_count + val_count:]

print(f"Total images: {total}")
print(f"Train: {len(train_files)}, Val: {len(val_files)}, Test: {len(test_files)}")

# Helper function
def copy_pair(img_name, split_type):
    base_name = os.path.splitext(img_name)[0]
    img_src = os.path.join(rgb_folder, img_name)
    lbl_src = os.path.join(label_folder, base_name + ".txt")

    img_dst = os.path.join(output_base, splits[split_type][0], img_name)
    lbl_dst = os.path.join(output_base, splits[split_type][1], base_name + ".txt")

    # Copy image
    shutil.copy2(img_src, img_dst)

    # Copy label if exists
    if os.path.exists(lbl_src):
        shutil.copy2(lbl_src, lbl_dst)
    else:
        print(f"⚠️ Warning: No label found for {img_name}")

# Copy to respective folders
for file in train_files:
    copy_pair(file, "train")

for file in val_files:
    copy_pair(file, "val")

for file in test_files:
    copy_pair(file, "test")

print("✅ Dataset split completed successfully.")
