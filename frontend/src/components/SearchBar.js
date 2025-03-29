import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import '../styles/SearchBar.css';

const SearchBar = () => {
  const [searchValue, setSearchValue] = useState('');
  const [searchType, setSearchType] = useState('video');
  const navigate = useNavigate();

  const extractVideoId = (url) => {
    // Handle various YouTube URL formats
    
    // Format: https://www.youtube.com/watch?v=VIDEO_ID
    const watchRegex = /(?:youtube\.com\/watch\?v=)([^&\s]+)/;
    // Format: https://youtu.be/VIDEO_ID
    const shortRegex = /(?:youtu\.be\/)([^&\s]+)/;
    // Format: https://www.youtube.com/embed/VIDEO_ID
    const embedRegex = /(?:youtube\.com\/embed\/)([^&\s]+)/;
    // Format: https://youtube.com/v/VIDEO_ID
    const vRegex = /(?:youtube\.com\/v\/)([^&\s]+)/;
    
    // Try each regex pattern
    let match = url.match(watchRegex) || 
                url.match(shortRegex) ||
                url.match(embedRegex) ||
                url.match(vRegex);
    
    // Return the video ID if found, otherwise return original input
    return match && match[1] ? match[1] : url;
  };
  
  const extractChannelId = (url) => {
    // Handle various YouTube channel URL formats
    
    // Format: https://www.youtube.com/channel/CHANNEL_ID
    const channelRegex = /(?:youtube\.com\/channel\/)([^\/\s?]+)/;
    // Format: https://www.youtube.com/c/CUSTOM_NAME
    const customRegex = /(?:youtube\.com\/c\/)([^\/\s?]+)/;
    // Format: https://www.youtube.com/user/USERNAME
    const userRegex = /(?:youtube\.com\/user\/)([^\/\s?]+)/;
    // Format: https://www.youtube.com/@HANDLE
    const handleRegex = /(?:youtube\.com\/@)([^\/\s?]+)/;
    
    // Try each regex pattern
    let match = url.match(channelRegex);
    if (match && match[1]) {
      return { type: 'id', value: match[1] };
    }
    
    match = url.match(customRegex) || url.match(userRegex) || url.match(handleRegex);
    if (match && match[1]) {
      return { type: 'username', value: match[1] };
    }
    
    // If it's a channel ID format (starts with UC and 24 chars)
    if (/^UC[\w-]{22}$/.test(url)) {
      return { type: 'id', value: url };
    }
    
    // Otherwise treat as username/handle
    return { type: 'username', value: url };
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    
    if (!searchValue) return;
    
    if (searchType === 'video') {
      const videoId = extractVideoId(searchValue);
      navigate(`/analyze/${videoId}`);
    } else if (searchType === 'channel') {
      const channelInfo = extractChannelId(searchValue);
      if (channelInfo.type === 'id') {
        navigate(`/channel/id/${channelInfo.value}`);
      } else {
        navigate(`/channel/username/${channelInfo.value}`);
      }
    }
  };

  return (
    <div className="search-bar-container">
      <form onSubmit={handleSubmit} className="search-form">
        <div className="search-type-toggle">
          <button
            type="button"
            className={`toggle-button ${searchType === 'video' ? 'active' : ''}`}
            onClick={() => setSearchType('video')}
          >
            Video
          </button>
          <button
            type="button"
            className={`toggle-button ${searchType === 'channel' ? 'active' : ''}`}
            onClick={() => setSearchType('channel')}
          >
            Channel
          </button>
        </div>
        <div className="search-input-container">
          <input
            type="text"
            value={searchValue}
            onChange={(e) => setSearchValue(e.target.value)}
            placeholder={searchType === 'video' 
              ? "Enter YouTube video ID or URL" 
              : "Enter YouTube channel ID, username, or URL"}
            className="search-input"
          />
          <button type="submit" className="search-button">
            Analyze
          </button>
        </div>
      </form>
    </div>
  );
};

export default SearchBar;