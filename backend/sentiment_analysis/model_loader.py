"""
Model loader utility to load the trained BERT sentiment analysis model.
This provides a clean interface for the Flask API to use the model.
"""

import os
import torch
import pickle
from transformers import BertTokenizer, BertForSequenceClassification
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class SentimentAnalyzer:
    """Class to handle sentiment analysis with BERT model."""
    
    def __init__(self):
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.model = None
        self.tokenizer = None
        self.model_loaded = False
        self.label_map = {0: 'negative', 1: 'positive', 2: 'neutral'}
        
    def load_model(self, models_dir='models'):
        """Load the BERT model and tokenizer."""
        try:
            # First try to load model info
            model_info_path = os.path.join(models_dir, 'model_info.pkl')
            
            if os.path.exists(model_info_path):
                with open(model_info_path, 'rb') as f:
                    model_info = pickle.load(f)
                
                # Load model and tokenizer using paths from model_info
                model_path = model_info['model_path']
                tokenizer_path = model_info['tokenizer_path']
                
                if 'labels' in model_info:
                    self.label_map = model_info['labels']
                
                logger.info(f"Loading model from {model_path}")
                
                self.model = BertForSequenceClassification.from_pretrained(model_path)
                self.tokenizer = BertTokenizer.from_pretrained(tokenizer_path)
                self.model.to(self.device)
                self.model.eval()
                
                logger.info(f"Model loaded successfully with metrics: {model_info.get('metrics', 'N/A')}")
                self.model_loaded = True
                return True
            else:
                # Try direct loading if model_info not found
                logger.warning("model_info.pkl not found, trying direct loading")
                model_path = os.path.join(models_dir, 'bert_sentiment_model')
                tokenizer_path = os.path.join(models_dir, 'bert_tokenizer')
                
                if os.path.exists(model_path) and os.path.exists(tokenizer_path):
                    self.model = BertForSequenceClassification.from_pretrained(model_path)
                    self.tokenizer = BertTokenizer.from_pretrained(tokenizer_path)
                    self.model.to(self.device)
                    self.model.eval()
                    
                    logger.info("Model loaded successfully via direct loading")
                    self.model_loaded = True
                    return True
                else:
                    logger.error(f"Model files not found at {model_path} or {tokenizer_path}")
                    return False
        except Exception as e:
            logger.error(f"Error loading model: {str(e)}")
            return False
    
    def analyze_comment(self, comment, max_length=128):
        """Analyze a single comment for sentiment."""
        if not self.model_loaded:
            logger.warning("Model not loaded, attempting to load...")
            if not self.load_model():
                logger.error("Failed to load model, returning neutral")
                return 'neutral'
        
        try:
            # Tokenize
            encoding = self.tokenizer(
                comment,
                add_special_tokens=True,
                max_length=max_length,
                return_token_type_ids=False,
                padding='max_length',
                truncation=True,
                return_attention_mask=True,
                return_tensors='pt'
            )
            
            # Move to device
            input_ids = encoding['input_ids'].to(self.device)
            attention_mask = encoding['attention_mask'].to(self.device)
            
            # Get prediction
            with torch.no_grad():
                outputs = self.model(input_ids=input_ids, attention_mask=attention_mask)
                logits = outputs.logits
                prediction = torch.argmax(logits, dim=1).item()
            
            # Map to sentiment label
            sentiment = self.label_map.get(prediction, 'neutral')
            return sentiment
            
        except Exception as e:
            logger.error(f"Error analyzing comment: {str(e)}")
            return 'neutral'
    
    def analyze_comments(self, comments):
        """Analyze multiple comments and return results with sentiment distribution."""
        if not comments:
            return [], {'positive': 0, 'negative': 0, 'neutral': 0}
        
        results = []
        sentiment_counts = {'positive': 0, 'negative': 0, 'neutral': 0}
        
        for comment in comments:
            sentiment = self.analyze_comment(comment)
            results.append({'comment': comment, 'sentiment': sentiment})
            sentiment_counts[sentiment] += 1
        
        return results, sentiment_counts

# Singleton instance for reuse
sentiment_analyzer = SentimentAnalyzer()