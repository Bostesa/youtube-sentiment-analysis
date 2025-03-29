"""
Utility module to extract YouTube IDs from various URL formats.
This ensures the backend can properly handle URLs sent from the frontend.
"""

import re

def extract_video_id(url_or_id):
    """
    Extract YouTube video ID from various URL formats or return the ID if already a valid ID.
    
    Supports formats:
    - https://www.youtube.com/watch?v=VIDEO_ID
    - https://youtu.be/VIDEO_ID
    - https://www.youtube.com/embed/VIDEO_ID
    - https://youtube.com/v/VIDEO_ID
    - Just the VIDEO_ID itself
    
    Returns the extracted video ID or the original string if it's already an ID
    """
    if not url_or_id:
        return None
        
    # Check if it's already a valid video ID (11 characters)
    if re.match(r'^[A-Za-z0-9_-]{11}$', url_or_id):
        return url_or_id
    
    # Try various URL patterns
    patterns = [
        r'(?:youtube\.com\/watch\?v=)([^&\s]+)',  # youtube.com/watch?v=ID
        r'(?:youtu\.be\/)([^&\s]+)',              # youtu.be/ID
        r'(?:youtube\.com\/embed\/)([^&\s?]+)',   # youtube.com/embed/ID
        r'(?:youtube\.com\/v\/)([^&\s?]+)'        # youtube.com/v/ID
    ]
    
    for pattern in patterns:
        match = re.search(pattern, url_or_id)
        if match:
            return match.group(1)
    
    # If no pattern matched, return the original (might be an ID)
    return url_or_id

def extract_channel_info(url_or_id):
    """
    Extract channel ID or username from various YouTube channel URL formats.
    
    Supports formats:
    - https://www.youtube.com/channel/CHANNEL_ID
    - https://www.youtube.com/c/CUSTOM_NAME
    - https://www.youtube.com/user/USERNAME
    - https://www.youtube.com/@HANDLE
    - Just the CHANNEL_ID itself
    
    Returns a tuple: (type, value)
    - type: 'id' or 'username'
    - value: the extracted channel ID or username
    """
    if not url_or_id:
        return None, None
    
    # Check if it's a channel ID format (starts with UC and is 24 chars)
    if re.match(r'^UC[\w-]{22}$', url_or_id):
        return 'id', url_or_id
    
    # Channel ID URL
    channel_match = re.search(r'(?:youtube\.com\/channel\/)([^\/\s?]+)', url_or_id)
    if channel_match:
        return 'id', channel_match.group(1)
    
    # Custom URL
    custom_match = re.search(r'(?:youtube\.com\/c\/)([^\/\s?]+)', url_or_id)
    if custom_match:
        return 'username', custom_match.group(1)
    
    # User URL
    user_match = re.search(r'(?:youtube\.com\/user\/)([^\/\s?]+)', url_or_id)
    if user_match:
        return 'username', user_match.group(1)
    
    # Handle URL
    handle_match = re.search(r'(?:youtube\.com\/@)([^\/\s?]+)', url_or_id)
    if handle_match:
        return 'username', handle_match.group(1)
    
    # If none of the URL patterns matched, treat as username
    return 'username', url_or_id