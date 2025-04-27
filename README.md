### 2025 SSE Business lab x Microsoft x KTH AI Society Hackathon

## Core idea:
Cameras will stream livefeeds to a website that will sent warningsignals to the user if the cameras detect scertain movement/objects/objects moving in a scertain way according to a prompt by the user (in natural language) that will be fed into an ML. 

# Set up environment:
- Make sure you have uv installed.
- Set up a uv venv in ur local repo.
- Install the modules in requirements.txt.

# Preliminary code structure:

<div align="center">
  <div class="mermaid">
    graph TD
      YOLO --> ML --> PYTHON
      YOLO --> PYTHON
      Cams --> PYTHON
      PYTHON -- FastAPI --> JavaScript --> HTML
      JavaScript --> cssTailwind[CSS & Tailwind]
      JavaScript --> Cams
      JavaScript --> prompts --> encode --> weightsbiases[weights & biases] --> vekdat[vector data]
      weightsbiases --> output

  </div>
</div>

## Important Steps

1. Online platform with FIGMA
2. Finish RB-track
3. Connect input data, CAWS/Azure
4. Meta SAM implementation

