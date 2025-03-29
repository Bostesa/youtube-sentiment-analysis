import requests
import sys
import time
import os
import argparse
import certifi
import logging
import importlib.util
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Try to import sentiment_analyzer - handle gracefully if it's not available
try:
    # Import the sentiment analyzer using relative import path
    sentiment_module_path = Path(__file__).parent.parent / "sentiment_analysis" / "model_loader.py"
    spec = importlib.util.spec_from_file_location("model_loader", sentiment_module_path)
    model_loader = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(model_loader)
    sentiment_analyzer = model_loader.sentiment_analyzer
    has_sentiment_analyzer = True
    logger.info("Sentiment analyzer loaded successfully")
except Exception as e:
    logger.warning(f"Could not load sentiment analyzer: {e}")
    has_sentiment_analyzer = False

# List of simple to collect features
snippet_features = ["comment_id", "comment_text", "author", "comment_date", "title",
                    "publishedAt", "channelId", "channelTitle", "categoryId"]

# Any characters to exclude, generally these are things that become problematic in CSV files
unsafe_characters = ['\n', '"']

# Used to identify columns, currently hardcoded order
header = ["video_id"] + snippet_features + ["trending_date", "tags", "view_count", "likes", "dislikes",
                                            "comment_count", "thumbnail_link", "comments_disabled",
                                            "ratings_disabled", "description"]

def setup(api_path, code_path):
    try:
        with open(api_path, 'r') as file:
            api_key = file.readline().strip()
    except FileNotFoundError:
        logger.error(f"Error: The API key file was not found at {api_path}")
        return None, []

    try:
        with open(code_path) as file:
            country_codes = [x.strip() for x in file if x.strip()]
    except FileNotFoundError:
        logger.error(f"Error: The country codes file was not found at {code_path}")
        return api_key, ["US"]  # Default to US if no country codes file

    return api_key, country_codes

def prepare_feature(feature):
    # Removes any character from the unsafe characters list and surrounds the whole item in quotes
    for ch in unsafe_characters:
        feature = str(feature).replace(ch, "")
    return f'"{feature}"'

def get_tags(tags_list):
    # Takes a list of tags, prepares each tag and joins them into a string by the pipe character
    return prepare_feature("|".join(tags_list))

def api_request(page_token, country_code, api_key):
    # Builds the URL and requests the JSON from it
    popular_videos_url = f"https://www.googleapis.com/youtube/v3/videos?part=snippet,statistics&chart=mostPopular&regionCode={country_code}&maxResults=50&key={api_key}{page_token}"
    try:
        response = requests.get(popular_videos_url, verify=certifi.where())
        if response.status_code == 429:
            logger.error("Temp-Banned due to excess requests, please wait and continue later")
            return None
        if response.status_code != 200:
            logger.error(f"Error: Received status code {response.status_code}")
            logger.error(response.text)
            return None
        return response.json()
    except Exception as e:
        logger.error(f"Error in API request: {e}")
        return None

def api_request_comments(video_id, api_key, max_results=10):
    # Builds the URL and requests the JSON from it
    comments_url = f"https://www.googleapis.com/youtube/v3/commentThreads?part=snippet&videoId={video_id}&maxResults={max_results}&key={api_key}"
    try:
        response = requests.get(comments_url, verify=certifi.where())
        if response.status_code == 429:
            logger.error("Temp-Banned due to excess requests, please wait and continue later")
            return None
        if response.status_code == 403 and "commentsDisabled" in response.text:
            logger.warning(f"Comments are disabled for video ID {video_id}")
            return None
        if response.status_code != 200:
            logger.error(f"Error: Received status code {response.status_code}")
            logger.error(response.text)
            return None
        return response.json()
    except Exception as e:
        logger.error(f"Error in comments API request: {e}")
        return None

