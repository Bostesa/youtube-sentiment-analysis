# feature_extraction.py

from transformers import BertTokenizer, BertModel
import torch

def extract_features_bert(data, max_length=128, device='cuda'):
    tokenizer = BertTokenizer.from_pretrained('bert-base-uncased')
    model = BertModel.from_pretrained('bert-base-uncased').to(device)
    
    def tokenize_and_pad(text):
        encoding = tokenizer.encode_plus(
            text,
            max_length=max_length,
            truncation=True,
            padding='max_length',
            return_tensors='pt'
        )
        return encoding['input_ids'].squeeze(), encoding['attention_mask'].squeeze()

    input_ids = []
    attention_masks = []
    
    for text in data['comment_text']:
        ids, mask = tokenize_and_pad(text)
        input_ids.append(ids)
        attention_masks.append(mask)
    
    input_ids = torch.stack(input_ids).to(device)
    attention_masks = torch.stack(attention_masks).to(device)
    
    with torch.no_grad():
        model_output = model(input_ids, attention_mask=attention_masks)
    
    return model_output.last_hidden_state[:, 0, :].cpu().numpy()  # Get the embeddings from [CLS] token
