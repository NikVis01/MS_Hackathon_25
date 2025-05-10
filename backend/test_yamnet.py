import time
from sound_detector import SoundDetector

def main():
    print("Initializing sound detector...")

    try:
        # Initialize the SoundDetector object
        detector = SoundDetector()
        print("Sound detector initialized successfully!")

        # Start continuous detection
        detector.start_detection()

        print("Press Ctrl+C to stop...")
        while True:
            time.sleep(1)  # Keeps the main thread alive until interrupted

    except KeyboardInterrupt:
        print("\nStopping sound detection...")
        detector.stop_detection()  # Stop the continuous detection properly

    except Exception as e:
        print(f"An error occurred: {e}")
        detector.stop_detection()

if __name__ == "__main__":
    main()
