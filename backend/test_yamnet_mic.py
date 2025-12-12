"""
Test YAMNet with microphone input.
Continuously monitors microphone and detects sounds using YAMNet.

Usage:
    python test_yamnet_mic.py
"""
import sounddevice as sd
import numpy as np
from sound_detector import SoundDetector
import time
import json
import librosa

def test_yamnet_microphone():
    """Test YAMNet with microphone input and continuous monitoring"""
    print("=" * 70)
    print("YAMNet Microphone Test")
    print("=" * 70)
    print("\nThis will use YAMNet to detect sounds from your microphone.")
    print("Speak, make sounds, or play audio - Press Ctrl+C to stop\n")
    
    # Initialize the detector with YAMNet
    print("Initializing YAMNet detector...")
    try:
        detector = SoundDetector(
            use_yamnet=True, 
            yamnet_categories_path="yamnet_categories.json"
        )
        print("✓ YAMNet detector initialized!\n")
    except Exception as e:
        print(f"✗ Failed to initialize YAMNet: {e}")
        import traceback
        traceback.print_exc()
        return
    
    # Load YAMNet categories to show what we're filtering for
    try:
        with open("yamnet_categories.json", 'r') as f:
            categories = json.load(f)
        print(f"Filtering for YAMNet categories: {categories}\n")
    except FileNotFoundError:
        print("⚠ Warning: yamnet_categories.json not found.")
        print("Will use all YAMNet categories (521 classes)\n")
    
    # YAMNet uses 16kHz sample rate
    sample_rate = 16000
    block_duration = 0.5  # Process 0.5 second chunks
    
    # Track last detection to avoid spam
    last_detection_time = 0
    detection_cooldown = 1.0  # Minimum seconds between detections
    
    def audio_callback(indata, frames, time_info, status):
        """Callback function for audio stream processing."""
        nonlocal last_detection_time
        
        if status:
            print(f"Audio status: {status}")
        
        # Convert to mono if stereo
        if len(indata.shape) > 1:
            audio_data = np.mean(indata, axis=1)
        else:
            audio_data = indata.flatten()
        
        # Resample to 16kHz if needed (YAMNet requirement)
        # Most microphones default to 44.1kHz or 48kHz
        current_sr = int(sd.query_devices(sd.default.device[0])['default_samplerate'])
        if current_sr != sample_rate:
            audio_data = librosa.resample(
                audio_data.astype(np.float32), 
                orig_sr=current_sr, 
                target_sr=sample_rate
            )
        
        # Normalize audio data
        if np.max(np.abs(audio_data)) > 0:
            audio_data = audio_data / np.max(np.abs(audio_data))
        
        # Calculate audio level (RMS) for visualization
        audio_level = np.sqrt(np.mean(np.square(audio_data)))
        level_str = '█' * int(audio_level * 50)  # Visual level indicator
        print(f"\rAudio Level: {level_str:<50} ({audio_level:.4f})", end='', flush=True)
        
        # Only run detection if enough time has passed (to avoid spam)
        current_time = time.time()
        if current_time - last_detection_time < detection_cooldown:
            return
        
        # Detect sounds using YAMNet
        try:
            # Audio is already resampled to 16kHz in the callback above
            results = detector.detect_sounds_from_stream(audio_data, threshold=0.3)
            
            if results:
                last_detection_time = current_time
                print("\n" + "─" * 70)
                print(f"🎵 Detected {len(results)} sound(s):")
                for i, result in enumerate(results[:5], 1):  # Show top 5
                    prob_bar = '█' * int(result['probability'] * 30)
                    print(f"   {i}. {result['class']:<40} {prob_bar} {result['probability']:.3f}")
                print("─" * 70)
                print("\r", end='', flush=True)  # Clear line for next audio level
        except Exception as e:
            print(f"\n⚠ Detection error: {e}")
    
    try:
        # Get list of available audio devices
        devices = sd.query_devices()
        print("Available audio input devices:")
        for i, device in enumerate(devices):
            if device['max_input_channels'] > 0:
                marker = " ← DEFAULT" if i == sd.default.device[0] else ""
                print(f"  {i}: {device['name']}{marker}")
        
        # Get default input device info
        default_device = sd.query_devices(kind='input')
        print(f"\nUsing input device: {default_device['name']}")
        print(f"Device sample rate: {default_device['default_samplerate']} Hz")
        print(f"YAMNet requires: {sample_rate} Hz (will resample automatically)")
        
        # Print configuration
        print(f"\nConfiguration:")
        print(f"  Sample rate: {sample_rate} Hz")
        print(f"  Block duration: {block_duration} seconds")
        print(f"  Detection threshold: 0.3")
        print(f"  Detection cooldown: {detection_cooldown} seconds")
        
        print("\n" + "=" * 70)
        print("Microphone is now active...")
        print("Make sounds or speak - detections will appear below")
        print("Press Ctrl+C to stop")
        print("=" * 70 + "\n")
        
        # Start recording
        # Note: We request the device's native sample rate, then resample in callback
        device_sr = int(default_device['default_samplerate'])
        with sd.InputStream(
            callback=audio_callback,
            channels=1,
            samplerate=device_sr,  # Use device's native rate
            blocksize=int(device_sr * block_duration),
            device=None  # Use default device
        ):
            while True:
                sd.sleep(100)  # Keep the stream alive
                
    except KeyboardInterrupt:
        print("\n\n" + "=" * 70)
        print("Microphone test stopped by user")
        print("=" * 70)
    except Exception as e:
        print(f"\n✗ Error during recording: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_yamnet_microphone()

