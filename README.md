### 2025 Microsoft AI Agent Hackathon

# Set up environment:
- Let's all use uv for packages and environment (make sure you have uv installed)
- Set up a uv venv in ur local repo
- Install requirements.txt with uv (uv pip install...)

# Preliminary code structure:
- Main.py will contain the app itself as well as entrypoint, so either web or locally running using openCV
- Infer.py will most likely run some YOLO model for image classification and bounding boxes
- Predictor.py will run the NN for movement prediction. Draws arrows for predicted direction, etc... 