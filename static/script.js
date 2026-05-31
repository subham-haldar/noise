// Extract YouTube video ID
function getYouTubeId(url) {
  const regExp = /^.*(youtu.be\/|v\/|u\/\w\/|embed\/|watch\?v=|\&v=)([^#\&\?]*).*/;
  const match = url.match(regExp);
  return (match && match[2].length === 11) ? match[2] : null;
}

// Preview element nodes
const urlInput = document.getElementById('yt-url');
const previewContainer = document.getElementById('preview-container');
const videoThumbnail = document.getElementById('video-thumbnail');
const loaderContainer = document.getElementById('loader-container');
const loaderStatus = document.getElementById('loader-status');
const downloadCard = document.getElementById('download-card');
const downloadLink = document.getElementById('download-link');
const statusMsg = document.getElementById('status');
const buttonsDiv = document.querySelector('.buttons');
const inputRow = document.querySelector('.input-row');

// Monitor URL input changes to show the preview card
urlInput.addEventListener('input', () => {
  const url = urlInput.value.trim();
  const videoId = getYouTubeId(url);
  
  if (videoId) {
    videoThumbnail.src = `https://img.youtube.com/vi/${videoId}/hqdefault.jpg`;
    previewContainer.style.display = 'block'; // Make sure it shows
  } else {
    previewContainer.style.display = 'none';
  }
});

async function processVideo() {
  const url = urlInput.value.trim();
  const videoId = getYouTubeId(url);

  if (!url) {
    showStatus('⚠ Please paste a YouTube URL first.', 'error');
    return;
  }

  // Set visual states
  showStatus('', '');
  inputRow.style.display = 'none';
  buttonsDiv.style.display = 'none';
  loaderContainer.style.display = 'flex';
  downloadCard.style.display = 'none';

  // Dynamic status rotation
  const statuses = [
    '⏳ Fetching YouTube video information...',
    '📥 Downloading video stream (may take up to a minute)...',
    '⚡ Splitting audio stream from video tracks...',
    '🧠 Running AI noisereduce models on audio...',
    '🎵 Enhancing vocal frequencies & acoustics...',
    '🎬 Remuxing high-quality video and clean audio...',
    '✨ Packaging output file...'
  ];
  let statusIdx = 0;
  loaderStatus.textContent = statuses[statusIdx];
  const interval = setInterval(() => {
    if (statusIdx < statuses.length - 1) {
      statusIdx++;
      loaderStatus.textContent = statuses[statusIdx];
    }
  }, 10000); // cycle status every 10s

  try {
    const res = await fetch('/process', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ url })
    });

    clearInterval(interval);

    if (!res.ok) {
      const errData = await res.json().catch(() => ({}));
      const errMsg = errData.error || 'Something went wrong during processing.';
      throw new Error(errMsg);
    }

    const blob = await res.blob();
    const downloadUrl = URL.createObjectURL(blob);
    
    // Configure download link
    downloadLink.href = downloadUrl;
    downloadLink.download = 'clean_video.mp4';
    
    // Show download card
    loaderContainer.style.display = 'none';
    downloadCard.style.display = 'block';
    
    showStatus('✅ Enhancement complete! Download your video below.', 'success');

  } catch (e) {
    clearInterval(interval);
    loaderContainer.style.display = 'none';
    inputRow.style.display = 'block';
    buttonsDiv.style.display = 'flex';
    showStatus(`❌ Error: ${e.message || 'Cannot connect to server. Check your network or backend logs.'}`, 'error');
  }
}

function resetForm() {
  urlInput.value = '';
  previewContainer.style.display = 'none';
  downloadCard.style.display = 'none';
  inputRow.style.display = 'block';
  buttonsDiv.style.display = 'flex';
  showStatus('', '');
}

function showStatus(text, type) {
  statusMsg.textContent = text;
  statusMsg.className = 'status-msg'; // clear previous styles
  if (type) {
    statusMsg.classList.add(type);
  }
}