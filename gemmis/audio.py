"""
GEMMIS Audio Engine - Pure Python Implementation (Native Linux)
"""
import asyncio
import os
import math
import struct
import wave
import tempfile
import subprocess
import threading
import random
from pathlib import Path

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
            
        self.enabled = True
        self.sounds = {}
        
        # Detect player
        self.player = None
        if self._check_command("paplay"):
            self.player = "paplay"
        elif self._check_command("aplay"):
            self.player = "aplay"
        else:
            self.enabled = False
            print("Audio Warning: No 'aplay' or 'paplay' found. Sound disabled.")
            
        if self.enabled:
            # Generate sounds cache (paths to temp files)
            self._generate_sounds()
            
        self.initialized = True
        self.tts_lock = asyncio.Lock()

    def _check_command(self, cmd):
        return subprocess.call(["which", cmd], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL) == 0

    def _write_wav(self, data, sample_rate=44100):
        """Write raw audio data to a temp wav file"""
        fd, path = tempfile.mkstemp(suffix=".wav")
        os.close(fd)
        
        with wave.open(path, 'w') as wav_file:
            wav_file.setnchannels(1)  # Mono
            wav_file.setsampwidth(2)  # 16-bit
            wav_file.setframerate(sample_rate)
            
            # Pack data
            # data is a list of floats -1.0 to 1.0
            # Scale to 16-bit integers
            scaled = [int(max(min(x, 1.0), -1.0) * 32767.0) for x in data]
            wav_file.writeframes(struct.pack('<' + 'h' * len(scaled), *scaled))
            
        return path

    def _gen_tone(self, freq, duration, vol=0.5, fade=True):
        """Generate a sine wave"""
        sample_rate = 44100
        n_samples = int(sample_rate * duration)
        data = []
        
        for i in range(n_samples):
            t = float(i) / sample_rate
            val = math.sin(2.0 * math.pi * freq * t)
            
            # Fade in/out
            if fade:
                fade_len = int(0.01 * sample_rate) # 10ms
                if i < fade_len:
                    val *= (i / fade_len)
                elif i > n_samples - fade_len:
                    val *= ((n_samples - i) / fade_len)
            
            data.append(val * vol)
        return data

    def _gen_noise(self, duration, vol=0.5):
        """Generate white noise"""
        sample_rate = 44100
        n_samples = int(sample_rate * duration)
        return [random.uniform(-1.0, 1.0) * vol for _ in range(n_samples)]

    def _generate_sounds(self):
        """Pre-render sounds to /tmp/"""
        # 1. Startup: A rising arpeggio (C5-E5-G5)
        startup_data = []
        startup_data.extend(self._gen_tone(523.25, 0.1, 0.3)) # C
        startup_data.extend(self._gen_tone(659.25, 0.1, 0.3)) # E
        startup_data.extend(self._gen_tone(783.99, 0.2, 0.3)) # G
        self.sounds["startup"] = self._write_wav(startup_data)

        # 2. Token: Very short high blip
        self.sounds["token"] = self._write_wav(self._gen_tone(1200, 0.015, 0.1))

        # 3. Success: High ping
        self.sounds["success"] = self._write_wav(self._gen_tone(880, 0.15, 0.2))

        # 4. Error: Low buzz
        error_data = []
        error_data.extend(self._gen_tone(150, 0.2, 0.4))
        error_data.extend(self._gen_tone(100, 0.2, 0.4))
        self.sounds["error"] = self._write_wav(error_data)

    def play(self, name: str):
        """Fire and forget sound playback"""
        if not self.enabled or name not in self.sounds:
            return
            
        def _run():
            try:
                subprocess.run([self.player, self.sounds[name]], 
                             stdout=subprocess.DEVNULL, 
                             stderr=subprocess.DEVNULL)
            except:
                pass
                
        # Run in thread to not block UI
        threading.Thread(target=_run, daemon=True).start()

    async def speak(self, text: str):
        """TTS using edge-tts (requires internet) or fallback"""
        if not self.enabled:
            return

        async with self.tts_lock:
            try:
                import edge_tts
                voice = "sv-SE-MattiasNeural" if any(c in text for c in "åäöÅÄÖ") else "en-GB-RyanNeural"
                communicate = edge_tts.Communicate(text, voice)
                
                with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as fp:
                    temp_path = fp.name
                
                await communicate.save(temp_path)
                
                # Play mp3
                subprocess.run([self.player, temp_path], 
                             stdout=subprocess.DEVNULL, 
                             stderr=subprocess.DEVNULL)
                             
                if os.path.exists(temp_path):
                    os.remove(temp_path)
            except Exception as e:
                pass # Fail silently if no internet/edge-tts

# Global instance
_audio = None

def get_audio():
    global _audio
    if _audio is None:
        _audio = AudioEngine()
    return _audio