// Global variables
let languageData = {};
let currentVideoId = '';

// DOM elements
const videoUrlInput = document.getElementById('videoUrl');
const analyzeBtn = document.getElementById('analyzeBtn');
const languageSection = document.getElementById('languageSection');
const languageSelect = document.getElementById('languageSelect');
const summarizeBtn = document.getElementById('summarizeBtn');
const videoPreview = document.getElementById('videoPreview');
const videoThumbnail = document.getElementById('videoThumbnail');
const videoLink = document.getElementById('videoLink');
const resultsSection = document.getElementById('resultsSection');
const summaryContent = document.getElementById('summaryContent');
const transcriptContent = document.getElementById('transcriptContent');
const errorMessage = document.getElementById('errorMessage');
const errorText = document.getElementById('errorText');
const loadingOverlay = document.getElementById('loadingOverlay');
const loadingText = document.getElementById('loadingText');
const downloadSummary = document.getElementById('downloadSummary');
const downloadTranscript = document.getElementById('downloadTranscript');

// Event listeners
analyzeBtn.addEventListener('click', analyzeVideo);
summarizeBtn.addEventListener('click', generateSummary);
videoUrlInput.addEventListener('keypress', function (e) {
    if (e.key === 'Enter') {
        analyzeVideo();
    }
});

// Show loading overlay
function showLoading(text = 'Processing...') {
    loadingText.textContent = text;
    loadingOverlay.classList.remove('hidden');
}

// Hide loading overlay
function hideLoading() {
    loadingOverlay.classList.add('hidden');
}

// Show error message
function showError(message) {
    errorText.textContent = message;
    errorMessage.classList.remove('hidden');
    setTimeout(() => {
        errorMessage.classList.add('hidden');
    }, 5000);
}

// Hide all sections
function hideAllSections() {
    languageSection.classList.add('hidden');
    videoPreview.classList.add('hidden');
    resultsSection.classList.add('hidden');
    errorMessage.classList.add('hidden');
}

// Analyze video function
async function analyzeVideo() {
    const videoUrl = videoUrlInput.value.trim();

    if (!videoUrl) {
        showError('Please enter a YouTube URL');
        return;
    }

    if (!isValidYouTubeUrl(videoUrl)) {
        showError('Please enter a valid YouTube URL');
        return;
    }

    hideAllSections();
    showLoading('Analyzing video...');

    try {
        const response = await fetch('/get_languages', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ video_url: videoUrl })
        });

        const data = await response.json();

        if (data.success) {
            // Store language data
            languageData = data.language_dict;
            currentVideoId = data.video_id;

            // Populate language dropdown
            languageSelect.innerHTML = '<option value="">Choose language...</option>';
            data.languages.forEach(lang => {
                const option = document.createElement('option');
                option.value = lang;
                option.textContent = lang;
                languageSelect.appendChild(option);
            });

            // Show video preview
            videoThumbnail.src = `https://img.youtube.com/vi/${currentVideoId}/0.jpg`;
            videoLink.href = `https://www.youtube.com/watch?v=${currentVideoId}`;
            videoPreview.classList.remove('hidden');

            // Show language section
            languageSection.classList.remove('hidden');
        } else {
            showError(data.error || 'Failed to analyze video');
        }
    } catch (error) {
        showError('Network error. Please try again.');
        console.error('Error:', error);
    } finally {
        hideLoading();
    }
}

// Generate summary function
async function generateSummary() {
    const selectedLanguage = languageSelect.value;
    const videoUrl = videoUrlInput.value.trim();

    if (!selectedLanguage) {
        showError('Please select a language');
        return;
    }

    showLoading('Generating summary...');

    try {
        const response = await fetch('/generate_summary', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                video_url: videoUrl,
                language: selectedLanguage,
                language_dict: languageData
            })
        });

        const data = await response.json();

        if (data.success) {
            // Display results
            summaryContent.textContent = data.summary;
            transcriptContent.textContent = data.transcript;

            // Setup download buttons
            setupDownloadButtons(data.summary, data.transcript, data.video_id);

            // Show results
            resultsSection.classList.remove('hidden');
        } else {
            showError(data.error || 'Failed to generate summary');
        }
    } catch (error) {
        showError('Network error. Please try again.');
        console.error('Error:', error);
    } finally {
        hideLoading();
    }
}

// Setup download buttons
function setupDownloadButtons(summary, transcript, videoId) {
    downloadSummary.onclick = () => downloadText(summary, `summary_${videoId}.txt`);
    downloadTranscript.onclick = () => downloadText(transcript, `transcript_${videoId}.txt`);
}

// Download text as file
function downloadText(text, filename) {
    const blob = new Blob([text], { type: 'text/plain' });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    window.URL.revokeObjectURL(url);
}

// Validate YouTube URL
function isValidYouTubeUrl(url) {
    const patterns = [
        /^https?:\/\/(www\.)?youtube\.com\/watch\?v=[\w-]+/,
        /^https?:\/\/youtu\.be\/[\w-]+/,
        /^https?:\/\/(www\.)?youtube\.com\/embed\/[\w-]+/,
        /^https?:\/\/(www\.)?youtube\.com\/v\/[\w-]+/
    ];

    return patterns.some(pattern => pattern.test(url));
}