# src/data_utils.py
import torch
from torch.utils.data import Dataset
from PIL import Image
import pandas as pd
import os, json

class DigitDataset(Dataset):
    def __init__(self, csv_file, label_map_file, transform=None):
        self.df = pd.read_csv(csv_file, dtype=str)
        self.df['label'] = self.df['label'].fillna('').apply(lambda x: 'empty' if str(x).strip()=='' else str(x).strip())
        # load label2idx (keys are strings)
        with open(label_map_file, 'r', encoding='utf-8') as f:
            self.label2idx = json.load(f)
        self.transform = transform

    def __len__(self):
        return len(self.df)

    def __getitem__(self, idx):
        row = self.df.iloc[idx]
        img_path = row['filename']
        if not os.path.isabs(img_path) and not img_path.startswith("dataset"):
            img_path = os.path.join("dataset", img_path)
        img = Image.open(img_path).convert('RGB')
        if self.transform:
            img = self.transform(img)
        label = self.label2idx[row['label']]
        return img, label, img_path
