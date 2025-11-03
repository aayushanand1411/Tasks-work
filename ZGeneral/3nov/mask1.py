import cv2
import os
import numpy as np

# ---------------- CONFIGURATION ----------------
input_folder = "./Images_samples"    # Folder with grayscale images
output_image_folder = "./rgb_images"   # Folder to save converted RGB images
output_label_folder = "./labels"       # Folder to save YOLO segmentation txt labels
threshold_value = 200                # Threshold for binary mask (adjust if needed)
approx_epsilon = 1.0                 # Polygon approximation accuracy
# ------------------------------------------------

# Create output folders if they don't exist
os.makedirs(output_image_folder, exist_ok=True)
os.makedirs(output_label_folder, exist_ok=True)

# Process all images
for filename in os.listdir(input_folder):
    if not filename.lower().endswith((".png", ".jpg", ".jpeg")):
        continue

    # Read grayscale image
    img_path = os.path.join(input_folder, filename)
    img_gray = cv2.imread(img_path, cv2.IMREAD_GRAYSCALE)
    height, width = img_gray.shape

    # Convert grayscale to RGB for YOLO input
    img_rgb = cv2.cvtColor(img_gray, cv2.COLOR_GRAY2RGB)
    output_img_path = os.path.join(output_image_folder, filename)
    cv2.imwrite(output_img_path, img_rgb)

    # Create binary mask (0=background, 255=object)
    _, mask = cv2.threshold(img_gray, threshold_value, 255, cv2.THRESH_BINARY)

    # Find contours (objects) in the mask
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    yolo_lines = []

    for contour in contours:
        # Simplify polygon for YOLO
        contour = cv2.approxPolyDP(contour, approx_epsilon, True)
        coords = []
        for point in contour:
            x, y = point[0]
            coords.append(str(x / width))   # normalize x
            coords.append(str(y / height))  # normalize y
        # Single class = 0
        line = "0 " + " ".join(coords)
        yolo_lines.append(line)

    # Save YOLO segmentation label
    label_filename = os.path.splitext(filename)[0] + ".txt"
    output_label_path = os.path.join(output_label_folder, label_filename)
    with open(output_label_path, "w") as f:
        for line in yolo_lines:
            f.write(line + "\n")

    print(f"Processed {filename}: {len(contours)} object(s) detected.")
