import cv2
import os
import numpy as np

# ---------------- CONFIG ----------------
rgb_folder = r"D:\Virtual_Environment_11\segmentation_lables\rgb_images"
label_folder = r"D:\Virtual_Environment_11\segmentation_lables\seg_labels"
output_folder = r"D:\Virtual_Environment_11\segmentation_lables\segmentation_results2"
mask_folder = r"D:\Virtual_Environment_11\segmentation_lables\segmentation_masks"   # optional: save separate masks
# ---------------------------------------

os.makedirs(output_folder, exist_ok=True)
os.makedirs(mask_folder, exist_ok=True)

# Process each image
for img_name in os.listdir(rgb_folder):
    if not img_name.lower().endswith((".png", ".jpg", ".jpeg")):
        continue

    # Load image
    img_path = os.path.join(rgb_folder, img_name)
    img = cv2.imread(img_path)
    height, width = img.shape[:2]

    # Create a blank mask
    mask_img = np.zeros((height, width), dtype=np.uint8)

    # Load corresponding label file
    label_path = os.path.join(label_folder, os.path.splitext(img_name)[0] + ".txt")
    if os.path.exists(label_path):
        with open(label_path, "r") as f:
            lines = f.readlines()
        for line in lines:
            parts = line.strip().split()
            if len(parts) < 3:
                continue
            class_id = int(parts[0])
            coords = np.array([float(x) for x in parts[1:]]).reshape(-1, 2)
            # Convert normalized coords to pixels
            coords[:, 0] *= width
            coords[:, 1] *= height
            coords_int = np.round(coords).astype(np.int32)
            # Draw filled polygon on mask
            cv2.fillPoly(mask_img, [coords_int], color=255)

    # Overlay mask on original image
    colored_mask = cv2.merge([mask_img, mask_img, mask_img])
    overlay = cv2.addWeighted(img, 1, colored_mask, 0.5, 0)

    # Save overlay and mask
    cv2.imwrite(os.path.join(output_folder, img_name), overlay)
    cv2.imwrite(os.path.join(mask_folder, img_name), mask_img)

    print(f"Processed {img_name}")

print("Segmentation done!")
