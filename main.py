# 385 Final project
# Moose Abou-Harb, Gabriel Schiavone-Hennighausen, Nicole Torbett, Clarisse Yapjoco
# Plant Balancer With Automatic Hand Contraption Thing

import time

#Program entry point, will fire main_loop every 1 minute
def main():
    #The number of seconds between each firing of the main loop
    update_delta: int = 60

    #Get the current time, fire main loop once
    cur_time: int = int(time.time())
    main_loop()

    #TODO program hypothetically runs forever? Brainstorm ideas for meaningful termination without linux syscm CTRL C
    while True:
        next_time: int = int(time.time())
        if (next_time - cur_time) > update_delta:
            main_loop()

#Main loop triggered by the periodic nature of main()
def main_loop():
    pass

#Nicole - pass an update to the LCD, unknown how this works, we can reframe it later
def update_LCD():
    pass

#Moose - make the buzzer go brrrr
def sound_buzzer():
    pass

#Moose - get the current heat level
def get_heat_level():
    pass

#Moose - get the current light level
def get_light_level():
    pass

#Gabe - get the current moisture level
def get_moisture_level():
    pass

#Clarisse - servo code to water
def activate_watering_hand():
    pass

if __name__ == "__main__":
    main()