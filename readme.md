# Hashbrown

Hashbrown is a video redaction tool designed for legal and investigative professionals. It allows users to selectively mute audio within specific time segments of a video file. The application supports two processing modes: a high-speed audio-only redaction and a visual redaction mode that applies an overlay image.

## Usage

1. **Load Video:** Run the executable and drag and drop a video file into the window, or click "Browse" to select a file.
2. **Define Segments:** Input the **Start** and **End** timestamps (HH:MM:SS) for the section you wish to censor.
3. **Add Multiple Redactions:** Click the **+** button to add additional redaction segments if multiple parts of the video require censoring.
4. **Select Mode:**
    * **Unchecked (Default):** Fast Mode. Mutes audio without re-encoding the video stream. This preserves exact video quality and is extremely fast (in theory, not on practice).
    * **Checked (Include Overlay Image):** Standard Mode. Mutes audio and burns a "mute" icon overlay onto the video during the redacted segments. This requires re-encoding the video.
5. **Process:** Click "Process Video". The output file will be saved in the same directory as the source file with a suffix (e.g., `_redacted.mp4`).

## Internal Operations

Hashbrown utilizes FFmpeg for all media processing. It detects available hardware acceleration (NVIDIA NVENC) for faster encoding when visual overlays are enabled.

### FFmpeg Command Examples

**1. Fast Mode (Audio Mute Only)**
This mode copies the video stream directly (`-c:v copy`) and applies an audio filter (`-af`) to mute specific sections.

```bash
ffmpeg -y -i input.mp4 -c:v copy -af "volume=enable='between(t,10,20)+between(t,45,50)':volume=0" -c:a aac -b:a 128k output_redacted_fast.mp4
```

**2. Overlay Mode (Visual + Audio Redaction)**
This mode uses a complex filter graph (`-filter_complex`) to overlay an image and mute audio simultaneously. It re-encodes the video using H.264 (or H.264_NVENC if available) matching the original bitrate.

```bash
ffmpeg -y -i input.mp4 -i mute_icon.png -filter_complex "[0:v][1:v]overlay=5:5:enable='between(t,10,20)'[v_out];[0:a]volume=enable='between(t,10,20)':volume=0[a_out]" -map [v_out] -map [a_out] -c:v libx264 -preset fast -b:v 2M -c:a aac -b:a 128k output_redacted.mp4
```

---

_The test file is from https://archive.org/details/ParkCons1938_