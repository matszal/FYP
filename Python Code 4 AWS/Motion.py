# Author: Mateusz Szalkowski
# Home Security System

# all required imports
#import boto3
#import send_file
from send_file import store_to_bucket
import ssl
import RPi.GPIO as GPIO
import time
import picamera
from time import sleep

# read certificates required for authentication
rootca = r'/home/pi/Desktop/pythonForAWS/certs/rootCA.pem'
certificate = r'/home/pi/Desktop/pythonForAWS/certs/certificate.pem.crt'
keyfile = r'/home/pi/Desktop/pythonForAWS/certs/private.pem.key'
# hostName = r'/home/pi/Desktop/pythonForAWS/certs/hostName.txt'
hostName = open("/home/pi/Desktop/pythonForAWS/certs/hostName.txt", "r")

# define gpio pins (board mode)
pirSensor = 37
#smoke, temperature, relay and others coming up shortly...

# setup gpio portsx
GPIO.setwarnings(False)
GPIO.setmode(GPIO.BOARD)
GPIO.setup(pirSensor, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)


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
# on connection send a message to console
def onc(c, userdfata, flags, rc):
    print("successfully connected to Amazon with RC ", rc)
    c.subscribe("mytopic/iot")
    c.subscribe("mytopic/iot2")


# wait for a message from aws console topic.
def onm(c, userdata, msg):
    m = msg.payload.decode()
    print(m)
    if m == 'hello':
        c.publish('mytopic/iot', 'Hello from Python to Amazon')


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
    camera.capture(full_path)
    #camera.capture('/home/pi/Desktop/Camera_test_python/pictures/image_' + date_string + '.jpg')
    #send a full path to be stored in s3. Threads required!!!
    store_to_bucket(full_path, date)
    print("Picture captured and saved\n")
    c.publish('mytopic/iot', 'Picture taken.')
    c.publish('mytopic/iot2', 'Picture taken2.')

# Setup interrupt service routine when pir sensor state changed detected.
GPIO.add_event_detect(pirSensor, GPIO.RISING, callback=my_callback)


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
        sleep(0.5)

        # c.loop_forever()

# if CTRL-C is pressed the main loop will break.
except KeyboardInterrupt:
    print("Exitting")


finally:
    GPIO.remove_event_detect(pirSensor)  # Turn off event detect interrupt
    GPIO.cleanup()  # Reset ports
    c.loop_stop()
    c.disconnect()
    print("Connection terminated")