def fetch_popular_videos(items):
    video_details = []
    for video in items:
        video_id = video['id']
        snippet = video['snippet']
        statistics = video['statistics']
        
        trending_date = time.strftime('%y.%d.%m')
        tags = get_tags(snippet.get('tags', []))
        view_count = statistics.get('viewCount', 0)
        likes = statistics.get('likeCount', 0)
        dislikes = statistics.get('dislikeCount', 0)
        comment_count = statistics.get('commentCount', 0)
        thumbnail_link = snippet['thumbnails']['high']['url']
        comments_disabled = 'commentCount' not in statistics
        ratings_disabled = 'likeCount' not in statistics
        description = prepare_feature(snippet.get('description', ''))
        
        video_details.append({
            "video_id": prepare_feature(video_id),
            "title": prepare_feature(snippet.get('title', '')),
            "publishedAt": prepare_feature(snippet.get('publishedAt', '')),
            "channelId": prepare_feature(snippet.get('channelId', '')),
            "channelTitle": prepare_feature(snippet.get('channelTitle', '')),
            "categoryId": prepare_feature(snippet.get('categoryId', '')),
            "trending_date": trending_date,
            "tags": tags,
            "view_count": view_count,
            "likes": likes,
            "dislikes": dislikes,
            "comment_count": comment_count,
            "thumbnail_link": thumbnail_link,
            "comments_disabled": comments_disabled,
            "ratings_disabled": ratings_disabled,
            "description": description
        })
    
    return video_details

def fetch_and_process_comments(video_details, api_key):
    lines = []
    for video in video_details:
        video_id = video["video_id"].strip('"')
        
        if video["comments_disabled"]:
            logger.info(f"Comments are disabled for video {video_id}, skipping")
            continue
            
        logger.info(f"Fetching comments for video {video_id}")
        comments_data = api_request_comments(video_id, api_key)
        if not comments_data:
            continue
        
        comment_lines = []
        for comment in comments_data.get('items', []):
            snippet = comment['snippet']['topLevelComment']['snippet']
            comment_id = prepare_feature(comment['id'])
            comment_text = prepare_feature(snippet['textDisplay'])
            author = prepare_feature(snippet['authorDisplayName'])
            comment_date = prepare_feature(snippet['publishedAt'])

            line = [video_id, comment_id, comment_text, author, comment_date] + [
                str(video["title"]), str(video["publishedAt"]), str(video["channelId"]), str(video["channelTitle"]), str(video["categoryId"]),
                str(video["trending_date"]), str(video["tags"]), str(video["view_count"]), str(video["likes"]), str(video["dislikes"]),
                str(video["comment_count"]), str(video["thumbnail_link"]), str(video["comments_disabled"]),
                str(video["ratings_disabled"]), str(video["description"])
            ]
            comment_lines.append(",".join(line))
            if len(comment_lines) >= 10:  # limit to 10 comments per video
                break
        
        lines.extend(comment_lines)
        # Sleep to avoid hitting API rate limits
        time.sleep(0.5)
    
    return lines

def get_pages(country_code, api_key, max_videos=5, comments_per_video=5):
    """
    Get trending videos and their comments for a specific country.
    Limited to top 5 videos with top 5 comments each by default.
    """
    country_data = []
    next_page_token = "&"
    
    # Only need one page since we're just getting top 5 videos
    video_data_page = api_request(next_page_token, country_code, api_key)
    if not video_data_page:
        logger.error(f"Failed to get video data for country code {country_code}")
        return []
    
    # Get the items (trending videos)
    items = video_data_page.get('items', [])
    
    # Limit to the top max_videos (default 5)
    top_videos = items[:max_videos]
    
    logger.info(f"Got {len(top_videos)} trending videos for country {country_code}")
    
    # Process video details
    video_details = fetch_popular_videos(top_videos)
    
    # Get comments for each video, limited to comments_per_video per video
    for video in video_details:
        video_id = video["video_id"].strip('"')
        
        if video["comments_disabled"]:
            logger.info(f"Comments are disabled for video {video_id}, skipping")
            continue
            
        logger.info(f"Fetching top {comments_per_video} comments for video {video_id}")
        comments_data = api_request_comments(video_id, api_key, max_results=comments_per_video)
        
        if not comments_data or 'items' not in comments_data:
            logger.warning(f"No comments found for video {video_id}")
            continue
        
        for comment in comments_data.get('items', [])[:comments_per_video]:
            snippet = comment['snippet']['topLevelComment']['snippet']
            comment_id = prepare_feature(comment['id'])
            comment_text = prepare_feature(snippet['textDisplay'])
            author = prepare_feature(snippet['authorDisplayName'])
            comment_date = prepare_feature(snippet['publishedAt'])

            line = [video_id, comment_id, comment_text, author, comment_date] + [
                str(video["title"]), str(video["publishedAt"]), str(video["channelId"]), str(video["channelTitle"]), str(video["categoryId"]),
                str(video["trending_date"]), str(video["tags"]), str(video["view_count"]), str(video["likes"]), str(video["dislikes"]),
                str(video["comment_count"]), str(video["thumbnail_link"]), str(video["comments_disabled"]),
                str(video["ratings_disabled"]), str(video["description"])
            ]
            country_data.append(",".join(line))
    
    logger.info(f"Processed {len(country_data)} comment lines for {country_code}")
    return country_data

