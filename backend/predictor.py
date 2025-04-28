### File for predicting movement

import torch
import torch.nn as nn
import torch.nn.functional as F

from torch.utils.data import TensorDataset, DataLoader


# Model itself:
class MomentumPredictor(nn.Module):
    def __init__():
        super().__init__()

    def forward(self, x):
        pass


# Training loop for model:
def train_model(epochs:50, lr=0.001, log_weights=False):
    pass

# Running the training loop:
if __name__ == "__main__":
    train_model(epochs=50, log_weights=True)