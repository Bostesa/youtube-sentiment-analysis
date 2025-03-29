import React, { useState, useEffect } from 'react';
import { fetchTrendingVideos } from '../services/api';
import VideoCard from './VideoCard';
import '../styles/Dashboard.css';

const Dashboard = () => {
  const [trendingVideos, setTrendingVideos] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const loadTrendingVideos = async () => {
      try {
        setLoading(true);
        const data = await fetchTrendingVideos();
        setTrendingVideos(data.trending_videos || []);
        setError(null);
      } catch (err) {
        setError('Failed to load trending videos. Please try again later.');
        console.error(err);
      } finally {
        setLoading(false);
      }
    };

    loadTrendingVideos();
  }, []);

  return (
    <div className="dashboard-container">
      <div className="dashboard-header">
        <h1>YouTube Sentiment Analysis Dashboard</h1>
        <p>Analyze viewer sentiment from YouTube comments</p>
      </div>

      <div className="dashboard-content">
        <div className="trending-section">
          <h2>Trending Videos</h2>
          {loading ? (
            <div className="loading">Loading trending videos...</div>
          ) : error ? (
            <div className="error-message">{error}</div>
          ) : trendingVideos.length === 0 ? (
            <div className="no-videos">No trending videos available</div>
          ) : (
            <div className="video-grid">
              {trendingVideos.map((video) => (
                <VideoCard key={video.videoId} video={video} />
              ))}
            </div>
          )}
        </div>
      </div>

      <div className="dashboard-footer">
        <p>
          Enter a YouTube video ID in the search bar above to analyze its comments
        </p>
      </div>
    </div>
  );
};

export default Dashboard;