def write_to_file(country_code, country_data, output_dir):
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    file_path = os.path.join(output_dir, f"{time.strftime('%y.%d.%m')}_{country_code}_videos.csv")
    logger.info(f"Writing data to {file_path}")

    with open(file_path, "w+", encoding='utf-8') as file:
        for row in country_data:
            file.write(f"{row}\n")
    
    return file_path

def get_data(key_path='api_key.txt', country_code_path='country_codes.txt', output_dir='output/'):
    """
    Get trending videos data and save to output files.
    Limits to top 5 trending videos with top 5 comments each.
    
    Returns list of results including file paths and record counts.
    """
    api_key, country_codes = setup(key_path, country_code_path)
    
    if not api_key:
        logger.error("No API key found, cannot proceed with scraping")
        return None

    results = []
    for country_code in country_codes:
        logger.info(f"Processing country code: {country_code}")
        
        # Add the CSV header
        country_data = [",".join(header)]
        
        # Get top 5 trending videos with top 5 comments each
        pages_data = get_pages(country_code, api_key, max_videos=5, comments_per_video=5)
        
        if pages_data:
            country_data.extend(pages_data)
            # Write data to output file
            file_path = write_to_file(country_code, country_data, output_dir)
            
            # Try to apply sentiment analysis if available
            sentiment_results = None
            if has_sentiment_analyzer:
                try:
                    logger.info(f"Applying sentiment analysis for {len(pages_data)} comments")
                    # Extract comment text for sentiment analysis
                    comment_texts = []
                    for line in pages_data:
                        parts = line.split(',')
                        if len(parts) > 2:  # Make sure we have enough parts
                            comment_text = parts[2].strip('"')  # comment_text is at index 2
                            comment_texts.append(comment_text)
                    
                    # Run sentiment analysis
                    _, sentiment_counts = sentiment_analyzer.analyze_comments(comment_texts)
                    sentiment_results = sentiment_counts
                    
                    # Create a sentiment summary file
                    sentiment_file_path = os.path.join(output_dir, f"{time.strftime('%y.%d.%m')}_{country_code}_sentiment.txt")
                    with open(sentiment_file_path, "w+", encoding='utf-8') as f:
                        f.write(f"Sentiment Analysis for {country_code} Trending Videos\n")
                        f.write(f"Date: {time.strftime('%Y-%m-%d %H:%M:%S')}\n\n")
                        f.write(f"Total Comments Analyzed: {len(comment_texts)}\n")
                        f.write(f"Positive Comments: {sentiment_counts.get('positive', 0)}\n")
                        f.write(f"Negative Comments: {sentiment_counts.get('negative', 0)}\n")
                        f.write(f"Neutral Comments: {sentiment_counts.get('neutral', 0)}\n")
                except Exception as e:
                    logger.error(f"Error during sentiment analysis: {str(e)}")
            
            # Add result info
            results.append({
                "country_code": country_code,
                "file_path": file_path,
                "record_count": len(pages_data),
                "has_sentiment": sentiment_results is not None
            })
        else:
            logger.warning(f"No data retrieved for country code {country_code}")
    
    logger.info(f"Completed data collection for {len(results)} countries")
    return results

