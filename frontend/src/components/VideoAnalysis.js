import React, { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import { fetchVideoSentiment } from '../services/api';
import '../styles/VideoAnalysis.css';

// Chart component will be used for visualizing sentiment data
import { Pie } from 'react-chartjs-2';
import { Chart as ChartJS, ArcElement, Tooltip, Legend } from 'chart.js';

// Register required Chart.js components
ChartJS.register(ArcElement, Tooltip, Legend);

const VideoAnalysis = () => {
  const { videoId } = useParams();
  const [analysisData, setAnalysisData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const analyzeVideo = async () => {
      if (!videoId) return;
      
      try {
        setLoading(true);
        const data = await fetchVideoSentiment(videoId);
        setAnalysisData(data);
        setError(null);
      } catch (err) {
        setError(err.message || 'Failed to analyze video. Please try again.');
        console.error(err);
      } finally {
        setLoading(false);
      }
    };

    analyzeVideo();
  }, [videoId]);

  // Prepare chart data for sentiment distribution
  const getChartData = () => {
    if (!analysisData || !analysisData.sentiment_distribution) {
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

    const { positive, negative, neutral } = analysisData.sentiment_distribution;
    
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

  return (
    <div className="video-analysis-container">
      <div className="video-analysis-header">
        <Link to="/" className="back-link">
          &larr; Back to Dashboard
        </Link>
        <h1>Video Sentiment Analysis</h1>
      </div>

      {loading ? (
        <div className="loading">Analyzing video comments...</div>
      ) : error ? (
        <div className="error-message">{error}</div>
      ) : analysisData ? (
        <div className="analysis-content">
          <div className="video-preview">
            <iframe
              title="YouTube Video"
              width="560"
              height="315"
              src={`https://www.youtube.com/embed/${videoId}`}
              frameBorder="0"
              allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
              allowFullScreen
            ></iframe>
          </div>

          <div className="sentiment-summary">
            <h2>Sentiment Analysis</h2>
            <div className="chart-container">
              <Pie data={getChartData()} />
            </div>
            <div className="sentiment-stats">
              <div className="stat-item">
                <span className="stat-label">Total Comments:</span>
                <span className="stat-value">{analysisData.comment_count}</span>
              </div>
              {analysisData.sentiment_distribution && (
                <>
                  <div className="stat-item positive">
                    <span className="stat-label">Positive:</span>
                    <span className="stat-value">
                      {analysisData.sentiment_distribution.positive}
                      {' '}
                      ({Math.round((analysisData.sentiment_distribution.positive / analysisData.comment_count) * 100)}%)
                    </span>
                  </div>
                  <div className="stat-item negative">
                    <span className="stat-label">Negative:</span>
                    <span className="stat-value">
                      {analysisData.sentiment_distribution.negative}
                      {' '}
                      ({Math.round((analysisData.sentiment_distribution.negative / analysisData.comment_count) * 100)}%)
                    </span>
                  </div>
                  <div className="stat-item neutral">
                    <span className="stat-label">Neutral:</span>
                    <span className="stat-value">
                      {analysisData.sentiment_distribution.neutral}
                      {' '}
                      ({Math.round((analysisData.sentiment_distribution.neutral / analysisData.comment_count) * 100)}%)
                    </span>
                  </div>
                </>
              )}
            </div>
          </div>

          <div className="comments-section">
            <h2>Comment Analysis</h2>
            <div className="comments-list">
              {analysisData.results.map((result, index) => (
                <div 
                  key={index} 
                  className={`comment-item ${result.sentiment ? result.sentiment : ''}`}
                >
                  <div className="comment-text">{result.comment}</div>
                  {result.sentiment && (
                    <div className="comment-sentiment">
                      Sentiment: <span className={`sentiment-tag ${result.sentiment}`}>
                        {result.sentiment.charAt(0).toUpperCase() + result.sentiment.slice(1)}
                      </span>
                    </div>
                  )}
                </div>
              ))}
            </div>
          </div>
        </div>
      ) : (
        <div className="no-data">No analysis data available</div>
      )}
    </div>
  );
};

export default VideoAnalysis;