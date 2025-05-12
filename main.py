#======================================================================================
# 385 Final project
# Moose Abou-Harb, Gabriel Schiavone-Hennighausen, Nicole Torbett, Clarisse Yapjoco
# Plant Balancer With Automatic Hand Contraption Thing

#==IMPORTS==============================================================================
import time, sys, struct
import serial
import serial.tools.list_ports
import RPi.GPIO as GPIO


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
#Master Serial port - I am losing my fucking mind
ports = serial.tools.list_ports.comports()
p_target = ""
for p in ports:
    print(f"Found Port: {p.description}")
    if ("uno" in p.description.lower() or "arduino" in p.description.lower() or "ttyacm" in p.description.lower()):
        print(f"Port match found, setting DEV_PATH to {p.device}")
        p_target = p.device
try:
    ser = serial.Serial(p_target, 9600)
    print(f"Serial connection created!")
except:
    print(f"Enumeration targeted: {p_target}, which failed to open!")
    sys.exit()

#Main rolling buffer for light, heat, and moisture
light_buffer = RollingBuffer(50, 300)
heat_buffer = RollingBuffer(50, 90)
moisture_buffer = RollingBuffer(50, 100)

#==MAIN====================================================================================
#Program entry point, will fire main_loop every 1 minute
def main():
    #The number of seconds between each firing of the main loop
    update_delta: int = 5

    #Set up GPIO pins
    config_GPIO()

    #Get the current time, fire main loop once
    cur_time: int = int(time.time())
    main_loop()

    #TODO program hypothetically runs forever? Brainstorm ideas for meaningful termination without linux syscm CTRL C
    while True:
        next_time: int = int(time.time())
        if (next_time - cur_time) > update_delta:
            cur_time = next_time
            main_loop()

#Main loop triggered by the periodic nature of main()
def main_loop():
    print("Main Loop Executing...")
    #Update analog levels, cur_x gets the most recent values
    cur_light, cur_temp, cur_moisture = analog_read()
    light_buffer.push(cur_light)
    heat_buffer.push(cur_temp)
    moisture_buffer.push(cur_moisture)

    #Get the rolling average of analog levels
    avg_light: int = light_buffer.avg()
    avg_temp: int = heat_buffer.avg()
    avg_moisture: int = moisture_buffer.avg()

    print(f"\tLight: {cur_light}, Heat: {cur_temp}, Moisture: {cur_moisture}")

    #Decide if the plant has had enough light, then SCREAM
    if (avg_light > 600 or avg_temp > 150 or avg_moisture > 700):
        sound_buzzer()

    #TODO watering, heat and light


#==HELPER FUNCTIONS=========================================================================
def config_GPIO() -> None:
    GPIO.setwarnings(False)
    GPIO.setmode(GPIO.BCM)

    #Config individual pins
    GPIO.setup(29, GPIO.OUT) #Buzzer pin

def analog_read() -> tuple[int, int, int]:
    #Flush the buffer
    while ser.in_waiting > 0:
        _ = ser.read_all()
    
    #Wait for a sync byte, then log
    while True:
        if ser.in_waiting >= 1:
            test_code = ser.read(1)
            print("\tPending arduino transmission...")
            if (int.from_bytes(test_code) == 253):
                print("\tReceiving!...")
                #Wait until ready
                if ser.in_waiting >= 6:
                    data: bytes = ser.read(6)
                    unpacked: tuple[int, int, int] = struct.unpack("<3h", data)
                    return unpacked

#Nicole - pass an update to the LCD, unknown how this works, we can reframe it later
def update_LCD():
    pass

#Moose - make the buzzer go brrrr
def sound_buzzer():
    GPIO.output(29, True)
    time.sleep(0.5)
    GPIO.output(29, False)

#Clarisse - servo code to water
def activate_watering_hand():
    pass

if __name__ == "__main__":
    main()
    