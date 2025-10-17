import pandas as pd
import os

dataset = pd.read_csv('labels.csv')
for j in range(1, 10):
    for i in range(1, 180):
        if os.system(f"rename .\\dataset\\{j}\\{i}.jpg {i}.jpg") == 0:      #exist?
            dataset.loc[len(dataset)] = [f"{j}/{i}.jpg", j]

for i in range(1, 1800):
        if os.system(f"rename .\\dataset\\empty\\{i}.jpg {i}.jpg") == 0:    #exist?
            dataset.loc[len(dataset)] = [f"empty/{i}.jpg", ""]

dataset.to_csv('labels.csv')
