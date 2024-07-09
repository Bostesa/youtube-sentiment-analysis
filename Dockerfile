# Use an official Python runtime as a parent image
FROM python:3.11.7

# Set the working directory in the container
WORKDIR /app

# Copy the requirements file first to leverage Docker cache
COPY backend/sentiment_analysis/requirements.txt /app/requirements.txt

# Install dependencies
RUN pip install --no-cache-dir -r /app/requirements.txt

# Copy the rest of the application code
COPY backend/sentiment_analysis /app/sentiment_analysis

# Set the default command to run the main script
CMD ["python", "/app/sentiment_analysis/main.py"]
