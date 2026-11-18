# Noteline MP3-to-MIDI benchmarks

On November 17, 2026, Noteline tested two limits of its audio-to-MIDI converter using synthetic eight-note phrases. **45 ms was the shortest tested MP3 note length that recovered all eight notes.** The 30 ms input decoded successfully and produced zero detected notes. **−52 dBFS was the quietest tested WAV peak that recovered all eight notes.** At −66 dBFS, only notes 2, 4, and 7 were recovered.

These readings apply to the ten files below. The duration test sampled 30 and 45 ms with no intermediate setting, and the gain test sampled −66 and −52 dBFS with no intermediate setting. The two tests changed one variable at a time in separate phrases.

- [Noteline MP3 to MIDI converter](https://mp3tomidi.online/)
- [Short-note duration guide](https://mp3tomidi.online/guides/short-note-duration-mp3-to-midi/)
- [Quiet audio and gain guide](https://mp3tomidi.online/guides/quiet-audio-gain-mp3-to-midi/)

## MP3 note duration

| Duration | Input | Notes matched | MIDI export |
| --- | --- | ---: | --- |
| 30 ms | [MP3](data/duration/notes-30ms.mp3) | 0/8 | No sustained notes detected |
| 45 ms | [MP3](data/duration/notes-45ms.mp3) | 8/8 | [MIDI](data/duration/notes-45ms.mp3.mid) |
| 60 ms | [MP3](data/duration/notes-60ms.mp3) | 8/8 | [MIDI](data/duration/notes-60ms.mp3.mid) |
| 90 ms | [MP3](data/duration/notes-90ms.mp3) | 8/8 | [MIDI](data/duration/notes-90ms.mp3.mid) |
| 120 ms | [MP3](data/duration/notes-120ms.mp3) | 8/8 | [MIDI](data/duration/notes-120ms.mp3.mid) |

[40 reference events](data/duration/reference-events.csv) · [Per-note results](data/duration/per-note-results.csv) · [Browser log](data/duration/browser.json) · [Summary JSON](data/duration/summary.json)

## WAV input gain

| Peak target | Input | Notes matched | MIDI export |
| --- | --- | ---: | --- |
| −66 dBFS | [WAV](data/gain/peak-minus-66dbfs.wav) | 3/8 | [MIDI](data/gain/peak-minus-66dbfs.wav.mid) |
| −52 dBFS | [WAV](data/gain/peak-minus-52dbfs.wav) | 8/8 | [MIDI](data/gain/peak-minus-52dbfs.wav.mid) |
| −38 dBFS | [WAV](data/gain/peak-minus-38dbfs.wav) | 8/8 | [MIDI](data/gain/peak-minus-38dbfs.wav.mid) |
| −24 dBFS | [WAV](data/gain/peak-minus-24dbfs.wav) | 8/8 | [MIDI](data/gain/peak-minus-24dbfs.wav.mid) |
| −8 dBFS | [WAV](data/gain/peak-minus-8dbfs.wav) | 8/8 | [MIDI](data/gain/peak-minus-8dbfs.wav.mid) |

[40 reference events](data/gain/reference-events.csv) · [Per-note results](data/gain/per-note-results.csv) · [Browser log](data/gain/browser.json) · [Summary JSON](data/gain/summary.json)

## How the inputs and scores were made

- Both tests used four-second, 44.1 kHz mono inputs. The MIDI pitches were 60, 64, 67, 62, 65, 69, 63, and 67. Notes started 180 ms into each file, with 450 ms between onsets. Each note used the first three harmonics at relative amplitudes of 0.75, 0.18, and 0.07, a 4 ms attack, and a 6 ms release.
- The duration test fixed the note amplitude, changed its duration in the source PCM, then encoded 16-bit PCM to 128 kbps MP3 using FFmpeg and libmp3lame. The CSV's PCM peak and reference onset times describe the source before encoding. All five MP3s passed a separate FFmpeg decode check.
- The gain test used 200 ms notes with fixed relative dynamics throughout the phrase. A single gain multiplier set each target peak, then the phrase was saved as 24-bit PCM WAV. The CSV records the target and the measured peak after quantization.
- The [scoring script](scripts/score-fixtures.py) matches each reference to the nearest unused MIDI onset with identical pitch within ±100 ms, including the endpoints. It records missing and unmatched onsets separately. The output contained no unmatched onsets in this run. Onset recall is the measured outcome. Reference end times are included for inspection.
- The published records come from Windows Chrome 157.0.8103.52 running the converter offline from Noteline build `e7b8eff619e99060ba75b680531dee9f54f73b8c`. The 45 ms case matched all eight notes with onsets 4.623–5.375 ms earlier than the reference.

## Reproduce

Use Python 3.12 and install the dependencies. The original inputs were generated using FFmpeg 9.0.2 with libmp3lame. Put FFmpeg on your PATH or pass `--ffmpeg /path/to/ffmpeg` to the [generator](scripts/generate-fixtures.py).

```sh
python -m pip install -r requirements.txt
python scripts/generate-fixtures.py
python scripts/score-fixtures.py data/duration --output build/rescored/duration
python scripts/score-fixtures.py data/gain --output build/rescored/gain
```

The generator writes new files under `build/regenerated`. The last two commands score the archived browser exports and score results can be compared with the CSV and JSON above.

To check the current converter with freshly generated fixtures, install Node.js and Google Chrome and run the [browser script](scripts/run-fixtures.cjs). It saves the MIDI files and browser log locally, where the scoring script can read them. Browser and converter updates can affect a rerun.

```sh
npm install --no-save --package-lock=false playwright
node scripts/run-fixtures.cjs build/regenerated/duration
node scripts/run-fixtures.cjs build/regenerated/gain
python scripts/score-fixtures.py build/regenerated/duration --output build/current/duration
python scripts/score-fixtures.py build/regenerated/gain --output build/current/gain
```

## Licenses

The audio fixtures, MIDI outputs, reference-event CSVs, per-note results, browser logs, summary JSON, and this README are licensed under [Creative Commons Attribution 4.0 International (CC BY 4.0)](LICENSE-DATA). Attribute the dataset to Noteline and cite the version you use.

The source code in `scripts/`, `requirements.txt`, and repository configuration files are licensed under the [MIT License](LICENSE-CODE).

The license texts grant these permissions for the v1.0.0 benchmark files as well as the matching files on the main branch.

## Cite this benchmark

wanyongtao1988. (2026). *Noteline MP3-to-MIDI benchmarks* (v1.0.0) [Data set]. Zenodo. [https://doi.org/10.5281/zenodo.24346025](https://doi.org/10.5281/zenodo.24346025).
