const uploadForm = document.getElementById('upload-form');
const fileInput = document.getElementById('file-input');
const uploadStatus = document.getElementById('upload-status');
const documentList = document.getElementById('document-list');
const queryInput = document.getElementById('query-input');
const queryBtn = document.getElementById('query-btn');
const answerSection = document.getElementById('answer-section');
const answerText = document.getElementById('answer-text');
const sourcesList = document.getElementById('sources-list');
const loadingIndicator = document.getElementById('loading');
const queryHistoryList = document.getElementById('query-history');

// Dummy search bar for theme only
const searchForm = document.getElementById('search-form');
if (searchForm) searchForm.addEventListener('submit', e => { e.preventDefault(); alert("Use the ask question box for searching your documents!"); });

const API_BASE = '/api';

window.onload = () => {
  fetchDocuments();
  fetchQueryHistory();
};

uploadForm.addEventListener('submit', async (event) => {
  event.preventDefault();
  uploadStatus.style.color = '#e75480';
  const file = fileInput.files[0];
  if (!file) {
    uploadStatus.textContent = 'Please select a PDF file.';
    return;
  }
  if (file.type !== 'application/pdf') {
    uploadStatus.textContent = 'Invalid type: only PDF files are allowed!';
    return;
  }
  uploadStatus.textContent = 'Uploading...';

  const formData = new FormData();
  formData.append('file', file);

  try {
    const response = await fetch(`${API_BASE}/documents/upload`, {
      method: 'POST',
      body: formData,
    });

    if (!response.ok) {
      const error = await response.json();
      uploadStatus.textContent = `Error: ${error.detail || 'Upload failed'}`;
      return;
    }
    uploadStatus.style.color = '#21c36b';
    uploadStatus.textContent = 'Upload complete!';
    fileInput.value = '';
    fetchDocuments();
  } catch (error) {
    uploadStatus.textContent = `Error: ${error.message}`;
  }
});

async function fetchDocuments() {
  documentList.innerHTML = '<li style="color:#aaa;">Loading...</li>';
  try {
    const response = await fetch(`${API_BASE}/documents/`);
    const data = await response.json();
    if (!data.length) {
      documentList.innerHTML = '<li style="color:#bbb;">No documents yet.</li>';
      return;
    }
    documentList.innerHTML = '';
    data.forEach(doc => {
      const li = document.createElement('li');
      li.innerHTML = `<b>${doc.filename}</b> <span style="color:#666;font-size:.95em;">(${new Date(doc.upload_time).toLocaleString()})</span>`;
      documentList.appendChild(li);
    });
  } catch (error) {
    documentList.innerHTML = `<li style="color:#c0392b;">Unable to load docs: ${error.message}</li>`;
  }
}

queryBtn.addEventListener('click', async () => {
  const question = queryInput.value.trim();
  if (!question) {
    alert('Please enter your question!');
    queryInput.focus();
    return;
  }

  loadingIndicator.hidden = false;
  answerSection.hidden = true;
  answerText.textContent = '';
  sourcesList.innerHTML = '';

  try {
    const response = await fetch(`${API_BASE}/query/`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ question }),
    });

    if (!response.ok) {
      const error = await response.json();
      alert(`Error: ${error.detail || 'Query failed'}`);
      loadingIndicator.hidden = true;
      return;
    }

    const result = await response.json();
    answerText.textContent = result.answer || "(No answer)";
    sourcesList.innerHTML = '';
    if (result.sources.length === 0) {
      sourcesList.innerHTML = "<li style='color:#aaa;'>No source snippets found.</li>";
    }
    result.sources.forEach(src => {
      const li = document.createElement('li');
      li.innerHTML = `<span style="color:#2196f3;">Doc: ${src.document_id} / Chunk ${src.chunk_index}</span>
        <div style="background:#fce3f5; border-radius:7px; padding:6px; margin:5px 0 0 0; color:#121;">${src.text}</div>`;
      sourcesList.appendChild(li);
    });

    answerSection.hidden = false;
    queryInput.value = '';
    fetchQueryHistory();
  } catch (error) {
    alert(`Error: ${error.message}`);
  } finally {
    loadingIndicator.hidden = true;
  }
});

async function fetchQueryHistory() {
  queryHistoryList.innerHTML = '<li style="color:#999;">Loading...</li>';
  try {
    const response = await fetch(`/api/query/history`);
    const data = await response.json();
    if (!data.queries || !data.queries.length) {
      queryHistoryList.innerHTML = '<li style="color:#bbb;">No queries yet.</li>';
      return;
    }
    queryHistoryList.innerHTML = '';
    data.queries.slice(-10).reverse().forEach(item => {
      const li = document.createElement('li');
      li.innerHTML = `<span style="color:#3a155b;">${new Date(item.timestamp * 1000).toLocaleString()}:</span>
        <span style="color:#5a2b6a;">${item.question}</span>`;
      queryHistoryList.appendChild(li);
    });
  } catch (error) {
    queryHistoryList.innerHTML = `<li style="color:#c0392b;">Error loading history: ${error.message}</li>`;
  }
}
