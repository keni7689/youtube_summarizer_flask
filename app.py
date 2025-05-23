from flask import Flask, render_template, request, jsonify
import os
import time
import random

# Add delays between requests
def add_request_delay():
    time.sleep(random.uniform(2, 5))
    
from utils.youtube_utils import (
    extract_languages, 
    extract_transcript, 
    generate_summary_with_huggingface,
    parse_youtube_url
)

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/get_languages', methods=['POST'])
def get_languages():
    try:
        data = request.get_json()
        video_url = data.get('video_url')
        
        if not video_url:
            return jsonify({'error': 'No video URL provided'}), 400
        
        # Extract video ID
        video_id = parse_youtube_url(video_url)
        
        # Get available languages
        language_list, language_dict = extract_languages(video_id)
        
        return jsonify({
            'success': True,
            'languages': language_list,
            'language_dict': language_dict,
            'video_id': video_id
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/generate_summary', methods=['POST'])
def generate_summary():
    try:
        data = request.get_json()
        video_url = data.get('video_url')
        selected_language = data.get('language')
        language_dict = data.get('language_dict')
        
        if not all([video_url, selected_language, language_dict]):
            return jsonify({'error': 'Missing required parameters'}), 400
        
        # Extract video ID
        video_id = parse_youtube_url(video_url)
        
        # Get language code
        language_code = language_dict.get(selected_language)
        if not language_code:
            return jsonify({'error': 'Invalid language selection'}), 400
        
        # Extract transcript
        transcript = extract_transcript(video_id, language_code)
        if not transcript:
            return jsonify({'error': 'Failed to extract transcript'}), 500
        
        # Generate summary
        summary = generate_summary_with_huggingface(transcript)
        if not summary:
            return jsonify({'error': 'Failed to generate summary'}), 500
        
        return jsonify({
            'success': True,
            'summary': summary,
            'transcript': transcript,
            'video_id': video_id
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    # Get port from environment variable (for deployment) or default to 5000
    port = int(os.environ.get('PORT', 5000))
    # For production deployment
    app.run(host='0.0.0.0', port=port, debug=False)