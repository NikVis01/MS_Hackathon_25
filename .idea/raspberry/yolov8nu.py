import cv2
from ultralytics import YOLO

# --- Setup YOLO
model = YOLO('yolov8n.pt')  # You can choose: n (nano), s (small), m (medium), l (large), x (extra large)
#model.to('cuda')  # Use GPU if available

# --- Setup OpenCV
#cv2.setNumThreads(4)  # You can adjust depending on your CPU
#cv2.setUseOptimized(True)

# --- Connect to Pi Camera
raspberry_pi_ip = '10.42.0.1'  # your Pi IP address
cap = cv2.VideoCapture(f'tcp://{raspberry_pi_ip}:8000')

if not cap.isOpened():
    raise IOError("Cannot open Raspberry Pi camera stream")

while True:
    ret, frame = cap.read()
    if not ret:
        break

    results = model.predict(frame, stream=True)  # Predict faster with half precision

    for result in results:
        boxes = result.boxes.xyxy.cpu().numpy()
        class_ids = result.boxes.cls.cpu().numpy().astype(int)
        confidences = result.boxes.conf.cpu().numpy()

        for i in range(len(boxes)):
            box = boxes[i]
            class_id = class_ids[i]
            confidence = confidences[i]

            class_name = model.names[class_id]

            allowed_classes = ['person', 'cell phone']
            if class_name not in allowed_classes:
                continue

            x1, y1, x2, y2 = map(int, box)

            color = (0, 255, 0)
            if class_name == 'person':
                color = (255, 0, 0)
            elif class_name == 'cell phone':
                color = (0, 0, 255)

            cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)

            label = f"{class_name} {confidence:.2f}"
            text_x = x1
            text_y = y1 - 10 if y1 > 10 else y1 + 15
            cv2.putText(frame, label, (text_x, text_y), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)

    cv2.imshow('YOLOv8 Detection from Pi Camera', frame)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
