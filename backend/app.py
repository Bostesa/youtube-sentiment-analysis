from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import pandas as pd
import numpy as np
from youtube_api.youtube_client import YouTubeClient
from youtube_api.url_parser import extract_video_id, extract_channel_info
from sentiment_analysis.model_loader import sentiment_analyzer
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)  # Enable CORS for frontend integration

# Create necessary directories
MODELS_DIR = os.path.join('sentiment_analysis', 'models')
os.makedirs(MODELS_DIR, exist_ok=True)

# Load sentiment model
model_loaded = sentiment_analyzer.load_model(MODELS_DIR)
if model_loaded:
    logger.info("Sentiment analysis model loaded successfully")
else:
    logger.warning("Sentiment analysis model not loaded, will attempt to load on first analysis")

@app.route('/api/status', methods=['GET'])
def status():
    return jsonify({
        'status': 'online',
        'model_loaded': sentiment_analyzer.model_loaded,
        'model_type': 'Advanced BERT' if sentiment_analyzer.model_loaded else 'Not loaded'
    })

@app.route('/api/trending', methods=['GET'])
def get_trending():
    """
    Fetch trending videos in real time using YouTubeClient.
    """
    region_code = request.args.get('regionCode', 'US')  # e.g. /api/trending?regionCode=US
    max_results = int(request.args.get('maxResults', 10))
    
    try:
        client = YouTubeClient()
        trending_videos = client.get_trending_videos(region_code=region_code, max_results=max_results)
        
        if not trending_videos:
            return jsonify({
                'message': 'No trending videos found or an error occurred'
            }), 404
        
        return jsonify({
            'regionCode': region_code,
            'trending_videos': trending_videos
        })
    
    except Exception as e:
        logger.error(f"Error in /api/trending: {str(e)}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/analyze/video', methods=['POST'])
def analyze_video():
    data = request.json
    if not data or 'videoId' not in data:
        return jsonify({'error': 'No video ID provided'}), 400
    
    try:
        # Extract video ID from URL if necessary
        video_id = extract_video_id(data['videoId'])
        if not video_id:
            return jsonify({'error': 'Invalid video ID or URL provided'}), 400
            
        logger.info(f"Analyzing video: {video_id}")
        
        # Initialize YouTube client
        client = YouTubeClient()
        
        # Get comments for the video
        response = client.get_video_comments(video_id)
        if not response or not response[0]['comments']:
            return jsonify({
                'videoId': video_id,
                'error': 'No comments found or comments are disabled for this video'
            }), 404
        
        # Extract just the comment text
        comments = [item['comment'] for item in response[0]['comments']]
        
        # Analyze sentiment
        results, sentiment_counts = sentiment_analyzer.analyze_comments(comments)
        
        return jsonify({
            'videoId': video_id,
            'comment_count': len(comments),
            'sentiment_distribution': sentiment_counts,
            'results': results
        })
            
    except Exception as e:
        logger.error(f"Error in analyze_video: {str(e)}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/analyze/channel', methods=['POST'])
def analyze_channel():
    data = request.json
    
    if not data:
        return jsonify({'error': 'No data provided'}), 400
    
    if 'channelId' not in data and 'username' not in data:
        return jsonify({'error': 'No channel ID or username provided'}), 400
    
    try:
        # Initialize YouTube client
        client = YouTubeClient()
        
        channel_id = data.get('channelId')
        username = data.get('username')
        
        # Handle URL or ID extraction
        if channel_id:
            channel_type, channel_value = extract_channel_info(channel_id)
            if channel_type == 'id':
                channel_id = channel_value
            else:
                username = channel_value
                channel_id = None
        
        # If we have a username but no channel ID, fetch the channel ID
        if username and not channel_id:
            channel_id = client.get_channel_id_from_username(username)
            if not channel_id:
                return jsonify({'error': f"Could not find channel ID for username: {username}"}), 404
        
        logger.info(f"Analyzing channel: {channel_id}")
        
        # Get channel info
        channel_info = client.get_channel_info(channel_id)
        if not channel_info:
            return jsonify({'error': f"Could not retrieve channel information for ID: {channel_id}"}), 404
        
        # Get videos from the channel
        max_results = int(data.get('maxResults', 10))
        videos = client.get_channel_videos(channel_id, max_results=max_results)
        if not videos:
            return jsonify({
                'channelInfo': channel_info,
                'error': 'No videos found for this channel'
            }), 404
        
        # Limit how many videos to analyze for comments
        video_limit = min(max_results, len(videos))
        video_ids = [v['videoId'] for v in videos[:video_limit]]
        
        comments_data = []
        total_comments = 0
        total_sentiment = {'positive': 0, 'negative': 0, 'neutral': 0}
        
        for vid in video_ids:
            video_comments = client.get_video_comments(vid, max_results=50)
            if video_comments and video_comments[0]['comments']:
                comments = [c['comment'] for c in video_comments[0]['comments']]
                results, sentiment_counts = sentiment_analyzer.analyze_comments(comments)
                
                # Aggregate
                total_comments += len(comments)
                for sentiment, count in sentiment_counts.items():
                    total_sentiment[sentiment] += count
                
                # Grab the relevant video info
                vid_info = next((x for x in videos if x['videoId'] == vid), None)
                title = vid_info['title'] if vid_info else "Unknown"
                
                comments_data.append({
                    'videoId': vid,
                    'title': title,
                    'commentCount': len(comments),
                    'sentiment': sentiment_counts,
                    'sentimentPercentages': {
                        s: round((c / len(comments)) * 100, 1) if len(comments) else 0 
                        for s, c in sentiment_counts.items()
                    }
                })
        
        # Calculate overall sentiment percentages
        overall_percentages = {
            s: round((c / total_comments) * 100, 1) if total_comments > 0 else 0 
            for s, c in total_sentiment.items()
        }
        
        return jsonify({
            'channelInfo': channel_info,
            'videoCount': len(videos),
            'analyzedVideos': len(comments_data),
            'totalComments': total_comments,
            'overallSentiment': total_sentiment,
            'overallSentimentPercentages': overall_percentages,
            'videos': videos[:video_limit],
            'videoAnalysis': comments_data
        })
            
    except Exception as e:
        logger.error(f"Error in analyze_channel: {str(e)}")
        return jsonify({'error': str(e)}), 500

def use_sample_trending_data():
    """Use sample trending data when real data is not available."""
    try:
        sample_path = os.path.join('scraper', 'output', 'sample_trending.csv')
        
        if not os.path.exists(sample_path):
            return jsonify({'error': 'No trending data available, sample file not found'}), 404
            
        df = pd.read_csv(sample_path)
        
        # Group by video_id to get unique videos
        video_data = df.groupby('video_id').first().reset_index()
        
        # Return trending videos information
        trending_videos = []
        for _, row in video_data.head(10).iterrows():
            video_id = row['video_id']
            if isinstance(video_id, str):
                video_id = video_id.strip('"')
                
            title = row.get('title', '')
            if isinstance(title, str):
                title = title.strip('"')
                
            channel_title = row.get('channelTitle', '')
            if isinstance(channel_title, str):
                channel_title = channel_title.strip('"')
            
            trending_videos.append({
                'videoId': video_id,
                'title': title,
                'channelTitle': channel_title,
                'viewCount': int(row.get('view_count', 0)),
                'commentCount': int(row.get('comment_count', 0))
            })
        
        return jsonify({
            'trending_videos': trending_videos,
            'note': 'Using sample trending data'
        })
        
    except Exception as e:
        logger.error(f"Error using sample trending data: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/run-scraper', methods=['POST'])
def run_scraper():
    try:
        from scraper.youtube_scraper import get_data
        
        # Get scraper parameters
        data = request.json or {}
        country_code = data.get('countryCode', 'US')
        
        # Set up the scraper
        api_key_path = os.path.join('scraper', 'api_key.txt')
        country_code_path = os.path.join('scraper', 'country_codes.txt')
        output_dir = os.path.join('scraper', 'output')
        
        os.makedirs(output_dir, exist_ok=True)
        
        # Write the country code to file
        with open(country_code_path, 'w') as f:
            f.write(country_code)
        
        # Check if API key exists
        if not os.path.exists(api_key_path):
            return jsonify({'error': 'YouTube API key not found. Please create scraper/api_key.txt file.'}), 400
            
        # Run the scraper
        results = get_data(api_key_path, country_code_path, output_dir)
        
        if results:
            return jsonify({
                'success': True,
                'message': f'Scraper completed successfully for country code: {country_code}',
                'files': results
            })
        else:
            return jsonify({
                'success': False,
                'message': 'Scraper ran but no data was obtained.'
            }), 500
        
    except Exception as e:
        logger.error(f"Error running scraper: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/train-model', methods=['POST'])
def train_model():
    """API endpoint to train the sentiment analysis model on demand."""
    try:
        from sentiment_analysis.advanced_model import train_model
        
        # Run the training process
        logger.info("Starting sentiment model training...")
        model_info = train_model()
        
        # Reload the model
        sentiment_analyzer.load_model()
        
        return jsonify({
            'success': True,
            'message': 'Sentiment analysis model trained successfully',
            'accuracy': model_info['metrics']['eval_accuracy']
        })
        
    except Exception as e:
        logger.error(f"Error training model: {str(e)}")
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    # Use environment variables for host and port if available
    host = os.environ.get('HOST', '0.0.0.0')
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('DEBUG', 'False').lower() == 'true'
    
    # Log server startup
    logger.info(f"Starting Flask server on {host}:{port} (debug={debug})")
    
    app.run(host=host, port=port, debug=debug)