import pandas as pd
import torch
import numpy as np
from transformers import Trainer, TrainingArguments, AutoTokenizer, AutoModelForSequenceClassification


label_df = pd.read_csv('./model/label_to_index.csv')
label_df = label_df[['label', 'index']]
label2idx = {}
idx2label = {}
for _,row in label_df.iterrows():
  label2idx[row['label']] = row['index']
  idx2label[row['index']] = row['label']

def collate_fn(batch):
    input_ids = torch.stack([x[0] for x in batch])
    attention_mask = torch.stack([x[1] for x in batch])
    labels = torch.tensor([x[2] for x in batch])
    return {'input_ids': input_ids, 'attention_mask': attention_mask, 'labels': labels}


# Load the tokenizer and model
tokenizer = AutoTokenizer.from_pretrained("airesearch/wangchanberta-base-att-spm-uncased")
model = AutoModelForSequenceClassification.from_pretrained("./model/model.pth", num_labels=len(label2idx))


trainer = Trainer(
    model=model,
    data_collator=collate_fn
)


def predict(input_texts):
    label = [0 for i in range(len(input_texts))]
    input_texts_arr = np.array(input_texts).astype(str)
    encoded_input = tokenizer(input_texts_arr.tolist(), padding=True, truncation=True, max_length=128)

    encoded_data = torch.utils.data.TensorDataset(torch.tensor(encoded_input['input_ids']),
                                                  torch.tensor(encoded_input['attention_mask']),
                                                  torch.tensor(label))
    
    predicted = trainer.predict(encoded_data)
    pred_list = []
    for i,pred in enumerate(predicted[0]) :
        l_np = np.asarray(pred)
        pred_list.append((input_texts[i],idx2label[l_np.argmax()]))
    
    return pred_list