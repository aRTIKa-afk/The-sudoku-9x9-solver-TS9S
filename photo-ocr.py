import easyocr
import re
import cv2
import numpy as np
from PIL import Image, ImageEnhance, ImageOps

reader = easyocr.Reader(['en'])
image = Image.open('./image.png')


w, h = image.size
cell_w = w // 9
cell_h = h // 9

table = []

for row_idx in range(9):
    row = []
    for col_idx in range(9):
        
        left   = col_idx * cell_w
        upper  = row_idx * cell_h
        right  = left   + cell_w
        lower  = upper  + cell_h
        cell = image.crop((left, upper, right, lower))

        
        cell = cell.convert('L')
        enhancer = ImageEnhance.Contrast(cell)
        cell = enhancer.enhance(2)   

        new_size = (cell_w*2, cell_h*2)
        cell = cell.resize(new_size, Image.Resampling.LANCZOS)
        cell = ImageOps.expand(cell, border=10, fill=255)

        cell_np = np.array(cell)
        _, cell_thr = cv2.threshold(cell_np, 0, 255,
                                     cv2.THRESH_BINARY + cv2.THRESH_OTSU)

        result = reader.readtext(cell_thr,
                                 detail=0,
                                 allowlist='0123456789')

        digit = 0
        for txt in result:
            if len(txt) == 1 and txt.isdigit():
                digit = int(txt)
                break

        row.append(digit)
    table.append(row)

for i in table:
    for j in i:
        print(j, end=' ')
    print('\n', end='')
