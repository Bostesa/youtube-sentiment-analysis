const API_BASE_URL = 'http://localhost:5000/api';

export const fetchVideoSentiment = async (videoId) => {
  try {
    const response = await fetch(`${API_BASE_URL}/analyze/video`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ videoId }),
    });
    
    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.error || 'Failed to analyze video');
    }
    
    return await response.json();
  } catch (error) {
    console.error('Error analyzing video:', error);
    throw error;
  }
};

export const fetchChannelAnalysis = async (channelId, username, maxResults = 10) => {
  try {
    const response = await fetch(`${API_BASE_URL}/analyze/channel`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ 
        channelId, 
        username, 
        maxResults 
      }),
    });
    
    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.error || 'Failed to analyze channel');
    }
    
    return await response.json();
  } catch (error) {
    console.error('Error analyzing channel:', error);
    throw error;
  }
};

export const fetchTrendingVideos = async () => {
  try {
    const response = await fetch(`${API_BASE_URL}/trending`);
    
    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.error || 'Failed to fetch trending videos');
    }
    
    return await response.json();
  } catch (error) {
    console.error('Error fetching trending videos:', error);
    throw error;
  }
};

export const runScraper = async (countryCode = 'US') => {
  try {
    const response = await fetch(`${API_BASE_URL}/run-scraper`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ countryCode }),
    });
    
    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.error || 'Failed to run scraper');
    }
    
    return await response.json();
  } catch (error) {
    console.error('Error running scraper:', error);
    throw error;
  }
};