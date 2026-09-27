let mediaRecorder = null;
let audioChunks = [];
let activeButton = null;
let activeField = null;
let speechRecognition = null;

let recognitionEngine = localStorage.getItem('recognitionEngine') || 'yandex';

function setEngine(engine) {
  recognitionEngine = engine;
  document.querySelectorAll('.engine-btn').forEach(btn => btn.classList.remove('active'));
  const btn = document.getElementById('btn-' + engine);
  if (btn) btn.classList.add('active');
  localStorage.setItem('recognitionEngine', engine);
}

function showStatus(msg) {
  const el = document.getElementById('voice-status');
  if (el) { el.textContent = msg; el.style.display = 'block'; }
}
function hideStatus() {
  const el = document.getElementById('voice-status');
  if (el) el.style.display = 'none';
}

function startWebSpeech(fieldId, btn) {
  const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
  if (!SpeechRecognition) return false;

  if (speechRecognition) {
    speechRecognition.stop();
    return true;
  }

  speechRecognition = new SpeechRecognition();
  speechRecognition.lang = 'ru-RU';
  speechRecognition.continuous = false;
  speechRecognition.interimResults = false;
  speechRecognition.maxAlternatives = 1;

  btn.classList.add('recording');
  btn.textContent = '⏹';
  showStatus('🎤 Говорите...');

  speechRecognition.onresult = (event) => {
    const text = event.results[0][0].transcript;
    const textarea = document.getElementById(fieldId);
    if (textarea) {
      textarea.value = (textarea.value ? textarea.value + ' ' : '') + text;
    }
    hideStatus();
    btn.classList.remove('recording');
    btn.textContent = '🎤';
    speechRecognition = null;
  };

  speechRecognition.onerror = (event) => {
    hideStatus();
    btn.classList.remove('recording');
    btn.textContent = '🎤';
    speechRecognition = null;
    if (event.error !== 'aborted' && event.error !== 'no-speech') {
      alert('Ошибка: ' + event.error);
    }
  };

  speechRecognition.onend = () => {
    btn.classList.remove('recording');
    btn.textContent = '🎤';
    speechRecognition = null;
    hideStatus();
  };

  speechRecognition.start();
  return true;
}

async function startVoice(fieldId, btn) {
  if (mediaRecorder && mediaRecorder.state === 'recording') {
    mediaRecorder.stop();
    return;
  }
  if (speechRecognition) {
    speechRecognition.stop();
    return;
  }

  if (startWebSpeech(fieldId, btn)) return;

  if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
    alert('Откройте сайт по HTTPS для записи голоса.');
    return;
  }

  try {
    const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
    audioChunks = [];
    activeButton = btn;
    activeField = fieldId;
    const mimeType = 'audio/webm;codecs=opus';
    mediaRecorder = new MediaRecorder(stream, { mimeType, audioBitsPerSecond: 24000 });
    mediaRecorder.ondataavailable = e => { if (e.data.size > 0) audioChunks.push(e.data); };
    mediaRecorder.onstop = async () => {
      stream.getTracks().forEach(t => t.stop());
      btn.classList.remove('recording');
      btn.textContent = '🎤';
      showStatus('⏳ Распознаю...');
      const blob = new Blob(audioChunks, { type: mimeType });
      const formData = new FormData();
      formData.append('file', blob, 'audio.webm');
      const endpoint = recognitionEngine === 'whisper' ? '/api/whisper/recognize' : '/api/speech/recognize';
      try {
        const resp = await fetch(endpoint, { method: 'POST', body: formData });
        if (!resp.ok) { const err = await resp.json(); hideStatus(); alert('Ошибка: ' + (err.detail || '?')); return; }
        const data = await resp.json();
        const textarea = document.getElementById(activeField);
        if (textarea && data.text) textarea.value = (textarea.value ? textarea.value + ' ' : '') + data.text;
        hideStatus();
      } catch(e) { hideStatus(); alert('Ошибка сети: ' + e.message); }
      mediaRecorder = null;
    };
    mediaRecorder.start();
    btn.classList.add('recording');
    btn.textContent = '⏹';
    showStatus('🎤 Запись...');
  } catch(e) {
    alert('Нет доступа к микрофону: ' + e.message);
  }
}
