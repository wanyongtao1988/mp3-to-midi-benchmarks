"""Generate the two November 17 controlled input sets and their note references."""

import argparse
import csv
import math
import subprocess
import tempfile
import wave
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
RATE = 44100
PITCHES = (60, 64, 67, 62, 65, 69, 63, 67)
DYNAMICS = (0.18, 0.7, 0.34, 0.93, 0.24, 0.52, 1.0, 0.45)


def note(pitch, duration_ms):
    frames = round(RATE * duration_ms / 1000)
    position = np.arange(frames)
    angle = position * 2 * np.pi * 440 * 2 ** ((pitch - 69) / 12) / RATE
    envelope = np.minimum(1, np.minimum(position / (0.004 * RATE), (frames - 1 - position) / (0.006 * RATE)))
    return envelope * (0.75 * np.sin(angle) + 0.18 * np.sin(2 * angle) + 0.07 * np.sin(3 * angle))


def build_phrase(duration_ms, strengths):
    samples = np.zeros(4 * RATE)
    events = []
    for i, (pitch, strength) in enumerate(zip(PITCHES, strengths)):
        start = round(RATE * (0.18 + 0.45 * i))
        value = strength * note(pitch, duration_ms)
        end = start + len(value)
        samples[start:end] = value
        events.append((i + 1, pitch, round(1000 * start / RATE, 3), round(1000 * end / RATE, 3)))
    return samples, events


def save_wave(file, samples, sample_bytes):
    assert np.max(abs(samples)) < 1
    ints = np.rint(samples * (2 ** (sample_bytes * 8 - 1) - 1)).astype("<i4")
    packed = ints.view(np.uint8).reshape(-1, 4)[:, :sample_bytes].copy().tobytes()
    with wave.open(str(file), "wb") as audio:
        audio.setparams((1, sample_bytes, RATE, 0, "NONE", "PCM"))
        audio.writeframes(packed)
    return 20 * math.log10(np.max(abs(ints)) / (2 ** (sample_bytes * 8 - 1) - 1))


def main(output, encoder):
    short_dir, gain_dir = output / "duration", output / "gain"
    for directory in (short_dir, gain_dir):
        directory.mkdir(parents=True, exist_ok=True)
    columns = ("input", "note", "pitch", "expected_start_ms", "expected_end_ms", "target_peak_dbfs", "pcm_peak_dbfs")
    for directory, conditions, make in (
        (short_dir, (30, 45, 60, 90, 120), make_short),
        (gain_dir, (-66, -52, -38, -24, -8), make_gain),
    ):
        with (directory / "reference-events.csv").open("w", newline="") as reference:
            rows = csv.writer(reference)
            rows.writerow(columns)
            for condition in conditions:
                name, events, target, peak = make(directory, condition, encoder)
                rows.writerows((name, *event, target, round(peak, 4)) for event in events)
                print(f"{name:21} {len(events)} notes, PCM peak {peak:.2f} dBFS")


def make_short(directory, duration, encoder):
    phrase, events = build_phrase(duration, (0.52,) * len(PITCHES))
    base = f"notes-{duration}ms"
    target = directory / f"{base}.mp3"
    with tempfile.TemporaryDirectory() as temporary_directory:
        wave_file = Path(temporary_directory) / f"{base}.wav"
        measured = save_wave(wave_file, phrase, 2)
        subprocess.run([encoder, "-v", "error", "-y", "-i", str(wave_file), "-c:a", "libmp3lame",
                        "-b:a", "128k", str(target)], check=True)
    subprocess.run([encoder, "-v", "error", "-i", str(target), "-f", "null", "-"], check=True)
    return target.name, events, "", measured


def make_gain(directory, dbfs, _encoder):
    phrase, events = build_phrase(200, DYNAMICS)
    target = directory / f"peak-minus-{abs(dbfs)}dbfs.wav"
    factor = 10 ** (dbfs / 20) / np.max(abs(phrase))
    measured = save_wave(target, phrase * factor, 3)
    assert abs(measured - dbfs) < 0.01
    return target.name, events, dbfs, measured


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=ROOT / "build" / "regenerated")
    parser.add_argument("--ffmpeg", default="ffmpeg", help="Path to FFmpeg with libmp3lame")
    args = parser.parse_args()
    main(args.output, args.ffmpeg)
