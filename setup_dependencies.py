import os
import sys
import zipfile
import urllib.request
import subprocess

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

def download_file(url, dest_path):
    print(f"Downloading {url}...")
    req = urllib.request.Request(
        url, 
        headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
    )
    with urllib.request.urlopen(req) as response, open(dest_path, 'wb') as out_file:
        total_size = int(response.info().get('Content-Length', 0))
        downloaded = 0
        chunk_size = 1024 * 1024  # 1MB
        while True:
            chunk = response.read(chunk_size)
            if not chunk:
                break
            out_file.write(chunk)
            downloaded += len(chunk)
            if total_size:
                percent = (downloaded / total_size) * 100
                sys.stdout.write(f"\rProgress: {percent:.1f}% ({downloaded / (1024*1024):.1f}MB / {total_size / (1024*1024):.1f}MB)")
            else:
                sys.stdout.write(f"\rProgress: {downloaded / (1024*1024):.1f}MB downloaded")
            sys.stdout.flush()
    print("\nDownload complete.")

def extract_ffmpeg_binaries(zip_path, dest_dir):
    print(f"Extracting ffmpeg.exe and ffprobe.exe from {zip_path}...")
    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
        extracted_count = 0
        for file_info in zip_ref.infolist():
            filename = os.path.basename(file_info.filename)
            if filename in ['ffmpeg.exe', 'ffprobe.exe']:
                target_path = os.path.join(dest_dir, filename)
                print(f"Extracting: {file_info.filename} -> {filename}")
                with zip_ref.open(file_info) as source, open(target_path, 'wb') as target:
                    target.write(source.read())
                extracted_count += 1
        if extracted_count < 2:
            print("Warning: Could not find both ffmpeg.exe and ffprobe.exe in the zip archive.")
        else:
            print("FFmpeg binaries extracted successfully.")

def install_packages():
    packages = ['flask', 'flask-cors', 'noisereduce', 'scipy', 'numpy']
    print(f"Installing Python packages: {', '.join(packages)}...")
    try:
        subprocess.check_call([sys.executable, '-m', 'pip', 'install', '--upgrade'] + packages)
        print("Python packages installed successfully.")
    except Exception as e:
        print(f"Failed to install Python packages: {e}")
        sys.exit(1)

def main():
    print("==================================================")
    print("Setting up dependencies for Audio Noise Remover...")
    print("==================================================")
    
    # 1. Install pip packages
    install_packages()

    # 2. Download yt-dlp.exe
    ytdlp_path = os.path.join(BASE_DIR, 'yt-dlp.exe')
    if not os.path.exists(ytdlp_path):
        ytdlp_url = "https://github.com/yt-dlp/yt-dlp/releases/latest/download/yt-dlp.exe"
        try:
            download_file(ytdlp_url, ytdlp_path)
        except Exception as e:
            print(f"Failed to download yt-dlp.exe: {e}")
            sys.exit(1)
    else:
        print("yt-dlp.exe already exists. Skipping download.")

    # 3. Download FFmpeg ZIP and extract binaries
    ffmpeg_exe_path = os.path.join(BASE_DIR, 'ffmpeg.exe')
    ffprobe_exe_path = os.path.join(BASE_DIR, 'ffprobe.exe')
    
    if not os.path.exists(ffmpeg_exe_path) or not os.path.exists(ffprobe_exe_path):
        ffmpeg_zip_path = os.path.join(BASE_DIR, 'ffmpeg-essentials.zip')
        ffmpeg_url = "https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-essentials.zip"
        try:
            download_file(ffmpeg_url, ffmpeg_zip_path)
            extract_ffmpeg_binaries(ffmpeg_zip_path, BASE_DIR)
            # Clean up ZIP file
            if os.path.exists(ffmpeg_zip_path):
                os.remove(ffmpeg_zip_path)
                print("Cleaned up ffmpeg-essentials.zip.")
        except Exception as e:
            print(f"Failed to set up FFmpeg: {e}")
            if os.path.exists(ffmpeg_zip_path):
                os.remove(ffmpeg_zip_path)
            sys.exit(1)
    else:
        print("ffmpeg.exe and ffprobe.exe already exist. Skipping download.")

    print("\nAll dependencies configured successfully! You can now start the application.")

if __name__ == '__main__':
    main()
