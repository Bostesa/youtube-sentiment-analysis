# main.py

import torch
import pandas as pd
from data_preparation import load_and_clean_data
from labeling_and_prompt import create_labels, train_test_data_split
from feature_extraction import extract_features_bert
from model_training import train_advanced_model, evaluate_model
from sklearn.model_selection import train_test_split

def main(file_paths):
    device = 'cuda' if torch.cuda.is_available() else 'cpu'
    
    # Load and clean data from multiple files
    data = pd.concat([load_and_clean_data(file_path) for file_path in file_paths], ignore_index=True)
    
    # Create labels
    data = create_labels(data)
    
    # Split data
    train_data, test_data = train_test_data_split(data)
    
    # Extract features
    X_train = extract_features_bert(train_data, device=device)
    y_train = torch.tensor(train_data['label'].values)
    X_test = extract_features_bert(test_data, device=device)
    y_test = torch.tensor(test_data['label'].values)
    
    # Further split train data into train and validation sets
    X_train_ids, X_val_ids, X_train_masks, X_val_masks, y_train, y_val = train_test_split(
        torch.tensor(X_train[0]), torch.tensor(X_train[1]), y_train, test_size=0.1, random_state=42
    )
    X_train = (X_train_ids, X_train_masks)
    X_val = (X_val_ids, X_val_masks)

    # Train model
    model = train_advanced_model(X_train, y_train, X_val, y_val, device=device)
    
    # Evaluate model
    evaluate_model(model, (torch.tensor(X_test[0]), torch.tensor(X_test[1])), y_test, device=device)
    
    return model

if __name__ == "__main__":
    file_paths = [
        "C:\\Users\\nates\\Youtube-app\\backend\\scraper\\output\\24.28.06_GB_videos.csv",
        "C\\Users\\nates\\Youtube-app\\backend\\scraper\\output\\24.28.06_US_videos.csv"
    ]
    model = main(file_paths)
