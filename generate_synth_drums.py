#!/usr/bin/env python3
"""
Generate synthesized drum sounds
Creates realistic electronic drum samples using synthesis
"""

import numpy as np
import wave
import os

# Audio parameters
SAMPLE_RATE = 44100
BIT_DEPTH = 16


def save_wav(filename, audio_data, sample_rate=SAMPLE_RATE):
    """Save audio data as WAV file"""
    # Normalize and convert to 16-bit PCM
    audio_data = np.clip(audio_data, -1.0, 1.0)
    audio_data = (audio_data * 32767).astype(np.int16)

    # Write WAV file
    with wave.open(filename, 'w') as wav_file:
        wav_file.setnchannels(1)  # Mono
        wav_file.setsampwidth(2)  # 16-bit
        wav_file.setframerate(sample_rate)
        wav_file.writeframes(audio_data.tobytes())

    print(f"✓ Created: {filename}")


def generate_kick(duration=0.5, freq=60, pitch_decay=50):
    """Generate kick drum sound"""
    t = np.linspace(0, duration, int(SAMPLE_RATE * duration))

    # Pitch envelope (starts high, drops quickly)
    pitch_envelope = freq + pitch_decay * np.exp(-15 * t)

    # Phase for sine wave with pitch envelope
    phase = 2 * np.pi * np.cumsum(pitch_envelope) / SAMPLE_RATE

    # Generate tone
    kick = np.sin(phase)

    # Amplitude envelope (punchy attack, quick decay)
    env = np.exp(-8 * t)

    # Apply envelope
    kick = kick * env

    # Add click for attack
    click = np.exp(-80 * t) * np.random.normal(0, 0.3, len(t))
    kick = kick * 0.9 + click * 0.1

    return kick


def generate_snare(duration=0.15, tone_freq=200):
    """Generate snare drum sound"""
    t = np.linspace(0, duration, int(SAMPLE_RATE * duration))

    # Tonal component (body)
    tone = np.sin(2 * np.pi * tone_freq * t) + 0.5 * np.sin(2 * np.pi * tone_freq * 1.5 * t)

    # Noise component (snare wires)
    noise = np.random.normal(0, 1, len(t))

    # High-pass filter the noise (emphasize high frequencies)
    # Simple HPF by subtracting low frequencies
    noise_filtered = noise - 0.5 * np.roll(noise, 1)

    # Envelopes
    tone_env = np.exp(-12 * t)
    noise_env = np.exp(-8 * t)

    # Mix tone and noise
    snare = tone * tone_env * 0.4 + noise_filtered * noise_env * 0.6

    return snare


def generate_hihat(duration=0.05, closed=True):
    """Generate hi-hat sound"""
    t = np.linspace(0, duration, int(SAMPLE_RATE * duration))

    # High frequency noise
    noise = np.random.normal(0, 1, len(t))

    # High-pass filter (emphasize very high frequencies)
    noise_filtered = noise - 0.7 * np.roll(noise, 1)

    # Envelope (very short for closed, longer for open)
    if closed:
        env = np.exp(-100 * t)
    else:
        env = np.exp(-15 * t)

    hihat = noise_filtered * env

    return hihat


def generate_tom(duration=0.3, freq=120):
    """Generate tom drum sound"""
    t = np.linspace(0, duration, int(SAMPLE_RATE * duration))

    # Pitch envelope
    pitch_envelope = freq + 30 * np.exp(-12 * t)
    phase = 2 * np.pi * np.cumsum(pitch_envelope) / SAMPLE_RATE

    # Generate tone with harmonics
    tom = np.sin(phase) + 0.3 * np.sin(2 * phase)

    # Amplitude envelope
    env = np.exp(-7 * t)

    # Add slight noise for realistic character
    noise = np.random.normal(0, 0.1, len(t)) * np.exp(-20 * t)

    tom = tom * env * 0.9 + noise * 0.1

    return tom


def generate_clap(duration=0.08, bursts=4):
    """Generate clap sound (multiple short bursts)"""
    t = np.linspace(0, duration, int(SAMPLE_RATE * duration))
    clap = np.zeros(len(t))

    # Create multiple bursts
    for i in range(bursts):
        burst_start = int(i * len(t) / (bursts * 2))
        burst_len = int(len(t) / (bursts * 3))

        if burst_start + burst_len < len(t):
            burst = np.random.normal(0, 1, burst_len)
            burst *= np.exp(-50 * np.linspace(0, duration / bursts, burst_len))
            clap[burst_start:burst_start + burst_len] += burst

    # High-pass filter
    clap_filtered = clap - 0.5 * np.roll(clap, 1)

    # Overall envelope
    env = np.exp(-15 * t)

    return clap_filtered * env


