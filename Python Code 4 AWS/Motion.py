# Author: Mateusz Szalkowski
# Home Security System

# all required imports
import pigpio
import thread
from send_file import store_to_bucket
import ssl
import RPi.GPIO as GPIO
import time
import picamera
from time import sleep

#i2c bus of Pi 3
i2c_bus = 1
#tmp sensor address on the i2c bus
addr = 0x48

dev_pi = pigpio.pi()
dev_tmp = dev_pi.i2c_open(i2c_bus, addr, 0)
register_n = 0


# read certificates required for authentication
rootca = r'/home/pi/Desktop/pythonForAWS/certs/rootCA.pem'
certificate = r'/home/pi/Desktop/pythonForAWS/certs/certificate.pem.crt'
keyfile = r'/home/pi/Desktop/pythonForAWS/certs/private.pem.key'
hostName = open("/home/pi/Desktop/pythonForAWS/certs/hostName.txt", "r")

# define gpio pins (board mode)
pir_sensor      = 37
led_test        = 35
#smoke, temperature, relay and others coming up shortly...

# setup gpio ports
GPIO.setwarnings(False)
GPIO.setmode(GPIO.BOARD)
GPIO.setup(pir_sensor, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
GPIO.setup(led_test, GPIO.OUT)
# Get camera instance
camera = picamera.PiCamera()

# setup AWS IoT
Librarycheck = True
try:
    import paho.mqtt.client as mqtt
except ImportError:
    Librarycheck = False
    print("paho-mqtt python package missing...")

# setup connection, try to connect and wait for incoming messages
c = mqtt.Client()

c.tls_set(rootca, certfile=certificate, keyfile=keyfile,
          cert_reqs=ssl.CERT_REQUIRED, tls_version=ssl.PROTOCOL_TLSv1_2, ciphers=None)

# FUNCTIONS================================================================================================
#Calculate temperature based on the first word and the first byte
def tmp_reading(byte0, word0):
    l4b = (word0 & 0b1111000000000000)>>12
    temperature = ((byte0<<4) | l4b) * 0.0625
    return temperature

# on connection send a message to console
def onc(c, userdfata, flags, rc):
    print("successfully connected to Amazon with RC ", rc)
    c.subscribe("mytopic/iot")
    c.subscribe("mytopic/iot2")
    c.subscribe("mytopic/iot/led")


# wait for a message from aws console topic.
def onm(c, userdata, msg):
    m = msg.payload.decode()
    print(m)
    if m == 'hello':
        c.publish('mytopic/iot', 'Hello from Python to Amazon')
    elif m == 'on':
        GPIO.output(led_test, GPIO.HIGH)
    elif m == 'off':
        GPIO.output(led_test, GPIO.LOW)



# A function to detect interrupt event.
def my_callback(channel):
    print("Event detected on pir sensor")
    take_snap()

# A function to take a snapshot and save in specific folder.
# date_string is used to take a picture and add current date as a name to prevent image duplication.
def take_snap():
    print("Taking snap\n")
    date_string = time.strftime("%Y-%m-%d-%H:%M:%S")
    path        = '/home/pi/Desktop/Camera_test_python/pictures/'
    date        = 'image_'+date_string
    ext         = '.jpg'
    full_path   = path+date+ext

    #Save camera picture locally and pass location to store2bucket function
    camera.capture(full_path)
    
    #Create new thread
    try:
        thread.start_new_thread(store_to_bucket, (full_path, date,))
    except:
        print("Error: unable to start thread")
#store_to_bucket(full_path, date)
    c.publish('mytopic/iot', 'Picture taken.')
    c.publish('mytopic/iot2', 'Picture taken2.')

# Setup interrupt service routine when pir sensor state changed detected.
GPIO.add_event_detect(pir_sensor, GPIO.RISING, callback=my_callback)

c.connect(hostName.read(), 8883)
sleep(2)

c.loop_start()
c.on_connect = onc
c.on_message = onm

# main function
try:
    while True:
        if GPIO.input(37) > 0.5:
            print("Movement dtetected, isr triggered!")

        else:
            print("No movement")

        t_byte = dev_pi.i2c_read_byte_data(dev_tmp, 0)
        t_word = dev_pi.i2c_read_word_data(dev_tmp, 0)
        t = tmp_reading(t_byte, t_word)
        print("Temperature {} C".format(t))
        sleep(1)

        

# if CTRL-C is pressed the main loop will break.
except KeyboardInterrupt:
    print("Exitting")


finally:
    GPIO.remove_event_detect(pir_sensor)  # Turn off event detect interrupt
    GPIO.cleanup()  # Reset ports
    c.loop_stop()
    c.disconnect()
    r = dev_pi.i2c_close(dev_tmp)
    print("Connection terminated")
