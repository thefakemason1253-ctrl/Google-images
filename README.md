# Google Images Lyrics Video Converter

Automatically convert videos into Google Images-style lyric videos! 🎬📸

## How It Works

1. **Extracts audio** from your video
2. **Transcribes speech** using AI to identify words and their timestamps
3. **Searches Google Images** for each spoken word
4. **Pulls random image results** and syncs them to when the word is spoken
5. **Creates a new video** with images displayed alongside the audio

The result is that iconic YouTube vibe where images pop up as words are spoken!

## Installation

```bash
# Clone the repo
git clone https://github.com/thefakemason1253-ctrl/Google-images
cd Google-images

# Install dependencies
pip install -r requirements.txt

# Make sure ffmpeg is installed
# macOS: brew install ffmpeg
# Ubuntu: sudo apt-get install ffmpeg
# Windows: Download from https://ffmpeg.org/download.html
```

## Usage

```bash
python video_to_lyrics.py input_video.mp4 -o output.mp4
```

### Options

```bash
python video_to_lyrics.py input_video.mp4 \
  -o output.mp4 \
  --width 1920 \
  --height 1080 \
  --fps 30
```

- `-o, --output`: Output video filename (default: `output.mp4`)
- `--width`: Video width in pixels (default: 1920)
- `--height`: Video height in pixels (default: 1080)
- `--fps`: Frames per second (default: 30)

## Features

✨ **Automatic Transcription** - Uses speech recognition AI to identify spoken words
🖼️ **Google Images Integration** - Automatically searches and downloads relevant images
🎨 **Smart Framing** - Centers images and adds word overlays
🔄 **Real-time Sync** - Images appear exactly when words are spoken
📹 **High Quality** - Supports custom resolution and framerate

## Example

```bash
python video_to_lyrics.py song.mp4 -o my_lyrics_video.mp4
```

## Dependencies

- Python 3.7+
- ffmpeg & ffprobe
- speech_recognition
- bing-image-downloader
- pillow
- opencv-python
- pydub

## How to Get Help

If images aren't downloading:
1. Check your internet connection
2. Try searching for a different word manually first
3. Some words may not return image results

If audio transcription fails:
1. Make sure audio is clear
2. Try English content (other languages not yet supported)
3. Check that SpeechRecognition library is properly installed

## License

MIT

---

Made with ❤️ for creating awesome lyric videos
