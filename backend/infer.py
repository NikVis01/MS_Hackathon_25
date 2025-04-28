### YOLO for establishing bounding boxes and identifying humans

import cv2
import numpy as np # For preprocessing
from ultralytics import YOLO
from typing import List, Dict, Any
import base64
from io import BytesIO
from PIL import Image

class YOLODetector:
    def __init__(self, model_path: str = "yolov8n.pt"):
        self.model = YOLO(model_path)
        
    def process_image(self, image_data: str) -> Dict[str, Any]:
        """
        Process an image and return detection results
        Args:
            image_data: Base64 encoded image string
        Returns:
            Dictionary containing detection results
        """
        try:
            # Decode base64 image
            image_bytes = base64.b64decode(image_data)
            image = Image.open(BytesIO(image_bytes))
            image_np = np.array(image)
            
            # Run YOLO detection
            results = self.model(image_np)
            
            # Process results
            detections = []
            for result in results:
                boxes = result.boxes
                for box in boxes:
                    x1, y1, x2, y2 = box.xyxy[0].tolist()
                    confidence = box.conf[0].item()
                    class_id = box.cls[0].item()
                    class_name = self.model.names[int(class_id)]
                    
                    detections.append({
                        "bbox": [x1, y1, x2, y2],
                        "confidence": confidence,
                        "class": class_name,
                        "class_id": int(class_id)
                    })
            
            return {
                "success": True,
                "detections": detections
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

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

            # Run YOLO detection
            results = self.model(frame)
            for result in results:
                boxes = result.boxes
                for box in boxes:
                    x1, y1, x2, y2 = map(int, box.xyxy[0])
                    confidence = box.conf[0].item()
                    class_id = int(box.cls[0].item())
                    class_name = self.model.names[class_id]
                    label = f"{class_name} {confidence:.2f}"
                    cv2.rectangle(frame, (x1, y1), (x2, y2), (0,255,0), 2)
                    cv2.putText(frame, label, (x1, y1-10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0,255,0), 2)

            cv2.imshow('YOLO Camera', frame)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

        cap.release()
        cv2.destroyAllWindows()
