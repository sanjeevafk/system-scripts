# Media Tools & Subtitle Embedding Guide

Tools and reference workflows for synchronizing, embedding, and managing video subtitles.

---

## 1. Automated Subtitle Sync (`sync-subs`)

`sync-subs` is an agnostic CLI tool that synchronizes out-of-sync subtitle files (`.srt`, `.vtt`, `.ass`) to video files (`.mp4`, `.mkv`, `.avi`, etc.) using voice activity detection and speech cross-correlation.

### Usage

```bash
# Run inside a folder containing video and subtitles:
sync-subs

# Run on a specific movie folder:
sync-subs /path/to/movie-folder

# Run on explicit files:
sync-subs movie.mkv subtitles.srt

# Custom output destination:
sync-subs movie.mp4 subtitles.srt -o output.srt
```

---

## 2. Embedding Subtitles into Video (FFmpeg)

### Method A: Soft Subtitles (Recommended)
Embeds subtitle tracks inside the media container without re-encoding the video. Takes ~5 seconds, retains 100% original video quality, and allows toggling subtitles on/off in media players.

#### For MKV Containers:
MKV supports raw UTF-8 SRT streams natively:
```bash
ffmpeg -i movie.mp4 -i movie.srt -c copy movie_with_subs.mkv
```

#### For MP4 Containers:
MP4 requires converting the subtitle stream to Apple `mov_text`:
```bash
ffmpeg -i movie.mp4 -i movie.srt -c:v copy -c:a copy -c:s mov_text movie_with_subs.mp4
```

#### Multiple Subtitle Tracks (Multi-Language):
```bash
ffmpeg -i movie.mkv -i eng.srt -i spa.srt \
  -map 0:v -map 0:a -map 1:s -map 2:s \
  -metadata:s:s:0 language=eng -metadata:s:s:0 title="English" \
  -metadata:s:s:1 language=spa -metadata:s:s:1 title="Spanish" \
  -c copy movie_multi_sub.mkv
```

---

### Method B: Hard Subtitles (Burned In)
Draws subtitle text directly onto the video frames. Subtitles cannot be turned off. This requires re-encoding the full video stream (takes minutes and requires CPU/GPU resources).

```bash
ffmpeg -i movie.mp4 -vf "subtitles=movie.srt" -c:a copy movie_burned.mp4
```

*Note on styling:* With hard burning, you can customize fonts and sizes via `force_style`:
```bash
ffmpeg -i movie.mp4 -vf "subtitles=movie.srt:force_style='FontSize=24,PrimaryColour=&H00FFFFFF,Outline=1'" -c:a copy movie_burned.mp4
```

---

## 3. Extracting Subtitles from Video

To pull an embedded subtitle track back out into a standalone `.srt` file:

```bash
# Extract the first subtitle stream (stream 0:s:0)
ffmpeg -i movie_with_subs.mkv -map 0:s:0 extracted.srt
```
