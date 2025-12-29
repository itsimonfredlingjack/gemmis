"""
GEMMIS Audio Engine - Synthetic SFX and TTS
"""
import asyncio
import numpy as np
import threading
import tempfile
import os
from pathlib import Path

# Suppress pygame welcome message
os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = "hide"

try:
    import pygame
    PYGAME_AVAILABLE = True
except ImportError:
    PYGAME_AVAILABLE = False

class AudioEngine:
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(AudioEngine, cls).__new__(cls)
            cls._instance.initialized = False
        return cls._instance

    def __init__(self):
        if self.initialized:
            return
            
        if not PYGAME_AVAILABLE:
            self.enabled = False
            self.initialized = True
            return

        try:
            pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=512)
            self.enabled = True
        except Exception:
            self.enabled = False
            return

        self.sounds = {}
        self._generate_sounds()
        self.initialized = True
        self.tts_lock = asyncio.Lock()

    def _generate_sine_wave(self, freq, duration, volume=0.2):
        if not PYGAME_AVAILABLE: return None
        sample_rate = 44100
        n_samples = int(sample_rate * duration)
        t = np.linspace(0, duration, n_samples, False)
        
        # Generate wave
        wave = np.sin(2 * np.pi * freq * t)
        
        # Apply fade in/out to avoid clicking
        fade = int(0.01 * sample_rate)
        if n_samples > fade * 2:
            wave[:fade] *= np.linspace(0, 1, fade)
            wave[-fade:] *= np.linspace(1, 0, fade)
            
        # Stereo
        stereo = np.column_stack((wave, wave))
        
        # Convert to 16-bit signed integer
        audio = (stereo * volume * 32767).astype(np.int16)
        return pygame.sndarray.make_sound(audio)

    def _generate_noise(self, duration, volume=0.1):
        if not PYGAME_AVAILABLE: return None
        sample_rate = 44100
        n_samples = int(sample_rate * duration)
        
        wave = np.random.uniform(-1, 1, n_samples)
        stereo = np.column_stack((wave, wave))
        audio = (stereo * volume * 32767).astype(np.int16)
        return pygame.sndarray.make_sound(audio)

    def _generate_sounds(self):
        """Generate synthetic Sci-Fi UI sounds"""
        if not self.enabled:
            return

        # 1. Power On (Gameboy-style coin chime)
        self.sounds["startup"] = self._generate_sine_wave(1760, 0.2, 0.2) # A6

        # 2. Token Stream (High freq tick/blip - adjusted to be clickier)
        # Using a very short, high frequency sine wave instead of noise for a "cleaner" click
        self.sounds["token"] = self._generate_sine_wave(800, 0.02, 0.1) 

        # 3. Success (Major Chord Arpeggio-ish)
        self.sounds["success"] = self._generate_sine_wave(880, 0.2, 0.2) # A5

        # 4. Error (Sawtooth-ish / low buzzy sine)
        self.sounds["error"] = self._generate_sine_wave(150, 0.3, 0.3)
        
        # 5. Tool Call (Tech chirp)
        self.sounds["tool"] = self._generate_sine_wave(1200, 0.05, 0.1)

    def play(self, name: str):
        """Fire and forget sound"""
        if not self.enabled or name not in self.sounds:
            return
        try:
            self.sounds[name].play()
        except Exception:
            pass

    async def speak(self, text: str):
        """Generate and play TTS"""
        if not self.enabled:
            return

        try:
            import edge_tts
            
            # Use a Swedish voice if detected, else English
            # Simple heuristic
            voice = "sv-SE-MattiasNeural" if any(c in text for c in "åäöÅÄÖ") else "en-GB-RyanNeural"
            
            communicate = edge_tts.Communicate(text, voice)
            
            with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as fp:
                temp_path = fp.name
            
            await communicate.save(temp_path)
            
            # Play using pygame music to not block too much, but wait for it
            try:
                pygame.mixer.music.load(temp_path)
                pygame.mixer.music.play()
                while pygame.mixer.music.get_busy():
                    await asyncio.sleep(0.1)
                pygame.mixer.music.unload()
            finally:
                if os.path.exists(temp_path):
                    os.remove(temp_path)
                    
        except Exception:
            pass

# Global instance
_audio = None

def get_audio():
    global _audio
    if _audio is None:
        _audio = AudioEngine()
    return _audio
