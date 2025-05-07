import sounddevice as sd
import numpy as np
from sound_detector import SoundDetector
import time
import json

def test_microphone():
    """Test microphone input with continuous monitoring"""
    print("\nStarting microphone test...")
    print("Speak or make sounds - Press Ctrl+C to stop")
    
    # Initialize the detector with config
    detector = SoundDetector(config_path="sound_classes.json")
    
    # Load config for display
    with open("sound_classes.json", 'r') as f:
        config = json.load(f)
    
    # Set up audio parameters from config
    sample_rate = config['model_config']['sample_rate']
    block_duration = config['model_config']['block_duration']
    
    def audio_callback(indata, frames, time, status):
        if status:
            print(f"Status: {status}")
        
        # Convert to mono if stereo
        if len(indata.shape) > 1:
            audio_data = np.mean(indata, axis=1)
        else:
            audio_data = indata.flatten()
        
        # Normalize audio data
        audio_data = audio_data / np.max(np.abs(audio_data)) if np.max(np.abs(audio_data)) > 0 else audio_data
        
        # Calculate audio level (RMS) with increased sensitivity
        audio_level = np.sqrt(np.mean(np.square(audio_data)))
        level_str = '#' * int(audio_level * 200)  # Increased multiplier for better visualization
        print(f"\rAudio Level: {level_str:<50} ({audio_level:.4f})", end='')
        
        # Detect sounds using class-specific thresholds
        results = detector.detect_sounds_from_stream(audio_data)
        
        if results:
            print("\nDetected sounds:")
            for result in results:
                print(f"- {result['class']} ({result['description']}): {result['probability']:.2f} [threshold: {result['threshold']:.2f}]")
            print("\nSpeak or make sounds - Press Ctrl+C to stop")
    
    try:
        # Get list of available audio devices
        devices = sd.query_devices()
        print("\nAvailable audio devices:")
        for i, device in enumerate(devices):
            print(f"{i}: {device['name']} (inputs: {device['max_input_channels']})")
        
        # Try to find the default input device
        default_device = sd.query_devices(kind='input')
        print(f"\nUsing input device: {default_device['name']}")
        
        # Print configuration
        print("\nSound detection configuration:")
        print(f"Sample rate: {sample_rate} Hz")
        print(f"Block duration: {block_duration} seconds")
        print("\nSound classes:")
        for cls in config['sound_classes']:
            print(f"- {cls['name']}: {cls['description']} (threshold: {cls['threshold']})")
        
        # Start recording with adjusted buffer size
        with sd.InputStream(callback=audio_callback,
                          channels=1,
                          samplerate=sample_rate,
                          blocksize=int(sample_rate * block_duration),
                          device=None):  # None means use default device
            print("\nMicrophone is now active...")
            print("Audio levels will be shown below (higher numbers mean louder sounds)")
            while True:
                sd.sleep(100)  # Shorter sleep for more responsive updates
                
    except KeyboardInterrupt:
        print("\n\nMicrophone test stopped by user")
    except Exception as e:
        print(f"\nError during recording: {str(e)}")

if __name__ == "__main__":
    test_microphone() 