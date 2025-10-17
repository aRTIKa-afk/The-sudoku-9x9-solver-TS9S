# src/train_cnn.py
import os, sys
# Ensure src dir is in path so data_utils can be imported when running "python src/train_cnn.py"
sys.path.append(os.path.dirname(__file__))
from data_utils import DigitDataset
import torch, torch.nn as nn
from torch.utils.data import DataLoader
import torchvision.transforms as T
from torchvision import models
import argparse
from tqdm import tqdm
import json

def train_epoch(model, loader, criterion, optimizer, device):
    model.train()
    running_loss = 0.0
    correct = 0
    total = 0
    for imgs, labels, _ in tqdm(loader, desc='train'):
        imgs, labels = imgs.to(device), labels.to(device)
        optimizer.zero_grad()
        outputs = model(imgs)
        loss = criterion(outputs, labels)
        loss.backward()
        optimizer.step()
        running_loss += loss.item() * imgs.size(0)
        preds = outputs.argmax(dim=1)
        correct += (preds == labels).sum().item()
        total += labels.size(0)
    return running_loss / total, correct / total

def val_epoch(model, loader, criterion, device):
    model.eval()
    running_loss = 0.0
    correct = 0
    total = 0
    with torch.no_grad():
        for imgs, labels, _ in tqdm(loader, desc='val'):
            imgs, labels = imgs.to(device), labels.to(device)
            outputs = model(imgs)
            loss = criterion(outputs, labels)
            running_loss += loss.item() * imgs.size(0)
            preds = outputs.argmax(dim=1)
            correct += (preds == labels).sum().item()
            total += labels.size(0)
    return running_loss / total, correct / total

def main(args):
    device = torch.device('cuda' if torch.cuda.is_available() and not args.no_cuda else 'cpu')
    with open(args.label_map, 'r', encoding='utf-8') as f:
        label2idx = json.load(f)
    num_classes = len(label2idx)

    train_transform = T.Compose([
        T.Resize((128,128)),
        T.RandomRotation(10),
        T.RandomAffine(0, translate=(0.05,0.05)),
        T.ToTensor(),
        T.Normalize(mean=[0.485,0.456,0.406], std=[0.229,0.224,0.225])
    ])
    val_transform = T.Compose([
        T.Resize((128,128)),
        T.ToTensor(),
        T.Normalize(mean=[0.485,0.456,0.406], std=[0.229,0.224,0.225])
    ])

    train_ds = DigitDataset(args.train_csv, args.label_map, transform=train_transform)
    val_ds   = DigitDataset(args.val_csv, args.label_map, transform=val_transform)

    train_loader = DataLoader(train_ds, batch_size=args.batch_size, shuffle=True, num_workers=4)
    val_loader   = DataLoader(val_ds,   batch_size=args.batch_size, shuffle=False, num_workers=4)

    model = models.resnet18(pretrained=True)
    model.fc = nn.Linear(model.fc.in_features, num_classes)
    model = model.to(device)

    criterion = nn.CrossEntropyLoss()
    optimizer = torch.optim.Adam(model.parameters(), lr=args.lr)

    best_acc = 0.0
    os.makedirs(args.out_dir, exist_ok=True)

    for epoch in range(1, args.epochs+1):
        train_loss, train_acc = train_epoch(model, train_loader, criterion, optimizer, device)
        val_loss, val_acc = val_epoch(model, val_loader, criterion, device)
        print(f"Epoch {epoch}/{args.epochs} | train loss {train_loss:.4f} acc {train_acc:.4f} | val loss {val_loss:.4f} acc {val_acc:.4f}")
        if val_acc >= best_acc:
            best_acc = val_acc
            torch.save({
                'epoch': epoch,
                'model_state': model.state_dict(),
                'optimizer_state': optimizer.state_dict(),
                'label2idx': label2idx
            }, os.path.join(args.out_dir, 'best.pth'))
            print('Saved best model. Val acc:', best_acc)

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--train_csv', default='annotations/labels_train.csv')
    parser.add_argument('--val_csv', default='annotations/labels_val.csv')
    parser.add_argument('--label_map', default='annotations/label2idx.json')
    parser.add_argument('--out_dir', default='experiments/saved_models/digit_cnn')
    parser.add_argument('--epochs', type=int, default=15)
    parser.add_argument('--batch_size', type=int, default=32)
    parser.add_argument('--lr', type=float, default=1e-4)
    parser.add_argument('--no_cuda', action='store_true')
    args = parser.parse_args()
    main(args)
