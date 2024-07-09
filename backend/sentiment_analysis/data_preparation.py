# data_preparation.py

import pandas as pd
import re

def clean_comment(comment):
    # Remove special characters, URLs, and numbers
    comment = re.sub(r"http\S+|www\S+|https\S+", '', comment, flags=re.MULTILINE)
    comment = re.sub(r'\@\w+|\#','', comment)
    comment = re.sub(r'[^A-Za-z\s]+', '', comment)
    comment = re.sub(r'\s+', ' ', comment).strip()
    return comment

def load_and_clean_data(file_path):
    data = pd.read_csv(file_path)
    data['comment_text'] = data['comment_text'].apply(clean_comment)
    return data
