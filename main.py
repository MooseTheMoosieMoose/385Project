#======================================================================================
# 385 Final project
# Moose Abou-Harb, Gabriel Schiavone-Hennighausen, Nicole Torbett, Clarisse Yapjoco
# Plant Balancer With Automatic Water Dispenser (might give up on hand)

#==IMPORTS==============================================================================
import time, sys, struct
import serial
import serial.tools.list_ports
import RPi.GPIO as GPIO
# import pigpio
from rpi_lcd import LCD

servo_pin1 = 18
servo_pin2 = 17
servo_pin3 = 27
# pi = pigpio.pi()

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

#Test PWM controller
GPIO.setwarnings(False)
GPIO.setmode(GPIO.BCM)
GPIO.setup(20, GPIO.OUT) #Buzzer pin

#Test PWM servos
GPIO.setup(servo_pin1, GPIO.OUT) #Servo1 pin
pwm1 = GPIO.PWM(servo_pin1, 50)
pwm1.start(0)
GPIO.setup(servo_pin2, GPIO.OUT) #Servo2 pin
pwm2 = GPIO.PWM(servo_pin2, 50)
pwm2.start(0)
GPIO.setup(servo_pin3, GPIO.OUT) #Servo3 pin
pwm3 = GPIO.PWM(servo_pin3, 50)
pwm3.start(0)

lcd = LCD()

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

    if (cur_light > 600) or (cur_temp > 150):
        sound_da_alarm("Yo plant", "hot, Gamer!!")
    elif (cur_light < 200):
        sound_da_alarm("Yo plant", "dark, Gamer!!")
    elif (cur_moisture > 375):
        sound_da_alarm("Yo plant", "dry, Gamer!!")
        activate_watering_hand_v1() 
    elif (cur_moisture < 250):
        sound_da_alarm("Yo plant", "*MOIST*, Gamer!!")
    elif (cur_temp < 50):
        sound_da_alarm("Yo plant", "frigid, Gamer!!")
    else:
        lcd.text("Plant is Healthy!", 1)

    # Practice code
    # update_LCD()
    # activate_watering_hand_v1()
    # activate_watering_hand_v2()


#==HELPER FUNCTIONS=========================================================================
def config_GPIO() -> None:
    #Config individual pins
    GPIO.setup(20, GPIO.OUT) #Buzzer pin
    GPIO.output(20, False)
    GPIO.setup(servo_pin1, GPIO.OUT) #Servo1 pin
    GPIO.setup(servo_pin2, GPIO.OUT) #Servo2 pin
    GPIO.setup(servo_pin3, GPIO.OUT) #Servo3 pin

def analog_read() -> tuple[int, int, int]:
    #Flush the buffer
    while ser.in_waiting > 0:
        _ = ser.read_all()
    
    #Wait for a sync byte, then log
    while True:
        if ser.in_waiting >= 1:
            test_code = ser.read(1)
            print("\tPending arduino transmission...")
            #Advance only if the read byte is the sync byte, 253
            if (int.from_bytes(test_code) == 253):
                print("\tReceiving!...")

                #Wait until ready
                while ser.in_waiting < 6:
                    pass

                #Pull
                data: bytes = ser.read(6)
                unpacked: tuple[int, int, int] = struct.unpack("<3h", data)
                return unpacked

#Nicole - pass an update to the LCD, unknown how this works, we can reframe it later
def update_LCD():
    lcd.text("Hello",1)

#Moose - make the buzzer go brrrr
def sound_buzzer():
    state = False
    GPIO.output(20, state)
    for _ in range(0, 2500):
        GPIO.output(20, state)
        state = not state
        time.sleep(0.0001)
    GPIO.output(20, False)

#Clarisse - servo code to water
def set_angle(angle):
    duty = 2 + (angle / 18)
    GPIO.output(servo_pin1, True)
    GPIO.output(servo_pin2, True)
    GPIO.output(servo_pin3, True)
    pwm1.ChangeDutyCycle(duty)
    pwm2.ChangeDutyCycle(duty)
    pwm3.ChangeDutyCycle(duty)
    time.sleep(0.5)
    GPIO.output(servo_pin1, False)
    GPIO.output(servo_pin2, False)
    GPIO.output(servo_pin3, False)
    pwm1.ChangeDutyCycle(0)
    pwm2.ChangeDutyCycle(0)
    pwm3.ChangeDutyCycle(0)    

def activate_watering_hand_v1():
    set_angle(180)
    time.sleep(1)
    set_angle(0)
    time.sleep(1)

# def activate_watering_hand_v2():
#     pi.set_servo_pulsewidth(17, 2000)  # Servo 1 - center
#     pi.set_servo_pulsewidth(18, 2000)  # Servo 2 - far left
#     pi.set_servo_pulsewidth(27, 2000)  # Servo 3 - far right
#     time.sleep(2)  # Let the servos move

#     pi.set_servo_pulsewidth(17, 1000)  # Servo 1 - center
#     pi.set_servo_pulsewidth(18, 1000)  # Servo 2 - far left
#     pi.set_servo_pulsewidth(27, 1000)  # Servo 3 - far right
#     time.sleep(2)  # Let the servos move

def sound_da_alarm(line1: str, line2: str) -> None:
        lcd.text("! ALERT !",1)
        sound_buzzer()
        lcd.clear()
        lcd.text(line1, 1)
        lcd.text(line2, 2)
        sound_buzzer()
        time.sleep(3)
        lcd.clear()

if __name__ == "__main__":
    main()
    