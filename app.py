from flask import Flask, request, send_file, jsonify
from flask_cors import CORS
import subprocess
import pydub
import os
from df.enhance import enhance, init_df, load_audio, save_audio

app = Flask(__name__, static_folder='static', static_url_path='')
CORS(app)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
YTDLP    = os.path.join(BASE_DIR, 'yt-dlp.exe')
FFMPEG   = os.path.join(BASE_DIR, 'ffmpeg.exe')
DL_DIR   = os.path.join(BASE_DIR, 'downloads')

# DeepFilterNet model load karo
print("Loading DeepFilterNet model...")
model, df_state, _ = init_df()
print("Model ready!")

@app.route('/')
def index():
    return app.send_static_file('index.html')

# =================== YOUTUBE URL ===================
@app.route('/process', methods=['POST'])
def process():
    data = request.get_json()
    url  = data.get('url')
    if not url:
        return jsonify({'error': 'No URL provided'}), 400

    video_path  = os.path.join(DL_DIR, 'video.mp4')
    audio_path  = os.path.join(DL_DIR, 'audio.wav')
    clean_audio = os.path.join(DL_DIR, 'clean_audio.wav')
    output_path = os.path.join(DL_DIR, 'output.mp4')

    for f in [video_path, audio_path, clean_audio, output_path]:
        if os.path.exists(f):
            os.remove(f)

    # Step 1: Download video
    subprocess.run([
        YTDLP,
        '-f', 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
        '--merge-output-format', 'mp4',
        '--ffmpeg-location', BASE_DIR,
        '-o', video_path,
        url
    ], check=True)

    # Step 2: Extract audio
    subprocess.run([
        FFMPEG, '-y',
        '-i', video_path,
        '-q:a', '0',
        '-map', 'a',
        audio_path
    ], check=True)

    # Step 3: DeepFilterNet se clean karo
    print("Cleaning audio...")
    audio_tensor, _ = load_audio(audio_path, sr=df_state.sr())
    enhanced = enhance(model, df_state, audio_tensor)
    save_audio(clean_audio, enhanced, df_state.sr())
    print("Done!")

    # Step 4: Merge back
    subprocess.run([
        FFMPEG, '-y',
        '-i', video_path,
        '-i', clean_audio,
        '-c:v', 'copy',
        '-map', '0:v:0',
        '-map', '1:a:0',
        output_path
    ], check=True)

    return send_file(output_path, as_attachment=True, download_name='clean_video.mp4')


# =================== FILE UPLOAD ===================
@app.route('/process-file', methods=['POST'])
def process_file():
    file = request.files['file']
    if not file:
        return jsonify({'error': 'No file provided'}), 400

    original_path = os.path.join(DL_DIR, 'uploaded_file')
    audio_path    = os.path.join(DL_DIR, 'audio.wav')
    clean_audio   = os.path.join(DL_DIR, 'clean_audio.wav')
    output_path   = os.path.join(DL_DIR, 'output.mp4')

    for f in [original_path, audio_path, clean_audio, output_path]:
        if os.path.exists(f):
            os.remove(f)

    # file save karo
    file.save(original_path)

    # WAV mein convert karo
    audio = pydub.AudioSegment.from_file(original_path)
    audio.export(audio_path, format='wav')

    # DeepFilterNet se clean karo
    print("Cleaning uploaded file...")
    audio_tensor, _ = load_audio(audio_path, sr=df_state.sr())
    enhanced = enhance(model, df_state, audio_tensor)
    save_audio(clean_audio, enhanced, df_state.sr())
    print("Done!")

    # video hai to merge karo
    is_video = file.filename.lower().endswith(('.mp4', '.mov', '.avi'))
    if is_video:
        subprocess.run([
            FFMPEG, '-y',
            '-i', original_path,
            '-i', clean_audio,
            '-c:v', 'copy',
            '-map', '0:v:0',
            '-map', '1:a:0',
            output_path
        ], check=True)
        return send_file(output_path, as_attachment=True,
                        download_name='clean_video.mp4')
    else:
        return send_file(clean_audio, as_attachment=True,
                        download_name='clean_audio.wav')


if __name__ == '__main__':
    app.run(debug=True)
if __name__ == '__main__':
    app.run(debug=True, port=5000)
