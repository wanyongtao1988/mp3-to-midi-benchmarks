"""Match each reference onset to the nearest unused MIDI onset of the same pitch."""

import argparse
import csv
import json
from collections import defaultdict
from pathlib import Path

import mido


def read_events(path):
    elapsed = 0.0
    events = []
    for message in mido.MidiFile(path):
        elapsed += message.time * 1000
        if message.type == "note_on" and message.velocity:
            events.append((message.note, elapsed, message.velocity))
    return events


def main(directory, output):
    expected = defaultdict(list)
    with (directory / "reference-events.csv").open(newline="") as file:
        for row in csv.DictReader(file):
            expected[row["input"]].append(row)
    browser = json.loads((directory / "browser.json").read_text(encoding="utf-8"))
    recorded_files = [record["file"] for record in browser["records"]]
    if len(recorded_files) != len(expected) or set(recorded_files) != set(expected):
        raise ValueError("browser.json must contain exactly one record per reference input")
    output.mkdir(parents=True, exist_ok=True)
    summary = []
    columns = ("input", "note", "reference_pitch", "reference_start_ms", "reference_end_ms",
               "midi_pitch", "midi_start_ms", "midi_velocity", "onset_error_ms", "result", "pcm_peak_dbfs")
    with (output / "per-note-results.csv").open("w", newline="") as file:
        writer = csv.writer(file)
        writer.writerow(columns)
        for record in browser["records"]:
            name = record["file"]
            remaining = read_events(directory / record["export"]) if record["export"] else []
            if len(remaining) != record["notes"]:
                raise ValueError(f"{name}: MIDI onset count does not match browser.json")
            matched = 0
            for ref in expected[name]:
                start = float(ref["expected_start_ms"])
                pitch = int(ref["pitch"])
                eligible = [event for event in remaining if abs(event[1] - start) <= 100]
                matching = [event for event in eligible if event[0] == pitch]
                comparison = [name, ref["note"], pitch, start, ref["expected_end_ms"]]
                if matching:
                    event = min(matching, key=lambda item: abs(item[1] - start))
                    remaining.remove(event)
                    matched += 1
                    writer.writerow((*comparison, event[0], round(event[1], 3), event[2],
                                     round(event[1] - start, 3), "matched", ref["pcm_peak_dbfs"]))
                else:
                    writer.writerow((*comparison, "", "", "", "", "missing", ref["pcm_peak_dbfs"]))
            for pitch, start, velocity in remaining:
                same_window = any(abs(float(ref["expected_start_ms"]) - start) <= 100 for ref in expected[name])
                status = "unmatched_in_reference_window" if same_window else "outside_reference_windows"
                writer.writerow((name, "", "", "", "", pitch, round(start, 3), velocity, "", status,
                                 expected[name][0]["pcm_peak_dbfs"]))
            summary.append({**record, "reference_count": len(expected[name]), "matched": matched,
                            "unmatched_output": len(remaining), "peak_dbfs": expected[name][0]["pcm_peak_dbfs"]})
    (output / "summary.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(summary))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("directory", type=Path, help="Fixture directory with reference CSV, browser log, and MIDI")
    parser.add_argument("--output", type=Path, required=True, help="Directory for the results CSV and summary JSON")
    args = parser.parse_args()
    main(args.directory, args.output)
