from PIL import ImageGrab as imgGrb
import mouse
import keyboard
import time

#--------calibration block --------------

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
step_x = (x2 - x1)/9
step_y = (y2 - y1)/9

for count in range(1, 1000):
    screenshot = imgGrb.grab(bbox=(x1,y1,x2,y2)) #make screenshot
    for j in range(1, 10):
        for i in range(1, 10):
            sc = screenshot
            sc.crop(((i-1)*step_x, (j-1)*step_y, (i)*step_x, (j)*step_y)).save(f"cell-{count}-{i}-{j}.jpg") #crop and save cells with numbers
    mouse.move(ng_x2, ng_y2)    #new game menu
    time.sleep(0.1)
    mouse.click()
    time.sleep(0.5)
    mouse.move(ez_x2, ez_y2)    #new easy game 
    time.sleep(0.1)
    mouse.click()
    mouse.move(100, 100)
    time.sleep(15)

    