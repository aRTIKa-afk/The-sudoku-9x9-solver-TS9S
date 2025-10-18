from PIL import ImageGrab as imgGrb
import mouse
import keyboard
import os
from PIL import Image, UnidentifiedImageError
import torch
from torchvision import transforms, models
from tqdm import tqdm
import torch.nn.functional as F
import numpy as np
import pandas as pd
import time
from ultralytics import YOLO

modelY = YOLO("yolo.pt")

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


_default_transform = transforms.Compose([
    transforms.Resize((128,128)),
    transforms.ToTensor(),
    transforms.Normalize(mean=[0.485,0.456,0.406], std=[0.229,0.224,0.225])
])


def predict_pil_image(model, idx2label, pil_img, device='cpu', transform=None):
    """
    model: загруженная модель
    idx2label: dict mapping index (str) -> label (строка)
    pil_img: PIL.Image.Image (RGB или L)
    device: 'cpu' или torch.device
    transform: torchvision.transforms (если None, используется _default_transform)
    Возвращает: (pred_label, confidence_float, logits_numpy)
    """
    if transform is None:
        transform = _default_transform

    if pil_img.mode != 'RGB':
        pil_img = pil_img.convert('RGB')

    x = transform(pil_img).unsqueeze(0).to(device)  # shape [1,C,H,W]
    model.to(device)
    model.eval()
    with torch.no_grad():
        logits = model(x)                    # [1, num_classes]
        probs = F.softmax(logits, dim=1)     # probabilities
        conf, pred_idx = torch.max(probs, dim=1)
        pred_idx = int(pred_idx.item())
        conf = float(conf.item())
        # idx2label keys are strings; try str(pred_idx)
        label = idx2label.get(str(pred_idx), idx2label.get(pred_idx, "UNKNOWN"))
        return label, conf, logits.squeeze(0).cpu().numpy()

ckpt_path = "ocr.pth"


device = torch.device('cpu')

model, idx2label = load_ckpt(ckpt_path, device) 
screenshot = imgGrb.grab( include_layered_windows=True)

results = modelY(screenshot)
print(results)

x1, y1, x2, y2 = results[0].boxes[0].xyxy[0]
x1, y1, x2, y2 = int(x1), int(y1), int(x2), int(y2)
print(x1, y1, x2, y2)

'''
print("Наведите курсор на левый верхний угол судоку и нажмите SPACE")
keyboard.wait("space")
x1, y1 = mouse.get_position()

print("Наведите курсор на правый нижний угол судоку и нажмите SPACE")
keyboard.wait("space")
x2, y2 = mouse.get_position()

print((x1,y1,x2,y2))
'''


screenshot = imgGrb.grab(bbox=(x1,y1,x2,y2), include_layered_windows=True)
screenshot.save('a.jpg')


step_x = (x2 - x1)/9
step_y = (y2 - y1)/9

s = ""

print("""
      +------------------------+
      |  начальный вид судоку  | 
      +------------------------+
      """)
for j in range(1, 10):
    print("\t  ", end='')
    for i in range(1, 10):
        sc = screenshot
        num,a,a = predict_pil_image(model, idx2label, sc.crop(((i-1)*step_x, (j-1)*step_y, (i)*step_x, (j)*step_y)), device)
        if num == "empty": num = '#'
        print(num, end=' ')
        s+=num+' '
    print()

isnt_solved = os.system(f"a.exe {s}")

answer = pd.read_csv("out.csv").to_numpy()


mouse.move(x1 + step_x/2, y1 + step_y/2)
mouse.click()

for i in range(1, 10):
    for j in range(1, 10):
        time.sleep(0.1)
        if i%2==1:
            keyboard.send(str(answer[i-1][j-1]))
            keyboard.send('right')
        else:
            keyboard.send(str(answer[i-1][9-j]))
            keyboard.send('left')
    keyboard.send('down')
