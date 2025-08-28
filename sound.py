import simpleaudio as sa
import math
import struct

def play_melody(notes, sample_rate=44100):
    """
    notes: list of (frequency, duration) tuples
    Plays melody non-blocking without numpy.
    """
    audio_samples = []

    for freq, dur in notes:
        n_samples = int(sample_rate * dur)
        amplitude = 32767 * 0.5  # half volume
        for i in range(n_samples):
            t = i / sample_rate
            value = int(amplitude * math.sin(2 * math.pi * freq * t))
            audio_samples.append(value)

    # Convert to bytes
    byte_data = b''.join(struct.pack('<h', s) for s in audio_samples)

    # Play with simpleaudio
    play_obj = sa.play_buffer(byte_data, 1, 2, sample_rate) # 1 channel, 2 bytes per sample
    play_obj.wait_done()  # blocks until finished

