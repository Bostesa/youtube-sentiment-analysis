import os
import time
import re
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

class YouTubeClient:
    def __init__(self):
        api_key = os.getenv('YOUTUBE_DATA_API_KEY')
        if not api_key:
            # Try to read from file if environment variable is not set
            try:
                with open(os.path.join(os.path.dirname(os.path.dirname(__file__)), 'scraper', 'api_key.txt'), 'r') as f:
                    api_key = f.read().strip()
            except:
                raise ValueError("YouTube API key not found. Please set YOUTUBE_DATA_API_KEY environment variable or create scraper/api_key.txt file.")
        
        self.youtube = build('youtube', 'v3', developerKey=api_key)

    def clean_comment(self, comment):
        # Basic preprocessing to remove URLs and non-alphanumeric characters
        comment = re.sub(r'http\S+', '', comment)  # Remove URLs
        comment = re.sub(r'[^A-Za-z0-9 ]+', '', comment)  # Remove non-alphanumeric chars
        return comment

    def get_channel_id_from_username(self, username):
        """Get channel ID from a username or custom URL."""
        try:
            request = self.youtube.channels().list(
                part="id",
                forUsername=username
            )
            response = request.execute()
            
            if response['items']:
                return response['items'][0]['id']
            else:
                # Try to handle custom URLs (e.g., youtube.com/c/CustomName)
                request = self.youtube.search().list(
                    part="snippet",
                    q=username,
                    type="channel",
                    maxResults=1
                )
                response = request.execute()
                
                if response['items']:
                    return response['items'][0]['snippet']['channelId']
                else:
                    return None
        except HttpError as e:
            print(f"An HTTP error {e.resp.status} occurred: {e.content}")
            return None

    def get_channel_videos(self, channel_id, max_results=50):
        """Get videos from a specific channel."""
        try:
            videos = []
            request = self.youtube.search().list(
                part="snippet",
                channelId=channel_id,
                maxResults=max_results,
                order="date",
                type="video"
            )
            response = request.execute()
            
            for item in response.get('items', []):
                video_id = item['id']['videoId']
                title = item['snippet']['title']
                description = item['snippet']['description']
                published_at = item['snippet']['publishedAt']
                thumbnail = item['snippet']['thumbnails']['high']['url']
                
                # Get video statistics
                video_stats = self.youtube.videos().list(
                    part="statistics",
                    id=video_id
                ).execute()
                
                stats = video_stats['items'][0]['statistics'] if video_stats['items'] else {}
                
                videos.append({
                    'videoId': video_id,
                    'title': title,
                    'description': description,
                    'publishedAt': published_at,
                    'thumbnail': thumbnail,
                    'viewCount': int(stats.get('viewCount', 0)),
                    'likeCount': int(stats.get('likeCount', 0)),
                    'commentCount': int(stats.get('commentCount', 0)) if 'commentCount' in stats else 0
                })
                
                # Sleep a bit to avoid hitting rate limits
                time.sleep(0.2)
                
            return videos
        
        except HttpError as e:
            print(f"An HTTP error {e.resp.status} occurred: {e.content}")
            return []

    def get_video_comments(self, video_ids, max_results=100):
        """Get comments from a list of video IDs."""
        all_comments = []
        
        if isinstance(video_ids, str):
            video_ids = [video_ids]
            
        for video_id in video_ids:
            video_comments = []
            try:
                request = self.youtube.commentThreads().list(
                    part='snippet',
                    videoId=video_id,
                    maxResults=max_results,
                    textFormat='plainText'
                )
                response = request.execute()

                while response:
                    for item in response['items']:
                        comment_data = item['snippet']['topLevelComment']['snippet']
                        comment_text = comment_data['textDisplay']
                        cleaned_comment = self.clean_comment(comment_text)
                        
                        video_comments.append({
                            'comment': cleaned_comment,
                            'author': comment_data['authorDisplayName'],
                            'publishedAt': comment_data['publishedAt'],
                            'likeCount': comment_data['likeCount']
                        })

                    # Handle pagination
                    if 'nextPageToken' in response:
                        request = self.youtube.commentThreads().list(
                            part='snippet',
                            videoId=video_id,
                            pageToken=response['nextPageToken'],
                            maxResults=max_results,
                            textFormat='plainText'
                        )
                        time.sleep(0.5)  # Simple backoff strategy
                        response = request.execute()
                    else:
                        break
                
                all_comments.append({
                    'videoId': video_id,
                    'comments': video_comments
                })

            except HttpError as e:
                # Handle disabled comments
                if e.resp.status == 403 and 'commentsDisabled' in str(e.content):
                    all_comments.append({
                        'videoId': video_id,
                        'comments': [],
                        'error': 'Comments are disabled for this video'
                    })
                else:
                    print(f"An HTTP error {e.resp.status} occurred for video {video_id}: {e.content}")
                    all_comments.append({
                        'videoId': video_id,
                        'comments': [],
                        'error': f"An error occurred: {e.resp.status}"
                    })
            except Exception as e:
                print(f"An error occurred for video {video_id}: {e}")
                all_comments.append({
                    'videoId': video_id,
                    'comments': [],
                    'error': f"An error occurred: {str(e)}"
                })

        return all_comments

    def get_channel_info(self, channel_id):
        """Get basic information about a channel."""
        try:
            request = self.youtube.channels().list(
                part="snippet,statistics,brandingSettings",
                id=channel_id
            )
            response = request.execute()
            
            if not response['items']:
                return None
                
            channel_data = response['items'][0]
            snippet = channel_data['snippet']
            statistics = channel_data['statistics']
            
            return {
                'channelId': channel_id,
                'title': snippet['title'],
                'description': snippet['description'],
                'publishedAt': snippet['publishedAt'],
                'thumbnail': snippet['thumbnails']['high']['url'] if 'high' in snippet['thumbnails'] else snippet['thumbnails']['default']['url'],
                'subscriberCount': int(statistics.get('subscriberCount', 0)),
                'videoCount': int(statistics.get('videoCount', 0)),
                'viewCount': int(statistics.get('viewCount', 0))
            }
            
        except HttpError as e:
            print(f"An HTTP error {e.resp.status} occurred: {e.content}")
            return None
    
    def get_trending_videos(self, region_code='US', max_results=10):
        """
        Fetch trending (mostPopular) videos for a given region_code.
        Returns a list of dictionaries with video details.
        """
        try:
            request = self.youtube.videos().list(
                part="snippet,statistics",
                chart="mostPopular",
                regionCode=region_code,
                maxResults=max_results
            )
            response = request.execute()
            
            items = response.get('items', [])
            trending_videos = []
            
            for item in items:
                video_id = item['id']
                snippet = item['snippet']
                statistics = item.get('statistics', {})
                
                trending_videos.append({
                    'videoId': video_id,
                    'title': snippet.get('title', ''),
                    'channelTitle': snippet.get('channelTitle', ''),
                    'publishedAt': snippet.get('publishedAt', ''),
                    'viewCount': int(statistics.get('viewCount', 0)),
                    'likeCount': int(statistics.get('likeCount', 0)),
                    'commentCount': int(statistics.get('commentCount', 0))
                })
            
            return trending_videos
        
        except HttpError as e:
            print(f"An HTTP error {e.resp.status} occurred: {e.content}")
            return []