"""
Script to train the advanced BERT-based sentiment analysis model locally on your device.
This creates a high-accuracy model that Docker will use, making the application run faster.
"""

import os
import sys
import subprocess
import time

print("=== YouTube Sentiment Analysis Advanced Model Trainer ===")
print("This script will train the BERT-based sentiment analysis model on your local device.")
print("The trained model will be used by the Docker container for faster performance.\n")

# Create necessary directories
os.makedirs('backend/sentiment_analysis/models', exist_ok=True)

# Check Python dependencies
required_packages = [
    'torch', 
    'transformers', 
    'pandas', 
    'scikit-learn', 
    'nltk',
    'joblib'
]

print("Checking required Python packages...")
missing_packages = []

for package in required_packages:
    try:
        __import__(package)
        print(f"✓ {package} is installed")
    except ImportError:
        missing_packages.append(package)
        print(f"✗ {package} is not installed")

if missing_packages:
    print("\nSome required packages are missing. Installing them now...")
    subprocess.check_call([sys.executable, "-m", "pip", "install"] + missing_packages)
    print("All required packages installed successfully.")

print("\nStarting model training process...")
print("This may take several minutes depending on your hardware.")
print("Training with BERT transformer model for high accuracy sentiment analysis.\n")

start_time = time.time()

# Run the advanced model training script
try:
    print("Running advanced_model.py")
    result = subprocess.run(
        [sys.executable, "backend/sentiment_analysis/advanced_model.py"],
        check=True,
        text=True
    )
    
    end_time = time.time()
    training_time = end_time - start_time
    
    print(f"\nTraining completed successfully in {training_time:.2f} seconds!")
    print(f"The trained model has been saved to 'backend/sentiment_analysis/models/'")
    
    print("\nYou can now build and run the Docker container with:")
    print("  docker-compose up -d")
    print("\nThe container will use your pre-trained model for faster sentiment analysis.")
    
except subprocess.CalledProcessError as e:
    print(f"\nError during model training: {e}")
    print("Please check the error message above and try again.")
    sys.exit(1)