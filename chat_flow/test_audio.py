#!/usr/bin/env python3
"""
Test script to check if audio input/output is working in WSL.
"""

import numpy as np
import sounddevice as sd
import time

def test_audio():
    print("Testing audio devices...")
    
    # List available audio devices
    print("\nAvailable audio devices:")
    print(sd.query_devices())
    
    try:
        # Test audio output with a simple tone
        print("\nTesting audio output (you should hear a beep)...")
        duration = 1  # seconds
        sample_rate = 44100
        frequency = 440  # A note
        
        # Generate a sine wave
        t = np.linspace(0, duration, int(sample_rate * duration), False)
        wave = 0.3 * np.sin(2 * np.pi * frequency * t)
        
        # Play the tone
        sd.play(wave, sample_rate)
        sd.wait()  # Wait until the sound finishes playing
        print("Audio output test completed.")
        
    except Exception as e:
        print(f"Audio output test failed: {e}")
    
    try:
        # Test audio input
        print("\nTesting audio input (recording for 3 seconds)...")
        duration = 3
        sample_rate = 44100
        
        recording = sd.rec(int(duration * sample_rate), samplerate=sample_rate, channels=1)
        print("Recording... speak now!")
        sd.wait()  # Wait until recording is finished
        
        # Check if we got any audio data
        max_amplitude = np.max(np.abs(recording))
        print(f"Recording completed. Max amplitude: {max_amplitude:.4f}")
        
        if max_amplitude > 0.001:
            print("✓ Audio input appears to be working!")
        else:
            print("⚠ Audio input might not be working (very low signal)")
            
    except Exception as e:
        print(f"Audio input test failed: {e}")

if __name__ == "__main__":
    test_audio()
