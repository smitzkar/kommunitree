"""
https://gpiozero.readthedocs.io/en/stable/recipes.html#button


mock pins -> deve laptop
https://gpiozero.readthedocs.io/en/stable/api_pins.html#mock-pins

"""

# #MARK: mock
from gpiozero import Device, LED, PWMLED
from gpiozero.pins.mock import MockFactory

Device.pin_factory = MockFactory() # sets all future pin assingment to be pretend only

def main():

    led = LED(3)
    led.value # 0 
    led.on() 
    led.value # 1
    led.off()
    led.value # 0

    # will run say_hello whenever the button is pressed  -> callback
    from gpiozero import Button
    from signal import pause

    def say_hello():
        print("Hello!")
        if led.value == 0:
            print("Praise the sun!")
            led.on()
        else:
            print("Darkness, my old friend!")
            led.off()

    button = Button(2)

    button.when_pressed = say_hello  # note: no parantheses -> assignment, not execution


    # even easier:

    led2 = LED(10)
    button2 = Button(11)

    led2.source = button2 # when button is pressed, led on, else off

    button2.pin.drive_low()     # to manually "press" the button
    button2.pin.drive_high()    # to release the button
    
    #MARK: time based
    from gpiozero import LED, TimeOfDay
    from datetime import time
    from signal import pause

    led = LED(2)
    tod = TimeOfDay(time(9), time(10)) # turns on at 9, off at 10am

    tod.when_activated = led.on
    tod.when_deactivated = led.off
    #pause()
    
    
    #MARK: rotary encoder
    # super simple!
    # https://gpiozero.readthedocs.io/en/stable/api_input.html#rotaryencoder more options
    from gpiozero import RotaryEncoder
    from gpiozero.tools import scaled_half
    rotor = RotaryEncoder(21, 20)
    led = PWMLED(5)
    led.source = scaled_half(rotor.values)



    pause() # keeps the script running indefinitely (until user stops it with keyboard interrupt or such)


if __name__ == "__main__":
    main()