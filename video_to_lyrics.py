#!/usr/bin/env python3
"""
Convert video to Google Images lyrics video.

When words are spoken in the video, AI searches Google Images for that word
and pulls a random image result, inserting it into the converted video.

Requirements:
    - ffmpeg, ffprobe
    - speech_recognition
    - requests
    - bing-image-downloader (for image searching)
    - opencv-python
    - pillow
"""

import os
import sys
import subprocess
import json
import tempfile
import shutil
from pathlib import Path
from typing import List, Tuple, Dict
import argparse
import random
import requests
from io import BytesIO


class VideoToGoogleImagesConverter:
    """Convert videos to Google Images-style lyrics videos."""

    def __init__(self, output_size: Tuple[int, int] = (1920, 1080), fps: int = 30):
        """
        Initialize converter.
        
        Args:
            output_size: Output video dimensions (width, height)
            fps: Frames per second for output video
        """
        self.output_size = output_size
        self.fps = fps
        self.temp_dir = tempfile.mkdtemp()
        self.images_cache = {}

    def extract_audio(self, video_path: str, output_audio: str) -> bool:
        """Extract audio from video file."""
        try:
            cmd = [
                'ffmpeg',
                '-i', video_path,
                '-q:a', '9',
                '-n',
                output_audio
            ]
            subprocess.run(cmd, check=True, capture_output=True)
            return True
        except subprocess.CalledProcessError as e:
            print(f"Error extracting audio: {e}")
            return False

    def get_video_duration(self, video_path: str) -> float:
        """Get video duration in seconds."""
        try:
            result = subprocess.run(
                ['ffprobe', '-v', 'error', '-show_entries', 'format=duration',
                 '-of', 'default=noprint_wrappers=1:nokey=1:novalue=1', video_path],
                capture_output=True, text=True, check=True
            )
            return float(result.stdout.strip())
        except Exception as e:
            print(f"Error getting duration: {e}")
            return 0

    def transcribe_audio(self, audio_path: str) -> List[Dict[str, any]]:
        """
        Transcribe audio to get words with timestamps.
        
        Returns:
            List of dicts: [{"word": "hello", "start": 0.5, "end": 1.2}, ...]
        """
        try:
            import speech_recognition as sr
            from pydub import AudioSegment
            
            recognizer = sr.Recognizer()
            
            # Convert to WAV if needed
            audio = AudioSegment.from_file(audio_path)
            wav_path = os.path.join(self.temp_dir, "audio.wav")
            audio.export(wav_path, format="wav")
            
            with sr.AudioFile(wav_path) as source:
                audio_data = recognizer.record(source)
            
            # Try to get partial results with timing
            try:
                result = recognizer.recognize_google(audio_data, language='en-US')
                # Basic parsing - ideally use Google's API for word-level timestamps
                words = result.split()
                duration = len(audio) / 1000.0  # ms to seconds
                word_duration = duration / len(words) if words else 0
                
                transcription = []
                for i, word in enumerate(words):
                    transcription.append({
                        "word": word.lower().strip('.,!?;:"'),
                        "start": i * word_duration,
                        "end": (i + 1) * word_duration
                    })
                
                return transcription
                
            except sr.UnknownValueError:
                print("Could not understand audio")
                return []
            except sr.RequestError as e:
                print(f"API error: {e}")
                return []
                
        except ImportError:
            print("Error: Required packages not installed.")
            print("Install with: pip install SpeechRecognition pydub")
            return []

    def search_google_images(self, query: str, num_images: int = 5) -> List[str]:
        """
        Search Google Images and return URLs.
        
        Args:
            query: Search term
            num_images: Number of images to fetch
            
        Returns:
            List of image URLs
        """
        if query in self.images_cache:
            return self.images_cache[query]
        
        try:
            from bing_image_downloader import bing_image_downloader
            
            # Use bing image search (more reliable than Google)
            bing = bing_image_downloader.bing_image_downloader(
                query=query,
                limit=num_images,
                output_dir="dataset",
                adult_filter_off=True,
                force_replace=False,
                timeout=15
            )
            
            # Get the downloaded image paths
            image_dir = f"dataset/{query.replace(' ', '_')}"
            if os.path.exists(image_dir):
                images = [os.path.join(image_dir, f) for f in os.listdir(image_dir)]
                self.images_cache[query] = images
                return images
            
            return []
            
        except ImportError:
            print("Error: bing-image-downloader not installed.")
            print("Install with: pip install bing-image-downloader")
            return []

    def create_frame_with_image(self, image_path: str, text: str = "") -> str:
        """Create a frame with an image and optional text overlay."""
        try:
            from PIL import Image, ImageDraw, ImageFont
            import cv2
            import numpy as np
            
            # Load and resize image to fit output size
            img = Image.open(image_path).convert('RGB')
            img.thumbnail(self.output_size, Image.Resampling.LANCZOS)
            
            # Create white background and center image
            bg = Image.new('RGB', self.output_size, color='white')
            offset = ((self.output_size[0] - img.width) // 2,
                     (self.output_size[1] - img.height) // 2)
            bg.paste(img, offset)
            
            # Add text if provided
            if text:
                draw = ImageDraw.Draw(bg)
                try:
                    font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 60)
                except:
                    font = ImageFont.load_default()
                
                # Add semi-transparent background for text
                bbox = draw.textbbox((0, 0), text, font=font)
                text_width = bbox[2] - bbox[0] + 20
                text_height = bbox[3] - bbox[1] + 20
                
                text_x = (self.output_size[0] - text_width) // 2
                text_y = self.output_size[1] - text_height - 20
                
                # Draw semi-transparent background
                overlay = Image.new('RGBA', self.output_size, (0, 0, 0, 0))
                overlay_draw = ImageDraw.Draw(overlay)
                overlay_draw.rectangle([text_x - 10, text_y - 10, text_x + text_width, text_y + text_height],
                                      fill=(0, 0, 0, 180))
                bg = Image.alpha_composite(bg.convert('RGBA'), overlay).convert('RGB')
                
                # Draw text
                draw = ImageDraw.Draw(bg)
                draw.text((text_x, text_y), text, fill='white', font=font)
            
            temp_frame = os.path.join(self.temp_dir, f"frame_{random.randint(0, 999999)}.png")
            bg.save(temp_frame)
            return temp_frame
            
        except Exception as e:
            print(f"Error creating frame: {e}")
            return None

    def create_black_frame(self, text: str = "") -> str:
        """Create a black frame with text."""
        try:
            from PIL import Image, ImageDraw, ImageFont
            
            img = Image.new('RGB', self.output_size, color='black')
            
            if text:
                draw = ImageDraw.Draw(img)
                try:
                    font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 80)
                except:
                    font = ImageFont.load_default()
                
                bbox = draw.textbbox((0, 0), text, font=font)
                text_width = bbox[2] - bbox[0]
                text_height = bbox[3] - bbox[1]
                
                x = (self.output_size[0] - text_width) // 2
                y = (self.output_size[1] - text_height) // 2
                
                draw.text((x, y), text, fill='white', font=font)
            
            temp_frame = os.path.join(self.temp_dir, f"frame_{random.randint(0, 999999)}.png")
            img.save(temp_frame)
            return temp_frame
            
        except Exception as e:
            print(f"Error creating black frame: {e}")
            return None

    def create_lyrics_video(self, video_path: str, output_path: str = "output.mp4") -> bool:
        """
        Create a Google Images lyrics video.
        
        Args:
            video_path: Path to input video
            output_path: Path for output video
            
        Returns:
            True if successful
        """
        try:
            # Extract audio
            print("[1/5] Extracting audio...")
            audio_file = os.path.join(self.temp_dir, "audio.mp3")
            if not self.extract_audio(video_path, audio_file):
                return False
            
            # Get duration
            print("[2/5] Analyzing video...")
            duration = self.get_video_duration(video_path)
            
            # Transcribe audio
            print("[3/5] Transcribing audio...")
            transcription = self.transcribe_audio(audio_file)
            
            if not transcription:
                print("⚠️  Could not transcribe audio. Using fallback mode...")
                transcription = []
            
            # Search for images
            print("[4/5] Searching for images...")
            unique_words = set(item['word'] for item in transcription if item['word'])
            
            for word in unique_words:
                if word and len(word) > 2:  # Skip short words
                    print(f"  Searching: {word}")
                    images = self.search_google_images(word, num_images=3)
                    if not images:
                        print(f"  ⚠️  No images found for '{word}'")
            
            # Create frames directory
            print("[5/5] Generating frames...")
            frames_dir = os.path.join(self.temp_dir, "frames")
            os.makedirs(frames_dir, exist_ok=True)
            
            frame_num = 0
            trans_idx = 0
            total_frames = int(duration * self.fps)
            
            for frame_idx in range(total_frames):
                current_time = frame_idx / self.fps
                current_word = ""
                
                # Find current word
                while trans_idx < len(transcription) and transcription[trans_idx]['end'] <= current_time:
                    trans_idx += 1
                
                if trans_idx < len(transcription) and transcription[trans_idx]['start'] <= current_time:
                    current_word = transcription[trans_idx]['word']
                
                # Get image for word or create black frame
                frame_path = None
                if current_word and current_word in self.images_cache:
                    images = self.images_cache[current_word]
                    if images:
                        image = random.choice(images)
                        frame_path = self.create_frame_with_image(image, current_word)
                
                if not frame_path:
                    frame_path = self.create_black_frame(current_word)
                
                if frame_path:
                    final_frame = os.path.join(frames_dir, f"frame_{frame_num:06d}.png")
                    shutil.copy(frame_path, final_frame)
                    frame_num += 1
                
                # Progress
                if frame_idx % 30 == 0:
                    print(f"  Progress: {frame_idx}/{total_frames} frames")
            
            # Create video from frames
            print("\n🎬 Creating video...")
            input_pattern = os.path.join(frames_dir, "frame_%06d.png")
            
            cmd = [
                'ffmpeg',
                '-framerate', str(self.fps),
                '-i', input_pattern,
                '-i', audio_file,
                '-c:v', 'libx264',
                '-pix_fmt', 'yuv420p',
                '-c:a', 'aac',
                '-shortest',
                '-n',
                output_path
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                print(f"✅ Video created: {output_path}")
                return True
            else:
                print(f"Error creating video: {result.stderr}")
                return False
            
        except Exception as e:
            print(f"Error: {e}")
            import traceback
            traceback.print_exc()
            return False
        
        finally:
            # Cleanup
            shutil.rmtree(self.temp_dir, ignore_errors=True)

    def cleanup(self):
        """Clean up temporary files."""
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)


def main():
    parser = argparse.ArgumentParser(
        description="Convert video to Google Images lyrics video"
    )
    parser.add_argument('video', help='Input video file')
    parser.add_argument('-o', '--output', default='output.mp4', help='Output video file')
    parser.add_argument('--width', type=int, default=1920, help='Output width')
    parser.add_argument('--height', type=int, default=1080, help='Output height')
    parser.add_argument('--fps', type=int, default=30, help='Frames per second')
    
    args = parser.parse_args()
    
    if not os.path.exists(args.video):
        print(f"Error: Video file not found: {args.video}")
        return 1
    
    converter = VideoToGoogleImagesConverter(
        output_size=(args.width, args.height),
        fps=args.fps
    )
    
    try:
        success = converter.create_lyrics_video(args.video, args.output)
        return 0 if success else 1
    finally:
        converter.cleanup()


if __name__ == '__main__':
    sys.exit(main())
