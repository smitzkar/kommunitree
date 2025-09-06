# https://gpiozero.readthedocs.io/en/stable/recipes.html#

from gpiozero import Button, LED

# gpiozero uses BCM/GPIO pin numbering by default and this can't be changed
# I added pi pinout references as png from pinout.xyz

button = Button(2) # GPIO2 = 3 on pi (BOARD3) = SDA I2C 

while True:
    if button.is_pressed:
        print("Button is pressed")
    else:
        print("Button is not pressed")