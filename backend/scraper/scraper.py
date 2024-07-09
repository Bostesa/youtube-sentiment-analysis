import requests
import sys
import time
import os
import argparse
import certifi

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
        print(f"Error: The API key file was not found at {api_path}")
        sys.exit(1)

    try:
        with open(code_path) as file:
            country_codes = [x.strip() for x in file if x.strip()]
    except FileNotFoundError:
        print(f"Error: The country codes file was not found at {code_path}")
        sys.exit(1)

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
    response = requests.get(popular_videos_url, verify=certifi.where())
    if response.status_code == 429:
        print("Temp-Banned due to excess requests, please wait and continue later")
        sys.exit(1)
    if response.status_code != 200:
        print(f"Error: Received status code {response.status_code}")
        print(response.text)
        sys.exit(1)
    return response.json()

def api_request_comments(video_id, api_key, max_results=10):
    # Builds the URL and requests the JSON from it
    comments_url = f"https://www.googleapis.com/youtube/v3/commentThreads?part=snippet&videoId={video_id}&maxResults={max_results}&key={api_key}"
    response = requests.get(comments_url, verify=certifi.where())
    if response.status_code == 429:
        print("Temp-Banned due to excess requests, please wait and continue later")
        sys.exit(1)
    if response.status_code == 403 and "commentsDisabled" in response.text:
        print(f"Comments are disabled for video ID {video_id}")
        return None
    if response.status_code != 200:
        print(f"Error: Received status code {response.status_code}")
        print(response.text)
        sys.exit(1)
    return response.json()

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
        if video["comments_disabled"]:
            continue
        video_id = video["video_id"].strip('"')
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
    
    return lines

def get_pages(country_code):
    country_data = []
    next_page_token = "&"

    while next_page_token is not None:
        # A page of data i.e. a list of videos and all needed data
        video_data_page = api_request(next_page_token, country_code, api_key)
        
        # Get the next page token and build a string which can be injected into the request with it, unless it's None,
        # then let the whole thing be None so that the loop ends after this cycle
        next_page_token = video_data_page.get("nextPageToken", None)
        next_page_token = f"&pageToken={next_page_token}&" if next_page_token is not None else next_page_token

        # Get all of the items as a list and let get_videos return the needed features
        items = video_data_page.get('items', [])
        video_details = fetch_popular_videos(items)
        country_data += fetch_and_process_comments(video_details, api_key)

        if len(country_data) >= 500:
            break

    return country_data[:500]

def write_to_file(country_code, country_data):
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    file_path = f"{output_dir}/{time.strftime('%y.%d.%m')}_{country_code}_videos.csv"

    with open(file_path, "w+", encoding='utf-8') as file:
        for row in country_data:
            file.write(f"{row}\n")

def get_data():
    for country_code in country_codes:
        country_data = [",".join(header)]
        pages_data = get_pages(country_code)
        if pages_data:
            country_data += pages_data
        write_to_file(country_code, country_data)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--key_path', help='Path to the file containing the API key, by default will use api_key.txt in the same directory', default='api_key.txt')
    parser.add_argument('--country_code_path', help='Path to the file containing the list of country codes to scrape, by default will use country_codes.txt in the same directory', default='country_codes.txt')
    parser.add_argument('--output_dir', help='Path to save the outputted files in', default='output/')

    args = parser.parse_args()

    output_dir = args.output_dir
    api_key, country_codes = setup(args.key_path, args.country_code_path)

    get_data()
=======
import requests
import sys
import time
import os
import argparse
import certifi

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
        print(f"Error: The API key file was not found at {api_path}")
        sys.exit(1)

    try:
        with open(code_path) as file:
            country_codes = [x.strip() for x in file if x.strip()]
    except FileNotFoundError:
        print(f"Error: The country codes file was not found at {code_path}")
        sys.exit(1)

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
    response = requests.get(popular_videos_url, verify=certifi.where())
    if response.status_code == 429:
        print("Temp-Banned due to excess requests, please wait and continue later")
        sys.exit(1)
    if response.status_code != 200:
        print(f"Error: Received status code {response.status_code}")
        print(response.text)
        sys.exit(1)
    return response.json()

def api_request_comments(video_id, api_key, max_results=10):
    # Builds the URL and requests the JSON from it
    comments_url = f"https://www.googleapis.com/youtube/v3/commentThreads?part=snippet&videoId={video_id}&maxResults={max_results}&key={api_key}"
    response = requests.get(comments_url, verify=certifi.where())
    if response.status_code == 429:
        print("Temp-Banned due to excess requests, please wait and continue later")
        sys.exit(1)
    if response.status_code == 403 and "commentsDisabled" in response.text:
        print(f"Comments are disabled for video ID {video_id}")
        return None
    if response.status_code != 200:
        print(f"Error: Received status code {response.status_code}")
        print(response.text)
        sys.exit(1)
    return response.json()

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
        if video["comments_disabled"]:
            continue
        video_id = video["video_id"].strip('"')
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
    
    return lines

def get_pages(country_code):
    country_data = []
    next_page_token = "&"

    while next_page_token is not None:
        # A page of data i.e. a list of videos and all needed data
        video_data_page = api_request(next_page_token, country_code, api_key)
        
        # Get the next page token and build a string which can be injected into the request with it, unless it's None,
        # then let the whole thing be None so that the loop ends after this cycle
        next_page_token = video_data_page.get("nextPageToken", None)
        next_page_token = f"&pageToken={next_page_token}&" if next_page_token is not None else next_page_token

        # Get all of the items as a list and let get_videos return the needed features
        items = video_data_page.get('items', [])
        video_details = fetch_popular_videos(items)
        country_data += fetch_and_process_comments(video_details, api_key)

        if len(country_data) >= 500:
            break

    return country_data[:500]

def write_to_file(country_code, country_data):
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    file_path = f"{output_dir}/{time.strftime('%y.%d.%m')}_{country_code}_videos.csv"

    with open(file_path, "w+", encoding='utf-8') as file:
        for row in country_data:
            file.write(f"{row}\n")

def get_data():
    for country_code in country_codes:
        country_data = [",".join(header)]
        pages_data = get_pages(country_code)
        if pages_data:
            country_data += pages_data
        write_to_file(country_code, country_data)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--key_path', help='Path to the file containing the API key, by default will use api_key.txt in the same directory', default='api_key.txt')
    parser.add_argument('--country_code_path', help='Path to the file containing the list of country codes to scrape, by default will use country_codes.txt in the same directory', default='country_codes.txt')
    parser.add_argument('--output_dir', help='Path to save the outputted files in', default='output/')

    args = parser.parse_args()

    output_dir = args.output_dir
    api_key, country_codes = setup(args.key_path, args.country_code_path)

    get_data()