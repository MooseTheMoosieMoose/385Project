#======================================================================================
# 385 Final project
# Moose Abou-Harb, Gabriel Schiavone-Hennighausen, Nicole Torbett, Clarisse Yapjoco
# Plant Balancer With Automatic Hand Contraption Thing

#==IMPORTS==============================================================================
import time
import serial


#==LOCAL CLASSES=========================================================================
#A simple rolling buffer that allows for averages to be taken over a rolling stack of samples
class RollingBuffer:
    # Constructor
    def __init__(self, buffer_size: int, initial_value: int = 0):
        self._buffer = []
        self._buffer_size = buffer_size
        self._new_insert_point = 0
        for i in range(0, buffer_size):
            self._buffer.append(initial_value)

    # Push a new value into the rolling buffer, its placement is automatic
    def push(self, value: float) -> None:
        self._buffer[self._new_insert_point] = value
        if (self._new_insert_point + 1 == self._buffer_size):
            self._new_insert_point = 0
        else:
            self._new_insert_point += 1

    # Pull an average from the buffer
    def avg(self) -> float:
        return (sum(self._buffer) / self._buffer_size)
    
    #Returns a size
    def getSize(self) -> int:
        return self._buffer_size

#==GLOBALS================================================================================
#Master Serial port
ser = serial.Serial('/dev/ttyUSB2', 9600)

#Main rolling buffer for light, heat, and moisture
light_buffer = RollingBuffer(50, 300)
heat_buffer = RollingBuffer(50, 90)
moisture_buffer = RollingBuffer(50, 100)

#==MAIN====================================================================================
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
            print("Main Loop Executing...")
            main_loop()

#Main loop triggered by the periodic nature of main()
def main_loop():
    #Update analog levels, cur_x gets the most recent values
    cur_light, cur_temp, cur_moisture = analog_read()
    light_buffer.push(cur_light)
    heat_buffer.push(cur_temp)
    moisture_buffer.push(cur_moisture)

    #Get the rolling average of analog levels
    avg_light: int = light_buffer.avg()
    avg_temp: int = heat_buffer.avg()
    avg_moisture: int = moisture_buffer.avg()

    print(f"Light: {cur_light}, Heat: {cur_temp}, Moisture: {cur_moisture}")

    #TODO decide how to act


#==HELPER FUNCTIONS=========================================================================
def analog_read() -> tuple[int, int, int]:
    #Ping the analog module to get new values
    ser.write(7)

    #Listen back
    data: bytes = bytes()
    try:
        num_bytes = 6
        data = ser.read(num_bytes)
    except serial.SerialException as e:
        print(f"Error reading from serial port: {e}")

    #If the bytes are succsessfully read, then bytes is a 6 byte structure, of 3 shorts
    light_val: int = int.from_bytes(data[0:2])
    therm_val: int = int.from_bytes(data[2:4])
    moist_val: int = int.from_bytes(data[4:])

    #Return thruple of analog inputs
    return tuple(light_val, therm_val, moist_val)



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