def get_video_data(video_id, api_key=None):
    """
    Get detailed data for a specific video including comments
    """
    if not api_key:
        # Try to load API key if not provided
        api_key, _ = setup(os.path.join(os.path.dirname(__file__), 'api_key.txt'),
                          os.path.join(os.path.dirname(__file__), 'country_codes.txt'))
        if not api_key:
            logger.error("No API key found, cannot retrieve video data")
            return None
    
    # Get video details
    video_url = f"https://www.googleapis.com/youtube/v3/videos?part=snippet,statistics&id={video_id}&key={api_key}"
    try:
        response = requests.get(video_url, verify=certifi.where())
        if response.status_code != 200:
            logger.error(f"Failed to get video data: Status code {response.status_code}")
            return None
        
        video_data = response.json()
        if not video_data.get('items'):
            logger.error(f"No video found with ID {video_id}")
            return None
        
        # Get comments if available
        comments_data = api_request_comments(video_id, api_key, 10)
        comments = []
        
        if comments_data and 'items' in comments_data:
            for comment in comments_data['items']:
                snippet = comment['snippet']['topLevelComment']['snippet']
                comments.append({
                    'text': snippet['textDisplay'],
                    'author': snippet['authorDisplayName'],
                    'date': snippet['publishedAt']
                })
        
        # Apply sentiment analysis if available
        sentiment_results = None
        if has_sentiment_analyzer and comments:
            try:
                comment_texts = [c['text'] for c in comments]
                results, sentiment_counts = sentiment_analyzer.analyze_comments(comment_texts)
                
                # Add sentiment to each comment
                for i, comment in enumerate(comments):
                    comment['sentiment'] = results[i]['sentiment']
                
                sentiment_results = sentiment_counts
            except Exception as e:
                logger.error(f"Error analyzing sentiment: {e}")
        
        return {
            'id': video_id,
            'title': video_data['items'][0]['snippet']['title'],
            'channel': video_data['items'][0]['snippet']['channelTitle'],
            'publishedAt': video_data['items'][0]['snippet']['publishedAt'],
            'viewCount': video_data['items'][0]['statistics'].get('viewCount', 0),
            'likeCount': video_data['items'][0]['statistics'].get('likeCount', 0),
            'commentCount': video_data['items'][0]['statistics'].get('commentCount', 0),
            'comments': comments,
            'sentiment': sentiment_results
        }
    except Exception as e:
        logger.error(f"Error retrieving video data: {e}")
        return None

