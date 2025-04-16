### YOLO for establishing bounding boxes and identifying humans

import cv2
import numpy as np # For preprocessing
from ultralytics import YOLO

model = YOLO("yolov8n.pt") # Loading model
