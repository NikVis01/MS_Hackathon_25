"""
YAMNet-based audio classification detector.
Uses TensorFlow Hub YAMNet model for audio event detection.
"""
import tensorflow as tf
import tensorflow_hub as hub
import numpy as np
import librosa
import json
import os
from typing import List, Dict, Optional
import soundfile as sf
import io
import requests
from urllib.parse import urlparse

# YAMNet model URL from TensorFlow Hub
YAMNET_MODEL_URL = 'https://tfhub.dev/google/yamnet/1'

class YAMNetDetector:
    def __init__(self, yamnet_categories_path: str = "yamnet_categories.json"):
        """
        Initialize YAMNet detector.
        Args:
            yamnet_categories_path: Path to JSON file containing YAMNet category names to filter
        """
        print("Loading YAMNet model from TensorFlow Hub...")
        self.model = hub.load(YAMNET_MODEL_URL)
        print("YAMNet model loaded successfully!")
        
        # Load YAMNet class names
        class_map_path = self.model.class_map_path().numpy().decode('utf-8')
        class_names_path = tf.keras.utils.get_file(
            'yamnet_class_map.csv',
            'https://raw.githubusercontent.com/tensorflow/models/master/research/audioset/yamnet/yamnet_class_map.csv'
        )
        
        # Read class names
        self.class_names = {}
        with open(class_names_path, 'r') as f:
            for line in f:
                parts = line.strip().split(',')
                if len(parts) >= 2:
                    idx = int(parts[0])
                    name = parts[1].strip('"')
                    self.class_names[idx] = name
        
        # Load filtered categories if provided
        self.filter_categories = None
        if yamnet_categories_path and os.path.exists(yamnet_categories_path):
            with open(yamnet_categories_path, 'r') as f:
                self.filter_categories = json.load(f)
            print(f"Filtering for categories: {self.filter_categories}")
        
        # YAMNet expects 16kHz sample rate
        self.sample_rate = 16000
    
    def preprocess_audio(self, audio_source: str) -> np.ndarray:
        """
        Preprocess audio from file or URL for YAMNet.
        Args:
            audio_source: Path to audio file or URL
        Returns:
            Audio waveform as numpy array (16kHz, mono)
        """
        # Check if the source is a URL
        if urlparse(audio_source).scheme in ('http', 'https'):
            response = requests.get(audio_source, stream=True)
            response.raise_for_status()
            audio_data = io.BytesIO(response.content)
            waveform, sr = sf.read(audio_data)
        else:
            # Load from local file
            waveform, sr = librosa.load(audio_source, sr=None)
        
        # Convert to mono if stereo
        if len(waveform.shape) > 1:
            waveform = librosa.to_mono(waveform)
        
        # Resample to 16kHz (YAMNet requirement)
        if sr != self.sample_rate:
            waveform = librosa.resample(waveform, orig_sr=sr, target_sr=self.sample_rate)
        
        return waveform.astype(np.float32)
    
    def detect_sounds(self, audio_source: str, threshold: float = 0.3, top_k: int = 10) -> List[Dict]:
        """
        Detect sounds using YAMNet.
        Args:
            audio_source: Path to audio file or URL
            threshold: Minimum probability threshold (0-1)
            top_k: Maximum number of results to return
        Returns:
            List of detected sounds with probabilities
        """
        # Preprocess audio
        waveform = self.preprocess_audio(audio_source)
        
        # Run YAMNet inference
        scores, embeddings, spectrogram = self.model(waveform)
        
        # Get top predictions
        scores_mean = np.mean(scores, axis=0)
        top_indices = np.argsort(scores_mean)[::-1][:top_k]
        
        results = []
        for idx in top_indices:
            prob = float(scores_mean[idx])
            class_name = self.class_names.get(idx, f"Unknown_{idx}")
            
            # Filter by threshold
            if prob < threshold:
                continue
            
            # Filter by category list if provided
            if self.filter_categories:
                # Check if this class name matches any of our filter categories
                # YAMNet class names are like "Glass, Glass" or "Crash" etc.
                matches_filter = any(
                    filter_cat.lower() in class_name.lower() 
                    or class_name.lower() in filter_cat.lower()
                    for filter_cat in self.filter_categories
                )
                if not matches_filter:
                    continue
            
            results.append({
                'class': class_name,
                'probability': prob,
                'class_index': int(idx)
            })
        
        return sorted(results, key=lambda x: x['probability'], reverse=True)
    
    def detect_sounds_from_stream(self, audio_stream: np.ndarray, threshold: float = 0.3, top_k: int = 10, input_sr: int = None) -> List[Dict]:
        """
        Detect sounds from audio stream data.
        Args:
            audio_stream: Numpy array containing audio data
            threshold: Minimum probability threshold
            top_k: Maximum number of results
            input_sr: Input sample rate (if None, assumes 16kHz)
        Returns:
            List of detected sounds
        """
        # Ensure mono
        if len(audio_stream.shape) > 1:
            audio_stream = librosa.to_mono(audio_stream)
        
        # Resample to 16kHz if needed (YAMNet requirement)
        if input_sr and input_sr != self.sample_rate:
            waveform = librosa.resample(
                audio_stream.astype(np.float32),
                orig_sr=input_sr,
                target_sr=self.sample_rate
            )
        else:
            waveform = audio_stream.astype(np.float32)
        
        # Run YAMNet
        scores, embeddings, spectrogram = self.model(waveform)
        
        # Process results
        scores_mean = np.mean(scores, axis=0)
        top_indices = np.argsort(scores_mean)[::-1][:top_k]
        
        results = []
        for idx in top_indices:
            prob = float(scores_mean[idx])
            if prob < threshold:
                continue
            
            class_name = self.class_names.get(idx, f"Unknown_{idx}")
            
            # Filter by category list if provided
            if self.filter_categories:
                matches_filter = any(
                    filter_cat.lower() in class_name.lower() 
                    or class_name.lower() in filter_cat.lower()
                    for filter_cat in self.filter_categories
                )
                if not matches_filter:
                    continue
            
            results.append({
                'class': class_name,
                'probability': prob,
                'class_index': int(idx)
            })
        
        return sorted(results, key=lambda x: x['probability'], reverse=True)

