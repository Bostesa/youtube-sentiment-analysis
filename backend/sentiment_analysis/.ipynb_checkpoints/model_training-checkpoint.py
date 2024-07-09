import torch
from torch.utils.data import DataLoader, TensorDataset
from transformers import BertForSequenceClassification, AdamW
from sklearn.metrics import accuracy_score, classification_report

def create_data_loader(features, labels, batch_size=32):
    data = TensorDataset(features, labels)
    return DataLoader(data, batch_size=batch_size, shuffle=True)

def train_advanced_model(X_train, y_train, X_val, y_val, epochs=3, batch_size=8, device='cuda'):
    model = BertForSequenceClassification.from_pretrained('bert-base-uncased', num_labels=3).to(device)
    optimizer = AdamW(model.parameters(), lr=2e-5)

    train_dataloader = create_data_loader(X_train, y_train, batch_size)
    val_dataloader = create_data_loader(X_val, y_val, batch_size)

    for epoch in range(epochs):
        model.train()
        total_loss = 0
        for batch in train_dataloader:
            batch = [item.to(device) for item in batch]
            inputs, labels = batch
            model.zero_grad()
            outputs = model(inputs, labels=labels)
            loss = outputs.loss
            total_loss += loss.item()
            loss.backward()
            optimizer.step()

        avg_train_loss = total_loss / len(train_dataloader)
        print(f"Average train loss: {avg_train_loss}")

        model.eval()
        total_eval_loss = 0
        for batch in val_dataloader:
            batch = [item.to(device) for item in batch]
            inputs, labels = batch
            with torch.no_grad():
                outputs = model(inputs, labels=labels)
            loss = outputs.loss
            total_eval_loss += loss.item()

        avg_val_loss = total_eval_loss / len(val_dataloader)
        print(f"Validation loss: {avg_val_loss}")

    return model

def evaluate_model(model, X_test, y_test, device='cuda'):
    test_dataloader = create_data_loader(X_test, y_test, batch_size=32)
    model.eval()
    test_preds = []
    test_labels = []
    for batch in test_dataloader:
        inputs, labels = tuple(t.to(device) for t in batch)
        with torch.no_grad():
            outputs = model(inputs)
        logits = outputs[0]
        test_preds.extend(torch.argmax(logits, dim=1).cpu().numpy())
        test_labels.extend(labels.cpu().numpy())

    print("Test Accuracy:", accuracy_score(test_labels, test_preds))
    print("Classification Report:\n", classification_report(test_labels, test_preds))
