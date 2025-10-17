import os
import sys
import json
from PIL import Image, UnidentifiedImageError
import torch
from torchvision import transforms, models
import argparse
import pandas as pd
from tqdm import tqdm

def load_ckpt(ckpt_path, device):
    if not os.path.exists(ckpt_path):
        raise FileNotFoundError(f"Checkpoint not found: {ckpt_path}")
    ckpt = torch.load(ckpt_path, map_location=device)
    if 'label2idx' not in ckpt:
        raise KeyError("Checkpoint does not contain 'label2idx'.")
    label2idx = ckpt['label2idx']

    
    idx2label = {}
    for lab, idx in label2idx.items():
        
        try:
            idx_int = int(idx)
        except Exception:
            
            try:
                idx_int = int(str(idx))
            except Exception:
                idx_int = idx
        idx2label[str(idx_int)] = lab

    
    model = models.resnet18(weights=None)  
    model.fc = torch.nn.Linear(model.fc.in_features, len(label2idx))
    model.load_state_dict(ckpt['model_state'])
    model.to(device)
    model.eval()
    return model, idx2label

def infer_folder(model, idx2label, folder, device):
    transform = transforms.Compose([
        transforms.Resize((128,128)),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.485,0.456,0.406], std=[0.229,0.224,0.225])
    ])
    rows = []
    for root, _, files in os.walk(folder):
        for f in files:
            if f.lower().endswith(('.jpg','.png','.jpeg')):
                path = os.path.join(root, f)
                try:
                    img = Image.open(path).convert('RGB')
                except (FileNotFoundError, UnidentifiedImageError, OSError) as e:
                    print(f"Warning: cannot open {path}: {e}")
                    rows.append({'filename': path, 'pred': 'error', 'note': str(e)})
                    continue

                x = transform(img).unsqueeze(0).to(device)
                with torch.no_grad():
                    out = model(x)
                    pred = int(out.argmax(dim=1).item())
                    label = idx2label.get(str(pred), idx2label.get(pred, "UNKNOWN"))
                rows.append({'filename': path, 'pred': label})
    return rows

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--ckpt', default='experiments/saved_models/digit_cnn/best.pth')
    parser.add_argument('--input_folder', default='dataset')
    parser.add_argument('--out_csv', default='predictions.csv')
    args = parser.parse_args()

    device = torch.device('cpu')  # у вас нет GPU — явно CPU
    try:
        model, idx2label = load_ckpt(args.ckpt, device)
    except Exception as e:
        print("Error loading checkpoint:", e)
        raise

    rows = infer_folder(model, idx2label, args.input_folder, device)
    df = pd.DataFrame(rows)
    df.to_csv(args.out_csv, index=False)
    print('Saved predictions to', args.out_csv)
    print("First 10 predictions:")
    print(df.head(10))
