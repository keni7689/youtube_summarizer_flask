import langcodes
from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api.formatters import TextFormatter
import requests
import time
import random
from urllib.parse import urlparse, parse_qs

def extract_languages(video_id):
    """Extract available transcript languages for a YouTube video"""
    try:
        # Add delay to avoid rate limiting
        time.sleep(random.uniform(1, 3))
        
        # Fetch the List of Available Transcripts for Given Video
        transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)

        # Extract the Language Codes from List
        available_transcripts = [i.language_code for i in transcript_list]

        # Convert Language_codes to Human-Readable Language_names
        language_list = list({langcodes.Language.get(i).display_name() for i in available_transcripts})

        # Create a Dictionary Mapping Language_names to Language_codes
        language_dict = {langcodes.Language.get(i).display_name():i for i in available_transcripts}

        return language_list, language_dict
    except Exception as e:
        # More specific error handling
        error_msg = str(e)
        if "Too Many Requests" in error_msg or "429" in error_msg:
            raise Exception("YouTube is temporarily blocking requests. Please try again in a few minutes, or try a different video.")
        elif "Transcript" in error_msg and "disabled" in error_msg:
            raise Exception("This video has transcripts disabled. Please try a different video.")
        elif "Video unavailable" in error_msg:
            raise Exception("Video not found or unavailable. Please check the URL.")
        else:
            raise Exception(f"Error accessing video: Please try a different video or wait a few minutes.")

def extract_transcript(video_id, language):
    """Extract transcript for a YouTube video in specified language"""
    try:
        # Add delay to avoid rate limiting
        time.sleep(random.uniform(1, 2))
        
        # Request Transcript for YouTube Video using API
        transcript_content = YouTubeTranscriptApi.get_transcript(
            video_id=video_id, 
            languages=[language]
        )
    
        # Extract Transcript Content from JSON Response and Join to Single Response
        transcript = ' '.join([i['text'] for i in transcript_content])

        return transcript
    
    except Exception as e:
        error_msg = str(e)
        if "Too Many Requests" in error_msg or "429" in error_msg:
            raise Exception("YouTube is temporarily blocking requests. Please try again in a few minutes.")
        elif "No transcripts" in error_msg:
            raise Exception("No transcript available in the selected language.")
        else:
            raise Exception(f"Error extracting transcript: {error_msg}")

def generate_summary_with_huggingface(transcript_text):
    """Generate summary using Hugging Face API with better error handling"""
    # Replace with your actual API key
    API_KEY = "Your_API_KEY"
    
    # If no API key, use fallback immediately
    if API_KEY == "Your_API_KEY" or not API_KEY:
        return fallback_summarization(transcript_text)
    
    try:
        # Use the Hugging Face Inference API with BART model for summarization
        API_URL = "https://api-inference.huggingface.co/models/facebook/bart-large-cnn"
        headers = {"Authorization": f"Bearer {API_KEY}"}
        
        # Truncate text if too long (BART model has token limits)
        max_length = 1024  # characters, approximate limit for better results
        if len(transcript_text) > max_length:
            transcript_text = transcript_text[:max_length]
            
        payload = {
            "inputs": transcript_text,
            "parameters": {
                "max_length": 500,
                "min_length": 100,
                "do_sample": False,
            }
        }
        
        # Make the API request with timeout
        response = requests.post(API_URL, headers=headers, json=payload, timeout=30)
        
        # Check if model is loading
        if response.status_code == 503:
            time.sleep(15)  # Wait longer for model to load
            response = requests.post(API_URL, headers=headers, json=payload, timeout=30)
        
        # Process the response
        if response.status_code == 200:
            result = response.json()
            if isinstance(result, list) and len(result) > 0 and "summary_text" in result[0]:
                summary = result[0]["summary_text"]
                return f"AI Summary:\n\n{summary}"
            else:
                return fallback_summarization(transcript_text)
        else:
            return fallback_summarization(transcript_text)
    
    except Exception as e:
        return fallback_summarization(transcript_text)

def fallback_summarization(text):
    """Improved extractive summarization as fallback"""
    try:
        sentences = [s.strip() for s in text.split('.') if s.strip()]
        
        if len(sentences) <= 3:
            return f"Summary (generated locally):\n\n{text}"
        
        # Calculate sentence importance based on length and word frequency
        word_freq = {}
        for sentence in sentences:
            words = sentence.lower().split()
            for word in words:
                if len(word) > 3:  # Skip short words
                    word_freq[word] = word_freq.get(word, 0) + 1
        
        # Score sentences
        sentence_scores = {}
        for i, sentence in enumerate(sentences):
            words = sentence.lower().split()
            score = 0
            for word in words:
                if word in word_freq:
                    score += word_freq[word]
            sentence_scores[i] = score / len(words) if words else 0
        
        # Get top sentences (about 25% of the original)
        num_sentences = max(3, len(sentences) // 4)
        top_sentences = sorted(sentence_scores.items(), key=lambda x: x[1], reverse=True)[:num_sentences]
        top_sentences = sorted(top_sentences, key=lambda x: x[0])  # Sort by original order
        
        summary = '. '.join([sentences[i] for i, _ in top_sentences]) + '.'
        
        return f"Summary (generated locally):\n\n{summary}"
    
    except Exception:
        return f"Summary (generated locally):\n\n{text[:500]}..."

def parse_youtube_url(url):
    """Extract video ID from different YouTube URL formats with better validation"""
    try:
        # Clean the URL
        url = url.strip()
        
        # Parse the URL
        parsed_url = urlparse(url)
        
        if "youtube.com" in parsed_url.netloc.lower():
            if "/watch" in parsed_url.path:
                # Regular youtube.com/watch?v=VIDEO_ID format
                query_params = parse_qs(parsed_url.query)
                if 'v' in query_params:
                    video_id = query_params['v'][0]
                else:
                    raise ValueError("No video ID found in URL")
            elif "/embed/" in parsed_url.path:
                # Embed format: youtube.com/embed/VIDEO_ID
                video_id = parsed_url.path.split("/embed/")[1].split("?")[0]
            elif "/v/" in parsed_url.path:
                # Old v format: youtube.com/v/VIDEO_ID
                video_id = parsed_url.path.split("/v/")[1].split("?")[0]
            else:
                raise ValueError("Unrecognized YouTube URL format")
                
        elif "youtu.be" in parsed_url.netloc.lower():
            # Short youtu.be/VIDEO_ID format
            video_id = parsed_url.path.lstrip("/").split("?")[0]
        else:
            raise ValueError("Not a valid YouTube URL")
        
        # Validate video ID format (YouTube video IDs are typically 11 characters)
        if not video_id or len(video_id) < 10:
            raise ValueError("Invalid video ID extracted")
            
        return video_id
        
    except Exception as e:
        raise ValueError(f"Could not extract video ID from URL. Please check the YouTube URL format.")