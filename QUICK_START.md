# Quick Start Guide - YouTube Sentiment Analysis App

This guide will help you get the YouTube Sentiment Analysis app running in minutes.

## Prerequisites

- [Docker](https://www.docker.com/products/docker-desktop) installed on your system
- A YouTube Data API key

## 1. Get a YouTube Data API Key (Skip if you already have one)

1. Go to the [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select an existing one
3. In the sidebar, click on "APIs & Services" > "Library"
4. Search for "YouTube Data API v3" and enable it
5. Go to "APIs & Services" > "Credentials"
6. Click "Create Credentials" > "API key"
7. Copy your new API key

## 2. Set Up and Run the Application

### On Windows:

1. Download or clone this repository
2. Open Command Prompt in the project directory
3. Run the setup script and enter your API key when prompted:
   ```
   setup.bat
   ```
4. Start the application:
   ```
   docker-compose up -d
   ```

### On macOS/Linux:

1. Download or clone this repository
2. Open Terminal in the project directory
3. Make the setup script executable and run it:
   ```
   chmod +x setup.sh
   ./setup.sh
   ```
4. Start the application:
   ```
   docker-compose up -d
   ```

## 3. Use the Application

1. Open your web browser and go to: http://localhost
2. Use the search bar to analyze:
   - **Videos**: Enter a YouTube video URL or ID
   - **Channels**: Enter a YouTube channel URL, username, or ID

## Analyzing Video Sentiment

1. Select "Video" in the search toggle
2. Enter a YouTube video URL (e.g., https://www.youtube.com/watch?v=dQw4w9WgXcQ)
3. Click "Analyze"
4. View the sentiment distribution and individual comment analysis

## Analyzing Channel Sentiment

1. Select "Channel" in the search toggle
2. Enter a YouTube channel URL (e.g., https://www.youtube.com/c/GoogleDevelopers)
3. Click "Analyze"
4. View the channel overview and sentiment trends across videos

## Stopping the Application

When you're done, you can stop the application with:
```
docker-compose down
```

## Troubleshooting

### API Quota Exceeded

If you see errors about API quota being exceeded:
- The YouTube Data API has daily quotas
- Try using a different API key or wait until the next day

### Container Won't Start

If the Docker container won't start:
- Make sure ports 80 and 5000 are available on your system
- Check that Docker is running
- Try restarting Docker

For more detailed information, refer to the full README.md file.