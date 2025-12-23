const recordBtn = document.getElementById('record-btn');
const stopBtn = document.getElementById('stop-btn');
const generateBtn = document.getElementById('generate-btn');
const recordStatus = document.getElementById('record-status');
const progressArea = document.getElementById('progress-area');
const storyViewer = document.getElementById('story-viewer');
const storiesList = document.getElementById('stories-list');
const panelTemplate = document.getElementById('panel-template');

let mediaRecorder = null;
let recordedChunks = [];
let recordedBlob = null;

async function fetchStories() {
  const response = await fetch('/api/stories');
  if (!response.ok) {
    return;
  }
  const stories = await response.json();
  renderStories(stories);
}

function renderStories(stories) {
  storiesList.innerHTML = '';
  if (stories.length === 0) {
    storiesList.innerHTML = '<li class="empty">No stories yet. Record one!</li>';
    return;
  }
  stories.forEach((story) => {
    const item = document.createElement('li');
    item.className = 'story-item';
    item.innerHTML = `
      <button class="story-button">
        <span class="story-title">${story.title}</span>
        <span class="story-date">${new Date(story.created_at).toLocaleString()}</span>
      </button>
    `;
    item.querySelector('button').addEventListener('click', () => loadStory(story.id));
    storiesList.appendChild(item);
  });
}

async function loadStory(id) {
  const response = await fetch(`/api/stories/${id}`);
  if (!response.ok) {
    return;
  }
  const story = await response.json();
  renderStory(story, { instant: true });
}

function renderStory(story, { instant }) {
  storyViewer.innerHTML = '';
  const header = document.createElement('div');
  header.className = 'viewer-header';
  header.innerHTML = `
    <h3>${story.title}</h3>
    <audio controls src="${story.audio_url}"></audio>
    <p class="transcript">${story.transcript}</p>
  `;
  storyViewer.appendChild(header);

  const panelsWrapper = document.createElement('div');
  panelsWrapper.className = 'panels-wrapper';
  storyViewer.appendChild(panelsWrapper);

  story.panels.forEach((panel, index) => {
    const clone = panelTemplate.content.cloneNode(true);
    const img = clone.querySelector('img');
    const caption = clone.querySelector('.caption');
    img.src = panel.image_url;
    caption.textContent = panel.caption_text;
    const node = clone.firstElementChild;
    if (!instant) {
      node.classList.add('hidden');
      setTimeout(() => {
        node.classList.remove('hidden');
      }, 700 * index);
    }
    panelsWrapper.appendChild(node);
  });
}

recordBtn.addEventListener('click', async () => {
  recordedChunks = [];
  recordedBlob = null;
  recordStatus.textContent = 'Requesting microphone…';

  const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
  mediaRecorder = new MediaRecorder(stream);
  mediaRecorder.ondataavailable = (event) => {
    if (event.data.size > 0) {
      recordedChunks.push(event.data);
    }
  };
  mediaRecorder.onstop = () => {
    recordedBlob = new Blob(recordedChunks, { type: 'audio/webm' });
    recordStatus.textContent = 'Recording saved! Ready to generate.';
    generateBtn.disabled = false;
  };
  mediaRecorder.start();
  recordStatus.textContent = 'Recording…';
  recordBtn.disabled = true;
  stopBtn.disabled = false;
});

stopBtn.addEventListener('click', () => {
  if (!mediaRecorder) {
    return;
  }
  mediaRecorder.stop();
  mediaRecorder.stream.getTracks().forEach((track) => track.stop());
  recordBtn.disabled = false;
  stopBtn.disabled = true;
});

generateBtn.addEventListener('click', async () => {
  if (!recordedBlob) {
    return;
  }
  progressArea.textContent = 'Uploading audio and generating panels…';
  generateBtn.disabled = true;

  const formData = new FormData();
  formData.append('audio', recordedBlob, 'story.webm');

  const response = await fetch('/api/stories', {
    method: 'POST',
    body: formData,
  });

  if (!response.ok) {
    progressArea.textContent = 'Oops! Something went wrong.';
    return;
  }

  const story = await response.json();
  progressArea.textContent = 'Panels ready!';
  renderStory(story, { instant: false });
  fetchStories();
});

fetchStories();
