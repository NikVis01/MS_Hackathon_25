import torch
import torchaudio
import numpy as np
import librosa
import requests
import io
import soundfile as sf
import json
from typing import List, Dict, Tuple, Optional
from urllib.parse import urlparse
import os
from torch import nn

# Optional YAMNet import
try:
    from yamnet_detector import YAMNetDetector
    YAMNET_AVAILABLE = True
except ImportError:
    YAMNET_AVAILABLE = False
    YAMNetDetector = None

class AudioCNN(nn.Module):
    def __init__(self, num_classes=10):
        super(AudioCNN, self).__init__()
        
        # Convolutional layers
        self.conv1 = nn.Conv1d(1, 64, kernel_size=80, stride=4)
        self.bn1 = nn.BatchNorm1d(64)
        self.conv2 = nn.Conv1d(64, 128, kernel_size=3, stride=1, padding=1)
        self.bn2 = nn.BatchNorm1d(128)
        self.conv3 = nn.Conv1d(128, 256, kernel_size=3, stride=1, padding=1)
        self.bn3 = nn.BatchNorm1d(256)
        self.conv4 = nn.Conv1d(256, 512, kernel_size=3, stride=1, padding=1)
        self.bn4 = nn.BatchNorm1d(512)
        
        # Pooling and activation
        self.pool = nn.MaxPool1d(4)
        self.relu = nn.ReLU()
        self.dropout = nn.Dropout(0.5)
        
        # Global average pooling
        self.global_pool = nn.AdaptiveAvgPool1d(1)
        
        # Fully connected layer
        self.fc = nn.Linear(512, num_classes)
        
    def forward(self, x):
        # Input shape: (batch_size, time_steps)
        # Add channel dimension
        x = x.unsqueeze(1)
        
        # Convolutional blocks
        x = self.relu(self.bn1(self.conv1(x)))
        x = self.pool(x)
        x = self.relu(self.bn2(self.conv2(x)))
        x = self.pool(x)
        x = self.relu(self.bn3(self.conv3(x)))
        x = self.pool(x)
        x = self.relu(self.bn4(self.conv4(x)))
        
        # Global average pooling
        x = self.global_pool(x)
        x = x.squeeze(-1)
        
        # Fully connected layer
        x = self.dropout(x)
        x = self.fc(x)
        
        return x

