### YOLO for establishing bounding boxes and identifying humans

import cv2
import numpy as np # For preprocessing
from ultralytics import YOLO
from typing import List, Dict, Any
import base64
from io import BytesIO
from PIL import Image
import torch

class YOLODetector:
    def __init__(self):
        # Initialize YOLO model
        self.model = YOLO('yolov8n.pt')

        # Enable CUDA if available
        if torch.cuda.is_available():
            self.model.to('cuda')
            torch.backends.cudnn.benchmark = True
            self.model.model.half()

        self.model.model.eval()

        # Cache class names
        self.class_names = self.model.names

        # Confidence threshold
        self.conf_threshold = 0.25

        # Target classes to detect (can be None = detect all)
        self.target_classes = None

        # Warm up the model
        dummy_input = torch.zeros((1, 3, 640, 640), device='cuda' if torch.cuda.is_available() else 'cpu')
        for _ in range(3):
            self.model(dummy_input)

    def set_target_classes(self, class_list):
        """Sätt de klasser vi vill detektera, enligt användarens prompt"""
        self.target_classes = [cls.lower() for cls in class_list]

    def process_image(self, image_data):
        try:
            image_data = image_data.split(',')[1] if ',' in image_data else image_data
            image_bytes = base64.b64decode(image_data)
            image = Image.open(BytesIO(image_bytes))

            frame = np.array(image)
            if len(frame.shape) == 2:
                frame = cv2.cvtColor(frame, cv2.COLOR_GRAY2RGB)
            elif frame.shape[2] == 4:
                frame = cv2.cvtColor(frame, cv2.COLOR_RGBA2RGB)

            results = self.model(frame, conf=self.conf_threshold, verbose=False)

            detections = []
            for result in results:
                boxes = result.boxes
                for box in boxes:
                    x1, y1, x2, y2 = map(int, box.xyxy[0].tolist())
                    confidence = float(box.conf[0].item())
                    class_id = int(box.cls[0].item())
                    class_name = self.class_names[class_id]

                    # Filtrera ut oönskade klasser
                    if self.target_classes and class_name.lower() not in self.target_classes:
                        continue

                    detections.append({
                        "bbox": [x1, y1, x2, y2],
                        "confidence": confidence,
                        "class": class_name,
                        "class_id": class_id
                    })

            return {"success": True, "detections": detections}

        except Exception as e:
            return {"success": False, "error": str(e)}

    def detect_from_camera(self):
        import cv2
        cap = cv2.VideoCapture(0)
        if not cap.isOpened():
            print("Cannot open camera")
            return

        while True:
            ret, frame = cap.read()
            if not ret:
                print("Can't receive frame (stream end?). Exiting ...")
                break

            results = self.model(frame, conf=self.conf_threshold, verbose=False)
            for result in results:
                boxes = result.boxes
                for box in boxes:
                    x1, y1, x2, y2 = map(int, box.xyxy[0])
                    confidence = float(box.conf[0].item())
                    class_id = int(box.cls[0].item())
                    class_name = self.class_names[class_id]

                    # Filtrera ut oönskade klasser även i livekamera
                    if self.target_classes and class_name.lower() not in self.target_classes:
                        continue

                    label = f"{class_name} {confidence:.2f}"
                    cv2.rectangle(frame, (x1, y1), (x2, y2), (0,255,0), 2)
                    cv2.putText(frame, label, (x1, y1-10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0,255,0), 2)

            cv2.imshow('YOLO Camera', frame)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

        cap.release()
        cv2.destroyAllWindows()