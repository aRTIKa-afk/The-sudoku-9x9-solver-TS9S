import os
import cv2



for i in range(1,10):
    os.system(f"mkdir {i}")
os.system(f"mkdir empty")


for count in range(1, 100):
    for j in range(1, 10):
        for i in range(1, 10):
            img = cv2.imread(f"cell-{count}-{i}-{j}.jpg")
            cv2.imshow('Image', img)
            key = cv2.waitKey(0)
            if key & 0xFF == ord('1'):
                os.system(f"move ./raw_data/cell-{count}-{i}-{j}.jpg ./dataset/1/")
            elif key & 0xFF == ord('2'):
                os.system(f"move ./raw_data/cell-{count}-{i}-{j}.jpg ./dataset/2/")
            elif key & 0xFF == ord('3'):
                os.system(f"move ./raw_data/cell-{count}-{i}-{j}.jpg ./dataset/3/")
            elif key & 0xFF == ord('4'):
                os.system(f"move ./raw_data/cell-{count}-{i}-{j}.jpg ./dataset/4/")
            elif key & 0xFF == ord('5'):
                os.system(f"move ./raw_data/cell-{count}-{i}-{j}.jpg ./dataset/5/")
            elif key & 0xFF == ord('6'):
                os.system(f"move ./raw_data/cell-{count}-{i}-{j}.jpg ./dataset/6/")
            elif key & 0xFF == ord('7'):
                os.system(f"move ./raw_data/cell-{count}-{i}-{j}.jpg ./dataset/7/")
            elif key & 0xFF == ord('8'):
                os.system(f"move ./raw_data/cell-{count}-{i}-{j}.jpg ./dataset/8/")
            elif key & 0xFF == ord('9'):
                os.system(f"move ./raw_data/cell-{count}-{i}-{j}.jpg ./dataset/9/")
            else:
                os.system(f"move ./raw_data/cell-{count}-{i}-{j}.jpg ./dataset/empty/")