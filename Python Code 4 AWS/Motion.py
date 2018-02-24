# Author: Mateusz Szalkowski
# Home Security System

# all required imports
import pigpio
import thread
from threading import Thread
from send_file import store_to_bucket
import ssl
import RPi.GPIO as GPIO
import time
import datetime
import picamera
from time import sleep
import sys

#delay for temperature publishing
delay_temp = 10

sn_number = '000001'


# read certificates required for authentication
rootca = r'/home/pi/Desktop/pythonForAWS/certs/rootCA.pem'
certificate = r'/home/pi/Desktop/pythonForAWS/certs/certificate.pem.crt'
keyfile = r'/home/pi/Desktop/pythonForAWS/certs/private.pem.key'
hostName = open("/home/pi/Desktop/pythonForAWS/certs/hostName.txt", "r")

# define gpio pins (board mode)
pir_sensor      = 37
led_test        = 35
#i2c bus of Pi 3
i2c_bus = 1
#tmp sensor address on the i2c bus
addr = 0x48
dev_pi = pigpio.pi()
dev_tmp = dev_pi.i2c_open(i2c_bus, addr, 0)
register_n = 0


#define IoT mqtt topics
topic_iot           = "mytopic/iot"
topic_iot2          = "mytopic/iot2"
topic_led           = "mytopic/iot/led"
topic_tmp           = "mytopic/iot/temp_read"


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
def tmp_reading():
    try:
        count = 0        
        while True:
            count += 1
            t_byte = dev_pi.i2c_read_byte_data(dev_tmp, 0)
            t_word = dev_pi.i2c_read_word_data(dev_tmp, 0)
            l4b = ( t_word & 0b1111000000000000)>>12
            temperature = ((t_byte<<4) | l4b) * 0.0625
            timestamp = datetime.datetime.now()
            print(' Temperature: {} C   Date: {} '. format(temperature, timestamp))
            msg = '"Device": "{:s}", "Temperature": "{}", "Loop": "{}"'.format(sn_number, temperature, count)
            msg = '{'+msg+'}'
            c.publish(topic_tmp, msg, 1)
            time.sleep(delay_temp) 
              
    except KeyboardInterrupt:
        pass


# on connection send a message to console
def onc(c, userdfata, flags, rc):
    print("successfully connected to Amazon with RC ", rc)
    c.subscribe(topic_iot)
    c.subscribe(topic_iot2)
    c.subscribe(topic_led)
    c.subscribe(topic_tmp)


# wait for a message from aws console topic.
def onm(c, userdata, msg):
    m = msg.payload.decode()
    print(m)
    if m == 'hello':
        c.publish(topic_iot, 'Hello from Python to Amazon')
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
    c.publish(topic_iot, 'Picture taken.')
    c.publish(topic_iot2, 'Picture taken2.')

# Setup interrupt service routine when pir sensor state changed detected.
GPIO.add_event_detect(pir_sensor, GPIO.RISING, callback=my_callback)

c.connect(hostName.read(), 8883)
sleep(2)

c.loop_start()
c.on_connect = onc
c.on_message = onm

#start temperature read thread
background_thread = Thread(target=tmp_reading, args=())
background_thread.start()

# main function
try:
    
    while True:
        if GPIO.input(37) > 0.5:
            print("\rMovement dtetected, isr triggered!")

        else:
            print("No movement")
        sleep(1)

        

# if CTRL-C is pressed the main loop will break.
except KeyboardInterrupt:
    print("Exitting")


finally:
    GPIO.remove_event_detect(pir_sensor)  # Turn off event detect interrupt
    GPIO.cleanup()      # Reset ports
    c.loop_stop()
    c.disconnect()
    r = dev_pi.i2c_close(dev_tmp)
    print("Connection terminated")
