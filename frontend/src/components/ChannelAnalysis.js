import React, { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import { fetchChannelAnalysis } from '../services/api';
import '../styles/ChannelAnalysis.css';

// Chart components
import { Pie, Bar } from 'react-chartjs-2';
import { Chart as ChartJS, ArcElement, Tooltip, Legend, CategoryScale, LinearScale, BarElement, Title } from 'chart.js';

// Register Chart.js components
ChartJS.register(ArcElement, Tooltip, Legend, CategoryScale, LinearScale, BarElement, Title);

const ChannelAnalysis = () => {
  const { channelId, username } = useParams();
  const [channelData, setChannelData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const analyzeChannel = async () => {
      if (!channelId && !username) return;
      
      try {
        setLoading(true);
        const data = await fetchChannelAnalysis(channelId, username, 10);
        setChannelData(data);
        setError(null);
      } catch (err) {
        setError(err.message || 'Failed to analyze channel. Please try again.');
        console.error(err);
      } finally {
        setLoading(false);
      }
    };

    analyzeChannel();
  }, [channelId, username]);

  // Prepare chart data for overall sentiment distribution
  const getOverallSentimentChart = () => {
    if (!channelData || !channelData.overallSentiment) {
      return {
        labels: ['No Data'],
        datasets: [
          {
            data: [1],
            backgroundColor: ['#ccc'],
          },
        ],
      };
    }

    const { positive, negative, neutral } = channelData.overallSentiment;
    
    return {
      labels: ['Positive', 'Negative', 'Neutral'],
      datasets: [
        {
          data: [positive, negative, neutral],
          backgroundColor: ['#4CAF50', '#F44336', '#2196F3'],
        },
      ],
    };
  };

  // Prepare chart data for per-video sentiment
  const getVideoSentimentChart = () => {
    if (!channelData || !channelData.videoAnalysis || channelData.videoAnalysis.length === 0) {
      return {
        labels: ['No Data'],
        datasets: [
          {
            label: 'Positive',
            data: [0],
            backgroundColor: '#4CAF50',
          },
          {
            label: 'Negative',
            data: [0],
            backgroundColor: '#F44336',
          },
          {
            label: 'Neutral',
            data: [0],
            backgroundColor: '#2196F3',
          },
        ]
      };
    }

    // Sort videos by comment count (highest first)
    const sortedVideos = [...channelData.videoAnalysis].sort((a, b) => b.commentCount - a.commentCount);
    const top5Videos = sortedVideos.slice(0, 5);
    
    return {
      labels: top5Videos.map(video => {
        // Truncate long titles
        const title = video.title;
        return title.length > 20 ? title.substring(0, 20) + '...' : title;
      }),
      datasets: [
        {
          label: 'Positive',
          data: top5Videos.map(video => video.sentiment.positive),
          backgroundColor: '#4CAF50',
        },
        {
          label: 'Negative',
          data: top5Videos.map(video => video.sentiment.negative),
          backgroundColor: '#F44336',
        },
        {
          label: 'Neutral',
          data: top5Videos.map(video => video.sentiment.neutral),
          backgroundColor: '#2196F3',
        },
      ]
    };
  };

  const formatNumber = (num) => {
    return new Intl.NumberFormat().format(num);
  };

  return (
    <div className="channel-analysis-container">
      <div className="channel-analysis-header">
        <Link to="/" className="back-link">
          &larr; Back to Dashboard
        </Link>
        <h1>Channel Sentiment Analysis</h1>
      </div>

      {loading ? (
        <div className="loading">Analyzing channel data...</div>
      ) : error ? (
        <div className="error-message">{error}</div>
      ) : channelData ? (
        <div className="analysis-content">
          <div className="channel-overview">
            <div className="channel-info">
              {channelData.channelInfo.thumbnail && (
                <img 
                  src={channelData.channelInfo.thumbnail} 
                  alt={channelData.channelInfo.title} 
                  className="channel-thumbnail"
                />
              )}
              <div className="channel-details">
                <h2>{channelData.channelInfo.title}</h2>
                <p className="channel-description">{channelData.channelInfo.description}</p>
                <div className="channel-stats">
                  <div className="stat">
                    <span className="stat-value">{formatNumber(channelData.channelInfo.subscriberCount)}</span>
                    <span className="stat-label">Subscribers</span>
                  </div>
                  <div className="stat">
                    <span className="stat-value">{formatNumber(channelData.channelInfo.videoCount)}</span>
                    <span className="stat-label">Videos</span>
                  </div>
                  <div className="stat">
                    <span className="stat-value">{formatNumber(channelData.channelInfo.viewCount)}</span>
                    <span className="stat-label">Views</span>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <div className="sentiment-overview">
            <h2>Audience Sentiment Overview</h2>
            <div className="sentiment-cards">
              <div className="sentiment-card">
                <div className="card-header">
                  <h3>Overall Sentiment</h3>
                </div>
                <div className="chart-container">
                  <Pie data={getOverallSentimentChart()} />
                </div>
                <div className="sentiment-stats">
                  <div className="stat-row positive">
                    <span className="sentiment-label">Positive</span>
                    <div className="sentiment-bar-container">
                      <div className="sentiment-bar positive" style={{ width: `${channelData.overallSentimentPercentages.positive}%` }}></div>
                    </div>
                    <span className="sentiment-percent">{channelData.overallSentimentPercentages.positive}%</span>
                  </div>
                  <div className="stat-row negative">
                    <span className="sentiment-label">Negative</span>
                    <div className="sentiment-bar-container">
                      <div className="sentiment-bar negative" style={{ width: `${channelData.overallSentimentPercentages.negative}%` }}></div>
                    </div>
                    <span className="sentiment-percent">{channelData.overallSentimentPercentages.negative}%</span>
                  </div>
                  <div className="stat-row neutral">
                    <span className="sentiment-label">Neutral</span>
                    <div className="sentiment-bar-container">
                      <div className="sentiment-bar neutral" style={{ width: `${channelData.overallSentimentPercentages.neutral}%` }}></div>
                    </div>
                    <span className="sentiment-percent">{channelData.overallSentimentPercentages.neutral}%</span>
                  </div>
                </div>
              </div>

              <div className="sentiment-card">
                <div className="card-header">
                  <h3>Sentiment by Video</h3>
                </div>
                <div className="chart-container bar-chart">
                  <Bar 
                    data={getVideoSentimentChart()} 
                    options={{
                      responsive: true,
                      maintainAspectRatio: false,
                      scales: {
                        x: {
                          stacked: false,
                        },
                        y: {
                          stacked: false
                        }
                      }
                    }}
                  />
                </div>
              </div>
            </div>
          </div>

          <div className="video-analysis-section">
            <h2>Video Analysis</h2>
            <div className="videos-grid">
              {channelData.videoAnalysis.map((video) => (
                <div key={video.videoId} className="video-analysis-card">
                  <div className="video-title-section">
                    <h3>{video.title}</h3>
                    <Link to={`/analyze/${video.videoId}`} className="view-video-link">
                      View Details
                    </Link>
                  </div>
                  <div className="video-sentiment-summary">
                    <div className="comment-count">
                      <span>{video.commentCount}</span> comments analyzed
                    </div>
                    <div className="sentiment-bars">
                      <div className="mini-bar-row">
                        <span className="mini-label">Positive</span>
                        <div className="mini-bar-container">
                          <div 
                            className="mini-bar positive" 
                            style={{ width: `${video.sentimentPercentages.positive}%` }}
                          ></div>
                        </div>
                        <span className="mini-percent">{video.sentimentPercentages.positive}%</span>
                      </div>
                      <div className="mini-bar-row">
                        <span className="mini-label">Negative</span>
                        <div className="mini-bar-container">
                          <div 
                            className="mini-bar negative" 
                            style={{ width: `${video.sentimentPercentages.negative}%` }}
                          ></div>
                        </div>
                        <span className="mini-percent">{video.sentimentPercentages.negative}%</span>
                      </div>
                      <div className="mini-bar-row">
                        <span className="mini-label">Neutral</span>
                        <div className="mini-bar-container">
                          <div 
                            className="mini-bar neutral" 
                            style={{ width: `${video.sentimentPercentages.neutral}%` }}
                          ></div>
                        </div>
                        <span className="mini-percent">{video.sentimentPercentages.neutral}%</span>
                      </div>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>

          <div className="insights-section">
            <h2>Content Insights</h2>
            <div className="insights-cards">
              <div className="insight-card">
                <h3>Audience Mood</h3>
                <p>
                  {channelData.overallSentimentPercentages.positive > 50 ? (
                    "Your audience is predominantly positive. They appreciate your content and engage with it constructively."
                  ) : channelData.overallSentimentPercentages.negative > 30 ? (
                    "There's significant negativity in your comments. Consider addressing audience concerns in upcoming videos."
                  ) : (
                    "Your audience sentiment is mixed. Focus on topics from your most positively-received videos to boost engagement."
                  )}
                </p>
              </div>
              <div className="insight-card">
                <h3>Content Strategy</h3>
                <p>
                  Based on your comment sentiment analysis, consider creating more content similar to your most positively-received videos. 
                  Your audience particularly engages with 
                  {channelData.videoAnalysis.length > 0 ? 
                    ` videos like "${channelData.videoAnalysis.sort((a, b) => 
                      b.sentimentPercentages.positive - a.sentimentPercentages.positive)[0].title}".` 
                    : " your most popular content themes."}
                </p>
              </div>
              <div className="insight-card">
                <h3>Engagement Tips</h3>
                <p>
                  With {formatNumber(channelData.totalComments)} comments analyzed, your channel 
                  shows {channelData.overallSentimentPercentages.positive > channelData.overallSentimentPercentages.negative ? 
                    "positive momentum" : "areas for improvement"} in audience engagement. 
                  {channelData.overallSentimentPercentages.neutral > 40 ? 
                    " Try to create more emotionally resonant content to reduce neutral sentiment." : 
                    " Keep fostering the conversation with your audience through comments."}
                </p>
              </div>
            </div>
          </div>
        </div>
      ) : (
        <div className="no-data">No channel data available</div>
      )}
    </div>
  );
};

export default ChannelAnalysis;