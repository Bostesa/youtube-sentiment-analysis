# YouTube Sentiment Analysis App

This fullstack application leverages the YouTube Data API to gather comments from videos and channels, then performs sentiment analysis to provide content creators with valuable insights into viewer reactions. These insights can help creators optimize their content strategy based on audience sentiment.

## Features

- **Immediate Sentiment Analysis**: The app comes with a pre-trained sentiment model - no waiting for training!
- **Video Sentiment Analysis**: Analyze comments from any YouTube video
- **Channel Analysis**: Analyze sentiment trends across an entire YouTube channel
- **Trending Videos Analysis**: See sentiment analysis of trending videos across different regions
- **Content Insights**: Get actionable recommendations to improve content strategy
- **Sentiment Visualization**: Visual charts showing the distribution of sentiments

## Quick Start with Docker

The easiest way to run the application is with Docker:

### 1. Install Docker

Make sure you have [Docker](https://www.docker.com/products/docker-desktop) and Docker Compose installed on your system.

### 2. Train the Model Locally (Optional but Recommended)

For faster performance, you can train the sentiment analysis model on your local machine:

```
python train_model_locally.py
```

This creates a pre-trained model that Docker will use, making the application faster as it won't need to train the model during startup.

### 3. Run the Setup Script

This will create necessary directories and prompt you for your YouTube API key:

**On Windows:**
```
setup.bat
```

**On macOS/Linux:**
```
chmod +x setup.sh
./setup.sh
```

### 4. Start the Application

```
docker-compose up -d
```

### 5. Access the Application

Open your browser and navigate to:
```
http://localhost
```

## How the Sentiment Analysis Model Works

The application uses an NLP-based sentiment analysis model that:

1. Is built using scikit-learn with a TF-IDF vectorizer and Random Forest classifier
2. Analyzes comments and categorizes them as positive, negative, or neutral
3. Uses natural language processing techniques including:
   - Text cleaning and normalization
   - Stopword removal
   - Lemmatization
   - TF-IDF feature extraction

When you train the model locally with `train_model_locally.py`:
- The model is trained on your device which may be faster than training in Docker
- The trained model is saved to `backend/sentiment_analysis/models/sentiment_model.pkl`
- Docker will automatically mount and use this pre-trained model
- This makes the application start faster as it doesn't need to train during startup

## How to Get a YouTube API Key

1. Go to the [Google Developers Console](https://console.developers.google.com/)
2. Create a new project
3. Enable the YouTube Data API v3
4. Create credentials for an API key
5. Copy your API key to use with the setup script

## How to Use

### Analyzing a Video

1. Select "Video" in the search toggle
2. Enter a YouTube video ID (e.g., dQw4w9WgXcQ) or URL
3. Click "Analyze" to view sentiment analysis for that video

### Analyzing a Channel

1. Select "Channel" in the search toggle
2. Enter a YouTube channel ID, username, or URL
3. Click "Analyze" to see sentiment analysis across the channel's videos

### Understanding the Results

- **Sentiment Distribution**: Shows the percentage of positive, negative, and neutral comments
- **Comment Analysis**: Lists individual comments with their analyzed sentiment
- **Content Insights**: Provides actionable recommendations based on sentiment analysis

## Technical Details

### Sentiment Analysis Model

The sentiment analysis model:

- Is based on a Random Forest classifier with TF-IDF vectorization
- Is trained on a diverse set of YouTube-style comments
- Analyzes text for positive, negative, or neutral sentiment
- Includes preprocessing steps like stopword removal and lemmatization

### Docker Implementation

The Docker setup includes:

- Multi-stage build for efficiency
- Ability to use a model pre-trained on your local machine
- Frontend React application served by Nginx
- Backend Flask API running with Gunicorn
- Volume mounts for API keys and data persistence

## Manual Setup (For Development)

### Backend Setup

1. Create a virtual environment:
   ```
   cd backend
   python -m venv new_youtube_venv
   source new_youtube_venv/bin/activate  # On Windows: new_youtube_venv\Scripts\activate
   ```

2. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

3. Set up your YouTube API key:
   ```
   # Add your API key to backend/scraper/api_key.txt
   ```

4. Train the sentiment model:
   ```
   python train_model_locally.py
   ```

5. Run the Flask API:
   ```
   cd backend
   python app.py
   ```

### Frontend Setup

1. Install dependencies:
   ```
   cd frontend
   npm install
   ```

2. Start the development server:
   ```
   npm start
   ```

3. Access the application at http://localhost:3000

## Project Structure

### Backend Components

- **Flask API**: RESTful API serving sentiment analysis data
- **YouTube API Integration**: Fetches video and channel data
- **Data Scraper**: Collects trending videos and their comments
- **Sentiment Analysis**: Processes comments to determine sentiment
- **Pre-trained Model**: Ready-to-use sentiment classification model

### Frontend Components

- **React SPA**: Single Page Application with React Router
- **Analysis Dashboard**: Interactive UI for displaying insights
- **Data Visualization**: Charts and graphs using Chart.js

## Technologies Used

- **Backend**: Python, Flask, scikit-learn, NLTK
- **Frontend**: React, React Router, Chart.js
- **Infrastructure**: Docker, Nginx, Gunicorn

## Future Enhancements

- More advanced deep learning models for improved sentiment accuracy
- Temporal analysis showing sentiment changes over time
- Keyword extraction from comments
- Topic clustering for comment themes
- Enhanced visualization options
- Export options for analysis results