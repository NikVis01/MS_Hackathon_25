"""
Test script demonstrating YAMNet integration.
Run this to verify YAMNet is working correctly.

Usage:
    python test_yamnet_integration.py [audio_file.wav]
    
If no audio file is provided, it will just test initialization.
"""
from sound_detector import SoundDetector
import json
import sys
import numpy as np
import soundfile as sf
import os

def test_yamnet_initialization():
    """Test that YAMNet can be initialized correctly."""
    print("=" * 60)
    print("Testing YAMNet Integration")
    print("=" * 60)
    
    # Initialize detector with YAMNet
    print("\n1. Initializing SoundDetector with YAMNet...")
    try:
        detector = SoundDetector(use_yamnet=True, yamnet_categories_path="yamnet_categories.json")
        print("   ✓ YAMNet detector initialized successfully!")
    except Exception as e:
        print(f"   ✗ Failed to initialize YAMNet: {e}")
        return None
    
    # Load categories to show what we're filtering for
    print("\n2. Checking YAMNet categories filter:")
    try:
        with open("yamnet_categories.json", 'r') as f:
            categories = json.load(f)
        print(f"   ✓ Loaded categories: {categories}")
    except FileNotFoundError:
        print("   ⚠ Warning: yamnet_categories.json not found. Using all YAMNet categories.")
    
    return detector

def test_yamnet_with_audio(detector, audio_file):
    """Test YAMNet detection with an actual audio file."""
    print(f"\n3. Testing audio detection on: {audio_file}")
    
    if not os.path.exists(audio_file):
        print(f"   ✗ Audio file not found: {audio_file}")
        return
    
    try:
        # Run detection
        results = detector.detect_sounds(audio_file, threshold=0.3)
        
        if results:
            print(f"   ✓ Detected {len(results)} sound(s):")
            for i, result in enumerate(results[:5], 1):  # Show top 5
                print(f"      {i}. {result['class']}: {result['probability']:.3f}")
        else:
            print("   ⚠ No sounds detected above threshold (0.3)")
            print("   Try lowering the threshold or checking if categories match the audio")
        
    except Exception as e:
        print(f"   ✗ Detection failed: {e}")
        import traceback
        traceback.print_exc()

def test_yamnet_with_synthetic_audio(detector):
    """Test YAMNet with synthetic audio (sine wave)."""
    print("\n3. Testing with synthetic audio (sine wave)...")
    
    try:
        # Generate a simple sine wave (1 second, 16kHz)
        sample_rate = 16000
        duration = 1.0
        frequency = 440  # A4 note
        t = np.linspace(0, duration, int(sample_rate * duration))
        audio_data = np.sin(2 * np.pi * frequency * t).astype(np.float32)
        
        # Run detection
        results = detector.detect_sounds_from_stream(audio_data, threshold=0.1)
        
        if results:
            print(f"   ✓ Detected {len(results)} sound(s) in synthetic audio:")
            for i, result in enumerate(results[:3], 1):
                print(f"      {i}. {result['class']}: {result['probability']:.3f}")
        else:
            print("   ⚠ No sounds detected (this is normal for a simple sine wave)")
            
    except Exception as e:
        print(f"   ✗ Synthetic audio test failed: {e}")

def main():
    """Main test function."""
    # Test initialization
    detector = test_yamnet_initialization()
    
    if detector is None:
        print("\n" + "=" * 60)
        print("Test failed at initialization stage.")
        print("=" * 60)
        return
    
    # Test with audio file if provided
    if len(sys.argv) > 1:
        audio_file = sys.argv[1]
        test_yamnet_with_audio(detector, audio_file)
    else:
        # Test with synthetic audio
        test_yamnet_with_synthetic_audio(detector)
        print("\n   Tip: Provide an audio file to test with real audio:")
        print("   python test_yamnet_integration.py path/to/audio.wav")
    
    print("\n" + "=" * 60)
    print("YAMNet integration test complete!")
    print("=" * 60)
    print("\nUsage examples:")
    print("  # Initialize detector")
    print("  detector = SoundDetector(use_yamnet=True)")
    print("  ")
    print("  # Detect sounds in audio file")
    print("  results = detector.detect_sounds('audio.wav')")
    print("  ")
    print("  # Detect sounds from audio stream (numpy array)")
    print("  results = detector.detect_sounds_from_stream(audio_array)")

if __name__ == "__main__":
    main()

