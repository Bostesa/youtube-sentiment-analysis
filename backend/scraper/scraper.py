import requests, sys, time, os, argparse

# List of simple to collect features
snippet_features = ["comment_id", "comment_text", "author", "comment_date"]

# Any characters to exclude, generally these are things that become problematic in CSV files
unsafe_characters = ['\n', '"']

# Used to identify columns, currently hardcoded order
header = ["video_id"] + snippet_features


def setup(api_path, code_path):
    with open(api_path, 'r') as file:
        api_key = file.readline()

    with open(code_path) as file:
        country_codes = [x.rstrip() for x in file]

    return api_key, country_codes


def prepare_feature(feature):
    # Removes any character from the unsafe characters list and surrounds the whole item in quotes
    for ch in unsafe_characters:
        feature = str(feature).replace(ch, "")
    return f'"{feature}"'


def fetch_popular_videos(page_token,country_code):
    popular_videos_url = f"https://www.googleapis.com/youtube/v3/videos?part=snippet&chart=mostPopular&regionCode={country_code}&maxResults=200&key={api_key}"
    response = requests.get(popular_videos_url)
    if response.status_code == 429:
        print("Temp-Banned due to excess requests, please wait and continue later")
        sys.exit()
    popular_videos_data = response.json()
     # Debugging: Print the full API response
    print(popular_videos_data)

    # Check for errors in the API response
    if 'error' in popular_videos_data:
        error_message = popular_videos_data.get('error', {}).get('message', 'Unknown error')
        print(f"API Error: {error_message}")
        sys.exit()

    if 'items' not in popular_videos_data:
        print("The 'items' key is missing in the API response.")
        sys.exit()

    video_ids = [item['id'] for item in popular_videos_data['items']]
    return video_ids

def get_tags(tags_list):
    # Takes a list of tags, prepares each tag and joins them into a string by the pipe character
    return prepare_feature("|".join(tags_list))

# Function to fetch comments for a given list of video IDs
def fetch_and_process_comments(video_id, max_results=100):
    all_comments_data = []
    page_token =""
    while True:
        comments_url = f"https://www.googleapis.com/youtube/v3/commentThreads?part=snippet&videoId={video_id}&maxResults={max_results}&key={api_key}{page_token}"
        response = requests.get(comments_url)
        if response.status_code == 429:
            print("Temp-Banned due to excess requests, please wait and continue later")
            sys.exit()
        comments_data = response.json()
        for item in comments_data['items']:
            comment_snippet = item['snippet']['topLevelComment']['snippet']
            features = [prepare_feature(comment_snippet.get(feature, "")) for feature in snippet_features]
            line = [prepare_feature(video_id)] + features
            all_comments_data.append(",".join(line))
        page_token = comments_data.get('nextPageToken', '')
        if not page_token:
            break
    return all_comments_data

def get_pages(country_code):
    for country_code in country_codes:
        print(f"Processing country code: {country_code}")
        video_ids = fetch_popular_videos(country_code, api_key)
        country_data = []
        for video_id in video_ids:
            comments_data = fetch_and_process_comments(video_id, api_key)
            country_data.extend(comments_data)
        write_to_file(country_code, country_data)


def write_to_file(country_code, country_data):

    print(f"Writing {country_code} data to file...")

    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    with open(f"{output_dir}/{time.strftime('%y.%d.%m')}_{country_code}_videos.csv", "w+", encoding='utf-8') as file:
        for row in country_data:
            file.write(f"{row}\n")


def get_data():
    for country_code in country_codes:
        country_data = [",".join(header)] + get_pages(country_code)
        write_to_file(country_code, country_data)


if __name__ == "__main__":

    parser = argparse.ArgumentParser()
    parser.add_argument('--key_path', help='Path to the file containing the api key, by default will use api_key.txt in the same directory', default='api_key.txt')
    parser.add_argument('--country_code_path', help='Path to the file containing the list of country codes to scrape, by default will use country_codes.txt in the same directory', default='country_codes.txt')
    parser.add_argument('--output_dir', help='Path to save the outputted files in', default='output/')

    args = parser.parse_args()

    output_dir = args.output_dir
    api_key, country_codes = setup(args.key_path, args.country_code_path)

    get_data()

