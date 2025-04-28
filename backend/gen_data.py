### File for generating synthetic training data for the predictor model

import numpy as np

"""
Issue: No data for jaywalking across a crosswalk, particularly from the angle we want

Solution: Generate synthetic data based off of 2 labels for motion paths on approach to the crosswalk based off of following parameters:

1. Slow
Avg speed: Low (defined within interval as in spd > x)
Deceleration: Low 
(maybe) Stopping distance from curb: High 

2. Rushed 
Avg speed: High (defined within interval as in spd > x)
Deceleration: High 
(maybe) Stopping distance from curb: Low 

Speed and deceleration tracked frame by frame with openCV and output from YOLO
"""