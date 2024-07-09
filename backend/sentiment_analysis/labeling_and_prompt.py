# labeling_and_prompt.py

from sklearn.model_selection import train_test_split

def create_labels(data):
    # Example: simplistic labeling for demonstration (actual labeling might require manual labeling or advanced techniques)
    data['label'] = data['comment_text'].apply(lambda x: 1 if 'good' in x or 'great' in x else 0 if 'bad' in x or 'terrible' in x else 2)
    return data

def train_test_data_split(data):
    return train_test_split(data, test_size=0.2, random_state=42)