def generate_rimshot(duration=0.03):
    """Generate rimshot sound (sharp, high-pitched click)"""
    t = np.linspace(0, duration, int(SAMPLE_RATE * duration))

    # High frequency tone
    tone = np.sin(2 * np.pi * 1800 * t) + 0.5 * np.sin(2 * np.pi * 3600 * t)

    # Sharp click
    click = np.random.normal(0, 1, len(t))

    # Very short envelope
    env = np.exp(-200 * t)

    rimshot = (tone * 0.6 + click * 0.4) * env

    return rimshot


def generate_cowbell(duration=0.4, freq=540):
    """Generate cowbell sound"""
    t = np.linspace(0, duration, int(SAMPLE_RATE * duration))

    # Two frequencies for metallic sound
    tone1 = np.sin(2 * np.pi * freq * t)
    tone2 = np.sin(2 * np.pi * freq * 1.5 * t)

    # Mix tones
    cowbell = tone1 * 0.6 + tone2 * 0.4

    # Envelope
    env = np.exp(-5 * t)

    return cowbell * env


def generate_crash(duration=1.5):
    """Generate crash cymbal sound"""
    t = np.linspace(0, duration, int(SAMPLE_RATE * duration))

    # Complex noise with multiple bands
    crash = np.zeros(len(t))

    for freq in [3000, 5000, 7000, 9000, 11000]:
        band = np.sin(2 * np.pi * freq * t + np.random.uniform(0, 2*np.pi))
        band += np.random.normal(0, 0.3, len(t))
        crash += band

    # High-pass filter
    crash_filtered = crash - 0.6 * np.roll(crash, 1)

    # Long decay envelope
    env = np.exp(-2 * t)

    return crash_filtered * env * 0.3


def main():
    print("="*60)
    print("  SYNTHESIZED DRUM GENERATOR")
    print("="*60)
    print()

    # Create output directory
    output_dir = "sounds/synth_drums"
    os.makedirs(output_dir, exist_ok=True)
    print(f"Output directory: {output_dir}\n")

    print("Generating drums...\n")

    # Generate all drum sounds
    drums = {
        'kick.wav': generate_kick(duration=0.5, freq=60, pitch_decay=50),
        'kick_deep.wav': generate_kick(duration=0.6, freq=45, pitch_decay=40),
        'snare.wav': generate_snare(duration=0.15, tone_freq=200),
        'snare_tight.wav': generate_snare(duration=0.10, tone_freq=250),
        'hihat_closed.wav': generate_hihat(duration=0.05, closed=True),
        'hihat_open.wav': generate_hihat(duration=0.3, closed=False),
        'tom_low.wav': generate_tom(duration=0.3, freq=100),
        'tom_mid.wav': generate_tom(duration=0.28, freq=140),
        'tom_high.wav': generate_tom(duration=0.25, freq=180),
        'clap.wav': generate_clap(duration=0.08, bursts=4),
        'rimshot.wav': generate_rimshot(duration=0.03),
        'cowbell.wav': generate_cowbell(duration=0.4, freq=540),
        'crash.wav': generate_crash(duration=1.5),
    }

    # Save all drums
    for filename, audio in drums.items():
        filepath = os.path.join(output_dir, filename)
        save_wav(filepath, audio)

    print(f"\n{'='*60}")
    print(f"  COMPLETE!")
    print(f"{'='*60}")
    print(f"\n✓ Generated {len(drums)} synthesized drums")
    print(f"✓ Saved to: {output_dir}/")
    print(f"\nDrum types:")
    print(f"  • Kicks: kick.wav, kick_deep.wav")
    print(f"  • Snares: snare.wav, snare_tight.wav")
    print(f"  • Hi-hats: hihat_closed.wav, hihat_open.wav")
    print(f"  • Toms: tom_low.wav, tom_mid.wav, tom_high.wav")
    print(f"  • Effects: clap.wav, rimshot.wav, cowbell.wav, crash.wav")
    print(f"\nPreview:")
    print(f"  afplay {output_dir}/kick.wav")
    print(f"  afplay {output_dir}/snare.wav")
    print(f"  afplay {output_dir}/hihat_closed.wav")
    print(f"\n{'='*60}\n")


if __name__ == '__main__':
    main()
