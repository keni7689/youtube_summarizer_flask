import langcodes
from youtube_transcript_api import YouTubeTranscriptApi
import requests
import time

def extract_languages(video_id):
    """Extract available transcript languages for a YouTube video"""
    try:
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
        raise Exception(f"Error extracting languages: {str(e)}")

def extract_transcript(video_id, language):
    """Extract transcript for a YouTube video in specified language"""
    try:
        # Request Transcript for YouTube Video using API
        transcript_content = YouTubeTranscriptApi.get_transcript(video_id=video_id, languages=[language])
    
        # Extract Transcript Content from JSON Response and Join to Single Response
        transcript = ' '.join([i['text'] for i in transcript_content])

        return transcript
    
    except Exception as e:
        raise Exception(f"Error extracting transcript: {str(e)}")

def generate_summary_with_huggingface(transcript_text):
    """Generate summary using Hugging Face API"""
    # Replace with your actual API key
    API_KEY = "Your_API_KEY"
    
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
            }
        }
        
        # Make the API request
        response = requests.post(API_URL, headers=headers, json=payload)
        
        # Check if model is loading
        if response.status_code == 503:
            time.sleep(10)  # Wait for model to load
            response = requests.post(API_URL, headers=headers, json=payload)
        
        # Process the response
        if response.status_code == 200:
            result = response.json()
            summary = result[0]["summary_text"]
            return summary
        else:
            return fallback_summarization(transcript_text)
    
    except Exception as e:
        return fallback_summarization(transcript_text)

def fallback_summarization(text):
    """Simple extractive summarization as fallback"""
    sentences = text.split('. ')
    importance = {}
    
    # Simple frequency-based importance
    for i, sentence in enumerate(sentences):
        words = sentence.lower().split()
        importance[i] = len(set(words))
    
    # Get top sentences (about 20% of the original)
    top_sentences = sorted(importance.items(), key=lambda x: x[1], reverse=True)[:max(3, len(sentences)//5)]
    top_sentences = sorted(top_sentences, key=lambda x: x[0])  # Sort by original order
    
    summary = '. '.join([sentences[i] for i, _ in top_sentences]) + '.'
    
    return "Summary (generated locally):\n\n" + summary

def parse_youtube_url(url):
    """Extract video ID from different YouTube URL formats"""
    try:
        if "youtube.com/watch" in url:
            # Regular youtube.com/watch?v=VIDEO_ID format
            if "v=" in url:
                video_id = url.split("v=")[1].split("&")[0]
            else:
                raise ValueError("Invalid YouTube URL format")
        elif "youtu.be" in url:
            # Short youtu.be/VIDEO_ID format
            video_id = url.split("/")[-1].split("?")[0]
        elif "youtube.com/embed" in url:
            # Embed format
            video_id = url.split("/")[-1].split("?")[0]
        elif "youtube.com/v" in url:
            # Old v format
            video_id = url.split("/")[-1].split("?")[0]
        else:
            raise ValueError("Unrecognized YouTube URL format")
        
        return video_id
    except Exception as e:
        raise ValueError(f"Could not extract video ID: {e}")