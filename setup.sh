#!/bin/bash

echo "===== YouTube Sentiment Analysis App Setup ====="
echo

# Create necessary directories
mkdir -p backend/scraper/output
mkdir -p backend/sentiment_analysis/models

# Request YouTube API key
echo "Please enter your YouTube Data API key:"
read api_key

# Save the API key to the required file
echo $api_key > backend/scraper/api_key.txt
echo "API key saved to backend/scraper/api_key.txt"

# Set up sample country codes
echo "US" > backend/scraper/country_codes.txt
echo "Sample country code (US) added to country_codes.txt"

echo
echo "Setup complete! You can now run the application with:"
echo "docker-compose up -d"
echo
echo "Access the application at: http://localhost"