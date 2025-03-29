import os
import joblib
import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.ensemble import RandomForestClassifier
from sklearn.pipeline import Pipeline
from sklearn.metrics import accuracy_score, classification_report
import nltk
from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer
import re

# Ensure the models directory exists
os.makedirs('models', exist_ok=True)

# Download necessary NLTK resources
nltk.download('stopwords', quiet=True)
nltk.download('wordnet', quiet=True)
nltk.download('punkt', quiet=True)

# Sample data with YouTube-like comments and their sentiment
# This is a simplified dataset for demonstration
sample_data = [
    # Positive comments
    ("This video was so helpful, thank you for sharing!", "positive"),
    ("I love your content, keep up the great work!", "positive"),
    ("This is exactly what I needed to see today, thank you!", "positive"),
    ("Your explanation made this topic so much clearer", "positive"),
    ("Best video I've seen on this subject, subscribed!", "positive"),
    ("The production quality is amazing, very professional", "positive"),
    ("I've learned so much from your channel, thanks!", "positive"),
    ("Excellent content as always, very informative", "positive"),
    ("You explain things so well, very easy to understand", "positive"),
    ("Great video! I've shared it with all my friends", "positive"),
    
    # Negative comments
    ("I was disappointed with this video, expected more depth", "negative"),
    ("This explanation is confusing, doesn't make sense", "negative"),
    ("Too many ads in this video, very annoying", "negative"),
    ("The audio quality is terrible, couldn't hear properly", "negative"),
    ("You got several facts wrong, please do better research", "negative"),
    ("This video is way too long for such a simple topic", "negative"),
    ("Stop clickbaiting with your thumbnails, wasted my time", "negative"),
    ("The background music is too loud, distracting", "negative"),
    ("This content seems copied from other channels", "negative"),
    ("Your editing style is very jarring and hard to watch", "negative"),
    
    # Neutral comments
    ("I have a question about the topic at 3:45", "neutral"),
    ("Could you make a video about related topics?", "neutral"),
    ("What camera do you use for filming?", "neutral"),
    ("Is there a part two to this video?", "neutral"),
    ("I'm new to your channel, just found it today", "neutral"),
    ("Do you have any resources for further reading?", "neutral"),
    ("I've seen similar content on other channels", "neutral"),
    ("First time watching one of your videos", "neutral"),
    ("What software do you use for editing?", "neutral"),
    ("I'll try this method and see if it works for me", "neutral"),
]

# Expand the dataset with more YouTube-typical comments
more_data = [
    # More positive comments
    ("Wow this is amazing content!", "positive"),
    ("Thanks for the tips, really useful!", "positive"),
    ("This changed my life, thank you so much", "positive"),
    ("Your channel deserves more subscribers", "positive"),
    ("I've been waiting for this video, worth it!", "positive"),
    ("The editing in this video is top notch", "positive"),
    ("You made my day with this content", "positive"),
    ("Finally someone explained this clearly", "positive"),
    ("Incredible work as always!", "positive"),
    ("This is why I love your channel", "positive"),
    ("Absolutely brilliant explanation", "positive"),
    ("You're the best YouTuber for this topic", "positive"),
    ("Subscribed immediately after watching", "positive"),
    ("Great job on this video!", "positive"),
    ("This is exactly what I was searching for", "positive"),
    
    # More negative comments
    ("Disliked, this was a waste of time", "negative"),
    ("You should stick to your old content", "negative"),
    ("I can't believe how wrong this is", "negative"),
    ("Unsubscribed after this video", "negative"),
    ("This video is just a copy of others", "negative"),
    ("You didn't even address the main issue", "negative"),
    ("The intro is way too long, get to the point", "negative"),
    ("Misleading title, didn't deliver what was promised", "negative"),
    ("This advice is actually harmful", "negative"),
    ("So disappointed with the quality lately", "negative"),
    ("Stop trying to sell us products in every video", "negative"),
    ("The constant jump cuts are annoying", "negative"),
    ("This feels rushed and poorly researched", "negative"),
    ("Not helpful at all", "negative"),
    ("Your older videos were much better", "negative"),
    
    # More neutral comments
    ("Watching this at 2x speed", "neutral"),
    ("Will you cover this topic more in future videos?", "neutral"),
    ("Just found your channel through recommendations", "neutral"),
    ("I'm taking notes on this", "neutral"),
    ("How often do you upload new videos?", "neutral"),
    ("Are these techniques applicable to other situations?", "neutral"),
    ("Interesting perspective on this topic", "neutral"),
    ("Do you have a playlist with similar content?", "neutral"),
    ("Watching this for a school project", "neutral"),
    ("I've heard different approaches to this", "neutral"),
    ("Can you provide sources for your information?", "neutral"),
    ("Is there an update to this since it was posted?", "neutral"),
    ("Maybe consider doing a collaboration with other creators", "neutral"),
    ("How long did it take you to research this?", "neutral"),
    ("I'll be trying this method tomorrow", "neutral"),
]

# Combine all data
all_data = sample_data + more_data

# Convert to DataFrame
df = pd.DataFrame(all_data, columns=['comment_text', 'sentiment'])

# Define sentiment mapping
sentiment_map = {
    'positive': 1,
    'negative': 0,
    'neutral': 2
}

# Convert sentiment labels to numeric values
df['label'] = df['sentiment'].map(sentiment_map)

# Text preprocessing function
def preprocess_text(text):
    # Convert to lowercase
    text = text.lower()
    
    # Remove special characters, URLs, and numbers
    text = re.sub(r"http\S+|www\S+|https\S+", '', text, flags=re.MULTILINE)
    text = re.sub(r'\@\w+|\#','', text)
    text = re.sub(r'[^a-zA-Z\s]', '', text)
    
    # Tokenize text
    tokens = nltk.word_tokenize(text)
    
    # Remove stopwords and lemmatize
    stop_words = set(stopwords.words('english'))
    lemmatizer = WordNetLemmatizer()
    tokens = [lemmatizer.lemmatize(token) for token in tokens if token not in stop_words]
    
    return ' '.join(tokens)

# Apply preprocessing
df['processed_text'] = df['comment_text'].apply(preprocess_text)

# Split the data into training and testing sets
from sklearn.model_selection import train_test_split
X_train, X_test, y_train, y_test = train_test_split(df['processed_text'], df['label'], test_size=0.2, random_state=42)

# Create and train the model
sentiment_pipeline = Pipeline([
    ('tfidf', TfidfVectorizer(max_features=5000)),
    ('clf', RandomForestClassifier(n_estimators=100, random_state=42))
])

sentiment_pipeline.fit(X_train, y_train)

# Evaluate the model
y_pred = sentiment_pipeline.predict(X_test)
print("Accuracy:", accuracy_score(y_test, y_pred))
print("\nClassification Report:")
print(classification_report(y_test, y_pred, target_names=['negative', 'positive', 'neutral']))

# Save the model
joblib.dump(sentiment_pipeline, 'models/sentiment_model.pkl')
print("\nDefault sentiment model trained and saved to 'models/sentiment_model.pkl'")