from PIL import ImageGrab as imgGrb
import mouse
import keyboard
import time
from random import randint as rand

for i in range(1, 21):
    
    print("Наведите курсор на левый верхний угол судоку и нажмите SPACE")
    keyboard.wait("space")
    x1, y1 = mouse.get_position()

    print("Наведите курсор на правый нижний угол судоку и нажмите SPACE")
    keyboard.wait("space")
    x2, y2 = mouse.get_position()

    print("Наведите курсор на new game и нажмите SPACE")
    keyboard.wait("space")
    ng_x2, ng_y2 = mouse.get_position()

    print("Наведите курсор на easy и нажмите SPACE")
    keyboard.wait("space")
    ez_x2, ez_y2 = mouse.get_position()

    time.sleep(5)

    for k in range(1, 41):
        im = imgGrb.grab(include_layered_windows=True)
        im.save(f'images/train/img-{i}-{k}.jpg')
        width, height = im.size

        class_id = 0  
        x_center = (x1 + x2) / 2 / width 
        y_center = (y1 + y2) / 2 / height 
        w = (x2 - x1) / width 
        h = (y2 - y1) / height 

        f = open(f'labels/train/img-{i}-{k}.txt', 'w')
        f.write(f'{class_id} {x_center} {y_center} {w} {h}')
        f.close()

        mouse.move(ng_x2, ng_y2)
        time.sleep(0.1)
        mouse.click()
        time.sleep(0.5)
        mouse.move(ez_x2, ez_y2)
        time.sleep(0.1)
        mouse.click()
        mouse.move(100, 100)
        time.sleep(5)
        mouse.move(rand(x1, x2), rand(y1, y2))
        mouse.click()
        mouse.move(100, 100)
        time.sleep(0.5)

    for k in range(1, 11):
        im = imgGrb.grab(include_layered_windows=True)
        im.save(f'images/val/img-{i}-{k}.jpg')
        width, height = im.size

        class_id = 0  
        x_center = (x1 + x2) / 2 / width 
        y_center = (y1 + y2) / 2 / height 
        w = (x2 - x1) / width 
        h = (y2 - y1) / height 

        f = open(f'labels/val/img-{i}-{k}.txt', 'w')
        f.write(f'{class_id} {x_center} {y_center} {w} {h}')
        f.close()

        mouse.move(ng_x2, ng_y2)
        time.sleep(0.1)
        mouse.click()
        time.sleep(0.5)
        mouse.move(ez_x2, ez_y2)
        time.sleep(0.1)
        mouse.click()
        mouse.move(100, 100)
        time.sleep(5)
        mouse.move(rand(x1, x2), rand(y1, y2))
        mouse.click()
        mouse.move(100, 100)
        time.sleep(0.5)