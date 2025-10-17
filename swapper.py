import os
from random import randint as rnd
for j in range(1, 21):
    for k in range(1, 19):
        for i in range(1, 10):
            num = rnd(1, 40)
            print(os.system(f'move .\\images\\val\\img-{k}-{i}.jpg .\\images\\'), end=' ')
            print(os.system(f'rename .\\images\\img-{k}-{i}.jpg img-{k}-{num}.jpg'), end=' ')
            print(os.system(f'move .\\images\\train\\img-{k}-{num}.jpg .\\'), end=' ')
            print(os.system(f'rename img-{k}-{num}.jpg img-{k}-{i}.jpg'), end=' ')
            print(os.system(f'move .\\images\\img-{k}-{num}.jpg .\\images\\train\\'), end=' ')
            print(os.system(f'move img-{k}-{i}.jpg .\\images\\val\\'), )
