async function processVideo() {
  const url    = document.getElementById('yt-url').value.trim();
  const status = document.getElementById('status');
  const link   = document.getElementById('download-link');

  if (!url) {
    status.textContent = '⚠ Please paste a YouTube URL first.';
    return;
  }

  status.textContent = '⏳ Processing... this may take 1-2 minutes. Please wait.';
  link.hidden = true;

  try {
    const res = await fetch('http://127.0.0.1:5000/process', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ url })
    });

    if (!res.ok) {
      status.textContent = '❌ Something went wrong. Check your terminal for errors.';
      return;
    }

    const blob = await res.blob();
    link.href = URL.createObjectURL(blob);
    link.download = 'clean_video.mp4';
    link.hidden = false;
    status.textContent = '✅ Done! Your clean video is ready.';

  } catch (e) {
    status.textContent = '❌ Cannot connect to backend. Make sure app.py is running.';
  }
}
async function processFile() {
  const file   = document.getElementById('file-input').files[0];
  const status = document.getElementById('status');
  const link   = document.getElementById('download-link');

  if (!file) return;

  status.textContent = '⏳ Processing... please wait.';
  link.hidden = true;

  const formData = new FormData();
  formData.append('file', file);

  try {
    const res = await fetch('http://127.0.0.1:5000/process-file', {
      method: 'POST',
      body: formData
    });

    if (!res.ok) {
      status.textContent = '❌ Something went wrong.';
      return;
    }

    const blob = await res.blob();
    link.href = URL.createObjectURL(blob);
    link.download = 'clean_file';
    link.hidden = false;
    status.textContent = '✅ Done! Your clean file is ready.';

  } catch (e) {
    status.textContent = '❌ Cannot connect to backend.';
  }
}
  }
}