class SoundDetector:
    def __init__(self, config_path: str = "sound_classes.json", model_path: str = None, vm_url: str = None, use_yamnet: bool = False, yamnet_categories_path: str = "yamnet_categories.json"):
        """
        Initialize the sound detector with an audio CNN model or YAMNet.
        Args:
            config_path: Path to the JSON configuration file (for AudioCNN)
            model_path: Path to the pretrained model weights (optional, for AudioCNN)
            vm_url: Base URL of the virtual machine hosting the audio stream
            use_yamnet: If True, use YAMNet instead of AudioCNN
            yamnet_categories_path: Path to YAMNet categories JSON file
        """
        self.use_yamnet = use_yamnet and YAMNET_AVAILABLE
        
        if self.use_yamnet:
            print("Using YAMNet for audio classification")
            self.yamnet_detector = YAMNetDetector(yamnet_categories_path=yamnet_categories_path)
            self.sample_rate = 16000  # YAMNet uses 16kHz
        else:
            if use_yamnet and not YAMNET_AVAILABLE:
                print("Warning: YAMNet requested but not available. Falling back to AudioCNN.")
            self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
            self.config = self._load_config(config_path)
            self.sample_rate = self.config['model_config']['sample_rate']
            self.model = self._load_model(model_path)
        
        self.vm_url = vm_url.rstrip('/') if vm_url else None
        
    def _load_config(self, config_path: str) -> Dict:
        """
        Load the configuration from JSON file.
        Args:
            config_path: Path to the JSON configuration file
        Returns:
            Dictionary containing the configuration
        """
        try:
            with open(config_path, 'r') as f:
                config = json.load(f)
            return config
        except Exception as e:
            raise Exception(f"Failed to load configuration: {str(e)}")
    
    def _get_class_mapping(self) -> Dict[int, Dict]:
        """
        Get the class mapping from the configuration.
        Returns:
            Dictionary mapping class indices to class information
        """
        return {int(cls['id']): cls for cls in self.config['sound_classes']}
        
    def _load_model(self, model_path: str = None) -> torch.nn.Module:
        """
        Load the audio CNN model.
        Args:
            model_path: Path to the pretrained model weights (optional)
        Returns:
            Loaded model
        """
        try:
            # Initialize the model with number of classes from config
            num_classes = len(self.config['sound_classes'])
            model = AudioCNN(num_classes=num_classes)
            
            # If a specific model path is provided, load those weights
            if model_path and os.path.exists(model_path):
                state_dict = torch.load(model_path, map_location=self.device)
                model.load_state_dict(state_dict)
            
            # Move model to device
            model = model.to(self.device)
            model.eval()  # Set to evaluation mode
            
            return model
            
        except Exception as e:
            raise Exception(f"Failed to load model: {str(e)}")
    
    def _fetch_audio_from_url(self, url: str) -> np.ndarray:
        """
        Fetch audio data from a URL.
        Args:
            url: URL to fetch audio from
        Returns:
            Audio data as numpy array
        """
        try:
            response = requests.get(url, stream=True)
            response.raise_for_status()
            
            # Read the audio data
            audio_data = io.BytesIO(response.content)
            waveform, sr = sf.read(audio_data)
            
            # Resample if necessary
            if sr != self.sample_rate:
                waveform = librosa.resample(waveform, orig_sr=sr, target_sr=self.sample_rate)
            
            return waveform
            
        except requests.exceptions.RequestException as e:
            raise Exception(f"Failed to fetch audio from URL: {str(e)}")
    
    def preprocess_audio(self, audio_source: str) -> torch.Tensor:
        """
        Preprocess audio from a file or URL.
        Args:
            audio_source: Path to audio file or URL
        Returns:
            Preprocessed audio tensor
        """
        # Check if the source is a URL
        if urlparse(audio_source).scheme in ('http', 'https'):
            waveform = self._fetch_audio_from_url(audio_source)
        else:
            # Load from local file
            waveform, sr = librosa.load(audio_source, sr=self.sample_rate)
        
        # Convert to mono if stereo
        if len(waveform.shape) > 1:
            waveform = librosa.to_mono(waveform)
        
        # Convert to tensor
        waveform = torch.from_numpy(waveform).float()
        
        # Add batch dimension
        waveform = waveform.unsqueeze(0)
        
        return waveform
    
    def detect_sounds(self, audio_source: str, threshold: Optional[float] = None) -> List[Dict[str, float]]:
        """
        Detect sounds in an audio file or URL.
        Args:
            audio_source: Path to audio file or URL
            threshold: Optional override for detection threshold
        Returns:
            List of detected sounds with their probabilities
        """
        if self.use_yamnet:
            # Use YAMNet
            threshold = threshold or 0.3
            yamnet_results = self.yamnet_detector.detect_sounds(audio_source, threshold=threshold)
            # Convert to consistent format
            return [
                {
                    'class': r['class'],
                    'description': r['class'],  # YAMNet doesn't have descriptions
                    'probability': r['probability'],
                    'threshold': threshold
                }
                for r in yamnet_results
            ]
        
        # Use AudioCNN (original implementation)
        # Preprocess audio
        waveform = self.preprocess_audio(audio_source)
        
        # Move to device
        waveform = waveform.to(self.device)
        
        # Get predictions
        with torch.no_grad():
            predictions = self.model(waveform)
            probabilities = torch.sigmoid(predictions)
        
        # Process predictions
        results = []
        class_mapping = self._get_class_mapping()
        
        for idx, prob in enumerate(probabilities[0]):
            # Use class-specific threshold if available, otherwise use default
            class_threshold = class_mapping[idx]['threshold'] if idx in class_mapping else self.config['model_config']['default_threshold']
            # Override with provided threshold if specified
            threshold_to_use = threshold if threshold is not None else class_threshold
            
            if prob > threshold_to_use:
                class_info = class_mapping[idx]
                results.append({
                    'class': class_info['name'],
                    'description': class_info['description'],
                    'probability': float(prob),
                    'threshold': float(threshold_to_use)
                })
        
        return results
    
    def detect_sounds_from_stream(self, audio_stream: np.ndarray, threshold: Optional[float] = None) -> List[Dict[str, float]]:
        """
        Detect sounds from a stream of audio data.
        Args:
            audio_stream: Numpy array containing audio data
            threshold: Optional override for detection threshold
        Returns:
            List of detected sounds with their probabilities
        """
        if self.use_yamnet:
            # Use YAMNet
            threshold = threshold or 0.3
            # YAMNet expects 16kHz, so if audio_stream is already resampled, pass input_sr=16000
            # Otherwise, let YAMNet handle resampling by not specifying input_sr
            yamnet_results = self.yamnet_detector.detect_sounds_from_stream(
                audio_stream, 
                threshold=threshold,
                input_sr=self.sample_rate if self.sample_rate == 16000 else None
            )
            # Convert to consistent format
            return [
                {
                    'class': r['class'],
                    'description': r['class'],
                    'probability': r['probability'],
                    'threshold': threshold
                }
                for r in yamnet_results
            ]
        
        # Use AudioCNN (original implementation)
        # Convert to tensor
        waveform = torch.from_numpy(audio_stream).float()
        waveform = waveform.unsqueeze(0)
        waveform = waveform.to(self.device)
        
        # Get predictions
        with torch.no_grad():
            predictions = self.model(waveform)
            probabilities = torch.sigmoid(predictions)
        
        # Process predictions
        results = []
        class_mapping = self._get_class_mapping()
        
        for idx, prob in enumerate(probabilities[0]):
            # Use class-specific threshold if available, otherwise use default
            class_threshold = class_mapping[idx]['threshold'] if idx in class_mapping else self.config['model_config']['default_threshold']
            # Override with provided threshold if specified
            threshold_to_use = threshold if threshold is not None else class_threshold
            
            if prob > threshold_to_use:
                class_info = class_mapping[idx]
                results.append({
                    'class': class_info['name'],
                    'description': class_info['description'],
                    'probability': float(prob),
                    'threshold': float(threshold_to_use)
                })
        
        return results

    def detect_sounds_from_vm_stream(self, endpoint: str, threshold: float = 0.5) -> List[Dict[str, float]]:
        """
        Detect sounds from a live audio stream on the virtual machine.
        Args:
            endpoint: Endpoint path on the VM (will be appended to vm_url)
            threshold: Detection threshold (0-1)
        Returns:
            List of detected sounds with their probabilities
        """
        if not self.vm_url:
            raise ValueError("VM URL not set. Initialize SoundDetector with vm_url parameter.")
        
        # Construct full URL
        url = f"{self.vm_url}/{endpoint.lstrip('/')}"
        
        # Fetch and process audio
        waveform = self._fetch_audio_from_url(url)
        
        # Convert to tensor
        waveform = torch.from_numpy(waveform).float()
        waveform = waveform.unsqueeze(0)
        waveform = waveform.to(self.device)
        
        # Get predictions
        with torch.no_grad():
            predictions = self.model(waveform)
            probabilities = torch.sigmoid(predictions)
        
        # Process predictions
        results = []
        for idx, prob in enumerate(probabilities[0]):
            if prob > threshold:
                class_name = self.class_mapping.get(idx, f"Unknown_{idx}")
                results.append({
                    "class": class_name,
                    "probability": float(prob)
                })
        
        return sorted(results, key=lambda x: x["probability"], reverse=True) 