def get_channel_data(channel_id, api_key=None, max_videos=5):
    """
    Get channel information and analyze its videos
    """
    if not api_key:
        # Try to load API key if not provided
        api_key, _ = setup(os.path.join(os.path.dirname(__file__), 'api_key.txt'),
                          os.path.join(os.path.dirname(__file__), 'country_codes.txt'))
        if not api_key:
            logger.error("No API key found, cannot retrieve channel data")
            return None
    
    try:
        # Get channel details
        channel_url = f"https://www.googleapis.com/youtube/v3/channels?part=snippet,statistics&id={channel_id}&key={api_key}"
        response = requests.get(channel_url, verify=certifi.where())
        if response.status_code != 200:
            logger.error(f"Failed to get channel data: Status code {response.status_code}")
            return None
        
        channel_data = response.json()
        if not channel_data.get('items'):
            logger.error(f"No channel found with ID {channel_id}")
            return None
        
        # Get channel's videos
        videos_url = f"https://www.googleapis.com/youtube/v3/search?part=snippet&channelId={channel_id}&maxResults={max_videos}&order=date&type=video&key={api_key}"
        response = requests.get(videos_url, verify=certifi.where())
        if response.status_code != 200:
            logger.error(f"Failed to get channel videos: Status code {response.status_code}")
            return None
        
        videos_data = response.json()
        video_items = videos_data.get('items', [])
        
        videos = []
        for item in video_items:
            video_id = item['id']['videoId']
            video_info = get_video_data(video_id, api_key)
            if video_info:
                videos.append(video_info)
        
        return {
            'id': channel_id,
            'title': channel_data['items'][0]['snippet']['title'],
            'description': channel_data['items'][0]['snippet']['description'],
            'publishedAt': channel_data['items'][0]['snippet']['publishedAt'],
            'thumbnail': channel_data['items'][0]['snippet']['thumbnails']['high']['url'],
            'subscriberCount': channel_data['items'][0]['statistics'].get('subscriberCount', 0),
            'videoCount': channel_data['items'][0]['statistics'].get('videoCount', 0),
            'viewCount': channel_data['items'][0]['statistics'].get('viewCount', 0),
            'videos': videos
        }
    except Exception as e:
        logger.error(f"Error retrieving channel data: {e}")
        return None

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="YouTube Data Scraper for trending videos, channel analysis, and video sentiment")
    parser.add_argument('--key_path', help='Path to the file containing the API key, by default will use api_key.txt in the same directory', default='api_key.txt')
    parser.add_argument('--country_code_path', help='Path to the file containing the list of country codes to scrape, by default will use country_codes.txt in the same directory', default='country_codes.txt')
    parser.add_argument('--output_dir', help='Path to save the outputted files in', default='output/')
    parser.add_argument('--video', help='Analyze a specific video ID')
    parser.add_argument('--channel', help='Analyze a specific channel ID')
    parser.add_argument('--max_videos', type=int, help='Maximum number of videos to process (default: 5)', default=5)
    parser.add_argument('--max_comments', type=int, help='Maximum number of comments per video (default: 5)', default=5)

    args = parser.parse_args()
    output_dir = args.output_dir
    
    # Make sure output directory exists
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    # Process based on arguments
    if args.video:
        logger.info(f"Analyzing video: {args.video}")
        video_data = get_video_data(args.video)
        if video_data:
            # Save video data to file
            video_file = os.path.join(output_dir, f"{args.video}_analysis.txt")
            with open(video_file, "w+", encoding='utf-8') as f:
                f.write(f"Video Analysis for {args.video}\n")
                f.write(f"Title: {video_data['title']}\n")
                f.write(f"Channel: {video_data['channel']}\n")
                f.write(f"Published: {video_data['publishedAt']}\n")
                f.write(f"Views: {video_data['viewCount']}\n")
                f.write(f"Likes: {video_data['likeCount']}\n")
                f.write(f"Comments: {video_data['commentCount']}\n\n")
                
                if video_data['sentiment']:
                    f.write("Sentiment Analysis:\n")
                    f.write(f"Positive: {video_data['sentiment']['positive']}\n")
                    f.write(f"Negative: {video_data['sentiment']['negative']}\n")
                    f.write(f"Neutral: {video_data['sentiment']['neutral']}\n\n")
                
                f.write("Top Comments:\n")
                for i, comment in enumerate(video_data['comments']):
                    f.write(f"{i+1}. {comment['author']} ({comment['date']}): {comment['text']}\n")
                    if 'sentiment' in comment:
                        f.write(f"   Sentiment: {comment['sentiment']}\n")
                    f.write("\n")
            
            logger.info(f"Video analysis saved to {video_file}")
        else:
            logger.error("Failed to analyze video")
            
    elif args.channel:
        logger.info(f"Analyzing channel: {args.channel}")
        channel_data = get_channel_data(args.channel, max_videos=args.max_videos)
        if channel_data:
            # Save channel data to file
            channel_file = os.path.join(output_dir, f"{args.channel}_analysis.txt")
            with open(channel_file, "w+", encoding='utf-8') as f:
                f.write(f"Channel Analysis for {args.channel}\n")
                f.write(f"Title: {channel_data['title']}\n")
                f.write(f"Subscribers: {channel_data['subscriberCount']}\n")
                f.write(f"Total Videos: {channel_data['videoCount']}\n")
                f.write(f"Total Views: {channel_data['viewCount']}\n\n")
                
                f.write("Top Videos:\n")
                for i, video in enumerate(channel_data['videos']):
                    f.write(f"{i+1}. {video['title']} ({video['publishedAt']})\n")
                    f.write(f"   Views: {video['viewCount']} | Likes: {video['likeCount']} | Comments: {video['commentCount']}\n")
                    
                    if video['sentiment']:
                        f.write(f"   Sentiment: Positive: {video['sentiment']['positive']}, " +
                               f"Negative: {video['sentiment']['negative']}, " +
                               f"Neutral: {video['sentiment']['neutral']}\n")
                    f.write("\n")
            
            logger.info(f"Channel analysis saved to {channel_file}")
        else:
            logger.error("Failed to analyze channel")
    else:
        # Get trending videos data
        results = get_data(args.key_path, args.country_code_path, output_dir)
        if results:
            logger.info(f"Successfully scraped data for {len(results)} countries")
        else:
            logger.error("Failed to scrape data for any countries")