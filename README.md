### 2025 Microsoft AI Agent Hackathon

## Core idea:
Predicts whether or not a person will jaywalk upon stopping at a crosswalk (entering the frame).
Identifies 2 cases upon stopping at a crosswalk:
1. Stop and wait for light to turn green
2. Run across upon first stopping

The predicted movement is based mainly off of approach velocity to the crosswalk
(e.g. if a person sprints toward a crosswalk, stops abruptly then they have a higher probability of continuing across)

# Set up environment:
- Let's all use uv for packages and environment (make sure you have uv installed)
- Set up a uv venv in ur local repo
- Install requirements.txt with uv (uv pip install...)

# Preliminary code structure:
- Main.py will contain the app itself as well as entrypoint, so either web or locally running using openCV
- Infer.py will most likely run some YOLO model for image classification and bounding boxes
- Predictor.py will run the NN for movement prediction. Draws arrows for predicted direction, etc...
- gen_data.py creates synthetic data for trianing predictor.py 

# Naming ideas:
- Rush detector