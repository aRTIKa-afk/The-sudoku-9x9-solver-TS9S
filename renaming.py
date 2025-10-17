import os

k = 1


for count in range(1, 31):
    for j in range(1, 10):
        for i in range(1, 10):
            if os.system(f"rename cell-{count}-{i}-{j}.jpg {k}.jpg") == 0: #exist?
                k += 1 

            