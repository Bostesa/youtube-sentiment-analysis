import React from 'react';
import { Link } from 'react-router-dom';
import '../styles/VideoCard.css';

const VideoCard = ({ video }) => {
  const { videoId, title, channelTitle, viewCount } = video;
  
  // Format view count with commas
  const formatViewCount = (count) => {
    return count.toString().replace(/\B(?=(\d{3})+(?!\d))/g, ",");
  };
  
  // Get YouTube thumbnail
  const thumbnailUrl = `https://img.youtube.com/vi/${videoId}/mqdefault.jpg`;
  
  return (
    <div className="video-card">
      <Link to={`/analyze/${videoId}`} className="video-card-link">
        <div className="video-thumbnail">
          <img src={thumbnailUrl} alt={title} />
        </div>
        <div className="video-info">
          <h3 className="video-title">{title}</h3>
          <p className="video-channel">{channelTitle}</p>
          <p className="video-views">{formatViewCount(viewCount)} views</p>
        </div>
      </Link>
    </div>
  );
};

export default VideoCard;