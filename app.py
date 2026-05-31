from flask import Flask, request, send_file, jsonify
from flask_cors import CORS
import subprocess
import noisereduce as nr
import scipy.io.wavfile as wav
import numpy as np
import os
import uuid
import time

app = Flask(__name__, static_folder='static', static_url_path='')
CORS(app)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
YTDLP    = os.path.join(BASE_DIR, 'yt-dlp.exe')
FFMPEG   = os.path.join(BASE_DIR, 'ffmpeg.exe')
DL_DIR   = os.path.join(BASE_DIR, 'downloads')

# Ensure downloads directory exists
os.makedirs(DL_DIR, exist_ok=True)

def cleanup_old_files():
    """Delete files in downloads directory that are older than 10 minutes."""
    if not os.path.exists(DL_DIR):
        return
    now = time.time()
    for filename in os.listdir(DL_DIR):
        file_path = os.path.join(DL_DIR, filename)
        if os.path.isfile(file_path):
            try:
                # 600 seconds = 10 minutes
                if os.path.getmtime(file_path) < now - 600:
                    os.remove(file_path)
                    print(f"Cleaned up old file: {filename}")
            except Exception as e:
                print(f"Error deleting {filename}: {e}")

@app.route('/')
def index():
    return app.send_static_file('index.html')

@app.route('/process', methods=['POST'])
def process():
    # Run cleanup of older temp files
    cleanup_old_files()

    data = request.get_json()
    url  = data.get('url')

    if not url:
        return jsonify({'error': 'No URL provided'}), 400

    session_id = str(uuid.uuid4())
    video_path  = os.path.join(DL_DIR, f'{session_id}_video.mp4')
    audio_path  = os.path.join(DL_DIR, f'{session_id}_audio.wav')
    clean_audio = os.path.join(DL_DIR, f'{session_id}_clean.wav')
    output_path = os.path.join(DL_DIR, f'{session_id}_output.mp4')

    try:
        # Step 1: Download video
        print(f"[{session_id}] Downloading video from URL: {url}")
        subprocess.run([
            YTDLP,
            '-f', 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
            '--merge-output-format', 'mp4',
            '--ffmpeg-location', BASE_DIR,
            '--no-playlist',
            '-o', video_path,
            url
        ], check=True)

        if not os.path.exists(video_path):
            raise FileNotFoundError("Downloaded video file not found")

        # Step 2: Extract audio as WAV
        print(f"[{session_id}] Extracting audio from video")
        subprocess.run([
            FFMPEG, '-y',
            '-i', video_path,
            '-q:a', '0',
            '-map', 'a',
            audio_path
        ], check=True)

        if not os.path.exists(audio_path):
            raise FileNotFoundError("Extracted audio file not found")

        # Step 3: Remove noise
        print(f"[{session_id}] Reducing noise from audio")
        rate, audio_data = wav.read(audio_path)
        if len(audio_data.shape) == 2:
            reduced = np.array([
                nr.reduce_noise(y=audio_data[:, i].astype(float), sr=rate)
                for i in range(audio_data.shape[1])
            ]).T
        else:
            reduced = nr.reduce_noise(y=audio_data.astype(float), sr=rate)
        
        # Save clean audio
        wav.write(clean_audio, rate, reduced.astype(np.int16))

        if not os.path.exists(clean_audio):
            raise FileNotFoundError("Processed clean audio file not found")

        # Step 4: Merge clean audio back into video
        print(f"[{session_id}] Merging clean audio back into video")
        subprocess.run([
            FFMPEG, '-y',
            '-i', video_path,
            '-i', clean_audio,
            '-c:v', 'copy',
            '-map', '0:v:0',
            '-map', '1:a:0',
            output_path
        ], check=True)

        if not os.path.exists(output_path):
            raise FileNotFoundError("Merged output video file not found")

        # Clean up intermediate processing files immediately to save space
        for f in [video_path, audio_path, clean_audio]:
            if os.path.exists(f):
                os.remove(f)

        print(f"[{session_id}] Processing complete. Sending clean video file.")
        return send_file(output_path, as_attachment=True, download_name='clean_video.mp4')

    except Exception as e:
        print(f"[{session_id}] Error occurred: {e}")
        # Clean up all temporary files on failure
        for f in [video_path, audio_path, clean_audio, output_path]:
            if os.path.exists(f):
                try:
                    os.remove(f)
                except Exception:
                    pass
        return jsonify({'error': f"Failed to process video: {str(e)}"}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5000)