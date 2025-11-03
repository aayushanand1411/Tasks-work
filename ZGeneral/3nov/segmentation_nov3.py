import cv2
import os
import numpy as np
import glob

# ---------------- CONFIGURATION ----------------
input_image_folder = r"D:\Virtual_Environment_11\segmentation_lables\Images_samples"           # Folder with grayscale images
input_label_folder = r"D:\Virtual_Environment_11\segmentation_lables\bbox_labels"      # Folder with YOLO bounding box labels
output_image_folder = r"D:\Virtual_Environment_11\segmentation_lables\rgb_images"      # Folder to save RGB images
output_seg_folder = r"D:\Virtual_Environment_11\segmentation_lables\seg_labels"        # Folder to save segmentation labels
threshold_value = 200                     # Threshold for segmentation mask
approx_epsilon = 1.0                      # Polygon approximation accuracy
# ------------------------------------------------

os.makedirs(output_image_folder, exist_ok=True)
os.makedirs(output_seg_folder, exist_ok=True)

# Helper function to get last 5 digits from a filename (to match image and label)
def get_key(name):
    base = os.path.splitext(os.path.basename(name))[0]
    return base[-5:]

# Create mapping of label files
label_map = {get_key(lbl): lbl for lbl in glob.glob(os.path.join(input_label_folder, "*.txt"))}

# Iterate through all images
for img_file in os.listdir(input_image_folder):
    if not img_file.lower().endswith((".png", ".jpg", ".jpeg")):
        continue

    key = get_key(img_file)
    if key not in label_map:
        print(f"No matching label found for {img_file}, skipping.")
        continue

    img_path = os.path.join(input_image_folder, img_file)
    img_gray = cv2.imread(img_path, cv2.IMREAD_GRAYSCALE)
    h, w = img_gray.shape

    # Convert grayscale to RGB
    img_rgb = cv2.cvtColor(img_gray, cv2.COLOR_GRAY2RGB)
    cv2.imwrite(os.path.join(output_image_folder, img_file), img_rgb)

    # Read YOLO bbox label
    label_path = label_map[key]
    with open(label_path, "r") as f:
        lines = f.readlines()

    yolo_lines = []
    for line in lines:
        parts = line.strip().split()
        if len(parts) != 5:
            continue
        cls, x_c, y_c, bw, bh = map(float, parts)
        # Convert normalized bbox to pixel coordinates
        x_center, y_center = int(x_c * w), int(y_c * h)
        box_w, box_h = int(bw * w), int(bh * h)
        x1, y1 = max(0, x_center - box_w // 2), max(0, y_center - box_h // 2)
        x2, y2 = min(w, x_center + box_w // 2), min(h, y_center + box_h // 2)

        # Crop region inside bbox
        roi = img_gray[y1:y2, x1:x2]
        if roi.size == 0:
            continue

        # Threshold to get binary mask
        _, mask = cv2.threshold(roi, threshold_value, 255, cv2.THRESH_BINARY)

        # Find contours only within ROI
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        for contour in contours:
            contour = cv2.approxPolyDP(contour, approx_epsilon, True)
            coords = []
            for point in contour:
                px, py = point[0]
                # Shift ROI coordinates to full image coordinates
                x_norm = (x1 + px) / w
                y_norm = (y1 + py) / h
                coords.append(f"{x_norm:.6f}")
                coords.append(f"{y_norm:.6f}")
            if len(coords) >= 6:
                yolo_lines.append(f"{int(cls)} " + " ".join(coords))

    # Save YOLO segmentation labels
    if yolo_lines:
        seg_label_path = os.path.join(output_seg_folder, os.path.splitext(img_file)[0] + ".txt")
        with open(seg_label_path, "w") as f:
            for line in yolo_lines:
                f.write(line + "\n")

    print(f"Processed {img_file}: {len(yolo_lines)} object(s) segmented.")
