from ultralytics import YOLO
import os

# ---------------- CONFIGURATION ----------------
data_yaml_path = r"D:\Virtual_Environment_11\segmentation_lables\data_split\data.yaml"  # Will create below
base_path = r"D:\Virtual_Environment_11\segmentation_lables\data_split"
pretrained_model = r"D:\Virtual_Environment_11\models\yolo11n-seg.pt"  # Path to YOLOv11 segmentation model
epochs = 50
patience = 20  # early stopping
img_size = 1280
batch_size = 4
# ------------------------------------------------

# Create YAML config dynamically
yaml_content = f"""
train: {os.path.join(base_path, 'train', 'images').replace('\\', '/')}
val: {os.path.join(base_path, 'val', 'images').replace('\\', '/')}
test: {os.path.join(base_path, 'test', 'images').replace('\\', '/')}

nc: 1  # number of classes
names: ['object']  # class names
"""

with open(data_yaml_path, "w") as f:
    f.write(yaml_content)

print(f"✅ data.yaml created at: {data_yaml_path}")

# ---------------- TRAINING ----------------
model = YOLO(pretrained_model)  # Load YOLO11 segmentation model

results = model.train(
    data=data_yaml_path,
    epochs=epochs,
    patience=patience,
    imgsz=img_size,
    batch=batch_size,
    save=True,
    save_period=10,       # save weights every 10 epochs
    project=os.path.join(base_path, "runs"),
    name="yolo11_seg_training",
    device=0,             # use GPU 0
    optimizer="AdamW",
    lr0=0.001,
    augment=True,
    verbose=True
)

print("✅ Training completed. Best model saved automatically.")
