import cv2
import os
import numpy as np
import glob

# ---------------- CONFIGURATION ----------------
input_image_folder = r"D:\Virtual_Environment_11\segmentation_lables\Images_samples"
input_label_folder = r"D:\Virtual_Environment_11\segmentation_lables\bbox_labels"
output_image_folder = r"D:\Virtual_Environment_11\segmentation_lables\rgb_images"        # Folder to save RGB images
output_seg_folder = r"D:\Virtual_Environment_11\segmentation_lables\seg_labels"          # Folder to save segmentation labels
incorrect_seg_folder = r"D:\Virtual_Environment_11\segmentation_lables\incorrect_cases"  # Folder for 0 or >1 segmented objects
bbox_visual_folder = r"D:\Virtual_Environment_11\segmentation_lables\bbox_visuals"       # Folder to save bbox visualizations
threshold_value = 150                     # Threshold for segmentation mask
approx_epsilon = 1.0                      # Polygon approximation accuracy
# ------------------------------------------------

# Create output folders
os.makedirs(output_image_folder, exist_ok=True)
os.makedirs(output_seg_folder, exist_ok=True)
os.makedirs(incorrect_seg_folder, exist_ok=True)
os.makedirs(bbox_visual_folder, exist_ok=True)

# Helper: Extract last 5 digits of filename to match image/label
def get_key(name):
    base = os.path.splitext(os.path.basename(name))[0]
    return base[-5:]

# Create mapping of label files
label_map = {get_key(lbl): lbl for lbl in glob.glob(os.path.join(input_label_folder, "*.txt"))}

# Process each image
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

    # Convert to RGB
    img_rgb = cv2.cvtColor(img_gray, cv2.COLOR_GRAY2RGB)

    # Read YOLO bbox label
    label_path = label_map[key]
    with open(label_path, "r") as f:
        lines = f.readlines()

    yolo_lines = []
    bbox_img = img_rgb.copy()  # For visualization

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

        # Draw bbox for visual check
        cv2.rectangle(bbox_img, (x1, y1), (x2, y2), (0, 255, 0), 2)
        cv2.putText(bbox_img, f"cls {int(cls)}", (x1, y1 - 5),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)

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

    # Save bbox visualization
    cv2.imwrite(os.path.join(bbox_visual_folder, img_file), bbox_img)

    # Save only if exactly one object segmented
    seg_count = len(yolo_lines)
    if seg_count == 1:
        # Save RGB image and segmentation label
        cv2.imwrite(os.path.join(output_image_folder, img_file), img_rgb)
        seg_label_path = os.path.join(output_seg_folder, os.path.splitext(img_file)[0] + ".txt")
        with open(seg_label_path, "w") as f:
            for line in yolo_lines:
                f.write(line + "\n")
        print(f"✅ {img_file}: 1 object segmented, saved to main folder.")
    else:
        # Save to incorrect folder
        cv2.imwrite(os.path.join(incorrect_seg_folder, img_file), img_rgb)
        print(f"⚠️ {img_file}: {seg_count} object(s) segmented, moved to incorrect folder.")
