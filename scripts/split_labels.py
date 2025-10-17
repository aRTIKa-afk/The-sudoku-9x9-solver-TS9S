#!/usr/bin/env python3
# scripts/split_labels.py
# Creates train/val splits and label->index map from dataset/labels.csv
import os, json, pandas as pd
from sklearn.model_selection import StratifiedShuffleSplit

input_csv = "dataset/labels.csv"   # path to your labels.csv
out_dir = "annotations"
os.makedirs(out_dir, exist_ok=True)

df = pd.read_csv(input_csv, dtype=str)
# Normalize label column: empty strings or NaN -> 'empty'
df['label'] = df['label'].fillna('').astype(str)
df['label'] = df['label'].apply(lambda x: 'empty' if x.strip() == '' else x.strip())

# Fix paths: if they aren't prefixed with dataset/, add it
def fix_path(p):
    p = str(p)
    if p.startswith("dataset/"):
        return p
    if os.path.isabs(p):
        return p
    return os.path.join("dataset", p)

df['filename'] = df['filename'].apply(fix_path)

# Stratified split (10% val)
labels = df['label']
try:
    split = StratifiedShuffleSplit(n_splits=1, test_size=0.10, random_state=42)
    train_idx, val_idx = next(split.split(df, labels))
    df.iloc[train_idx].to_csv(os.path.join(out_dir, "labels_train.csv"), index=False)
    df.iloc[val_idx].to_csv(os.path.join(out_dir, "labels_val.csv"), index=False)
except Exception as e:
    # Fallback: simple random split preserving distribution as much as possible
    print("Stratified split failed (maybe too few samples per class). Doing random split. Error:", e)
    df = df.sample(frac=1, random_state=42).reset_index(drop=True)
    val_count = max(1, int(0.1 * len(df)))
    df.iloc[val_count:].to_csv(os.path.join(out_dir, "labels_train.csv"), index=False)
    df.iloc[:val_count].to_csv(os.path.join(out_dir, "labels_val.csv"), index=False)

# Save label2idx map
unique_labels = sorted(df['label'].unique())
label2idx = {lab: i for i, lab in enumerate(unique_labels)}
with open(os.path.join(out_dir, "label2idx.json"), "w", encoding="utf-8") as f:
    json.dump(label2idx, f, ensure_ascii=False, indent=2)

print("Saved train/val splits to", out_dir)
print("Labels saved:", unique_labels)
print("Label->idx map saved to annotations/label2idx.json")
