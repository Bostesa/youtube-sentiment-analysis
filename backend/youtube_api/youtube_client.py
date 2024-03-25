import os
import time
import re
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

class YouTubeClient:
    def __init__(self):
        api_key = os.getenv('YOUTUBE_DATA_API_KEY')
        self.youtube = build('youtube', 'v3', developerKey=api_key)

    def clean_comment(self, comment):
        # Basic preprocessing to remove URLs and non-alphanumeric characters
        comment = re.sub(r'http\S+', '', comment)  # Remove URLs
        comment = re.sub(r'[^A-Za-z0-9 ]+', '', comment)  # Remove non-alphanumeric chars
        return comment

    def get_video_comments(self, video_ids, max_results=100):
        all_comments = []
        for video_id in video_ids:
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
                        comment = item['snippet']['topLevelComment']['snippet']['textDisplay']
                        comment = self.clean_comment(comment)  # Preprocess comment
                        all_comments.append(comment)

                    # Pagination handling with a sleep to respect rate limits
                    if 'nextPageToken' in response:
                        request = self.youtube.commentThreads().list(
                            part='snippet',
                            videoId=video_id,
                            pageToken=response['nextPageToken'],
                            maxResults=max_results,
                            textFormat='plainText'
                        )
                        time.sleep(1)  # Simple backoff strategy
                        response = request.execute()
                    else:
                        break

            except HttpError as e:
                print(f'An HTTP error {e.resp.status} occurred:\n{e.content}')
            except Exception as e:
                print(f'An error occurred: {e}')

        return all_comments
