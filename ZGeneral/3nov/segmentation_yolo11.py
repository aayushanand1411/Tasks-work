import cv2
import os
from ultralytics import YOLO  # <-- use the official ultralytics API

# ---------------- CONFIG ----------------
rgb_folder = "./rgb_images"         # RGB images folder
label_folder = "./labels"           # YOLO labels folder (optional for overlay)
output_folder = "./segmentation_results"  # Where to save the segmented images
yolo_weights = "./yolo11n-seg.pt"   # Path to your YOLOv11 segmentation weights
conf_threshold = 0.25               # Confidence threshold
iou_threshold = 0.45                # NMS IoU threshold
# ---------------------------------------

os.makedirs(output_folder, exist_ok=True)

# Load YOLOv11 segmentation model
model = YOLO(yolo_weights)

# Process all images
for img_name in os.listdir(rgb_folder):
    if not img_name.lower().endswith((".png", ".jpg", ".jpeg")):
        continue

    img_path = os.path.join(rgb_folder, img_name)
    img = cv2.imread(img_path)

    # Run inference
    results = model(img, conf=conf_threshold, iou=iou_threshold)  # ultralytics API supports direct conf/iou

    # Draw segmentation masks
    if hasattr(results[0], 'masks') and results[0].masks is not None:
        masks = results[0].masks
        for mask in masks.data:  # masks.data contains binary mask arrays
            mask = mask.cpu().numpy().astype('uint8') * 255
            colored_mask = cv2.merge([mask, mask, mask])  # convert to 3 channels
            img = cv2.addWeighted(img, 1, colored_mask, 0.5, 0)  # overlay mask

    # Draw bounding boxes
    for result in results:
        boxes = result.boxes.xyxy.cpu().numpy()  # x1, y1, x2, y2
        scores = result.boxes.conf.cpu().numpy()
        classes = result.boxes.cls.cpu().numpy()
        for box, conf, cls in zip(boxes, scores, classes):
            x1, y1, x2, y2 = map(int, box)
            label = f"{int(cls)} {conf:.2f}"
            cv2.rectangle(img, (x1, y1), (x2, y2), (0, 0, 255), 2)
            cv2.putText(img, label, (x1, y1 - 5), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 1)

    # Save output
    output_path = os.path.join(output_folder, img_name)
    cv2.imwrite(output_path, img)
    print(f"Processed: {img_name}")

print("Segmentation done!")
