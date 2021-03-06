# Author: Mateusz Szalkowski
# Home Security System

# all required imports
import pigpio
import thread
from threading import Thread
from send_file import store_to_bucket
import I2C_LCD_driver
import ssl
import RPi.GPIO as GPIO
import time
import datetime
import picamera
from time import sleep
import sys
import json

# a time delay for temperature database store interval
delay_temp          = 2
heater_delay        = 1

# read certificates required for authentication
rootca = r'/home/pi/Desktop/pythonForAWS/certs/rootCA.pem'
certificate = r'/home/pi/Desktop/pythonForAWS/certs/certificate.pem.crt'
keyfile = r'/home/pi/Desktop/pythonForAWS/certs/private.pem.key'
hostName = open("/home/pi/Desktop/pythonForAWS/certs/hostName.txt", "r")

# define gpio pins (board mode)
pir_sensor          = 37
led_device          = 35
led_heater          = 33

# i2c bus of Pi 3
i2c_bus             = 1
# address devices on the i2c bus
tmp_sensor_addr     = 0x48
lcd_screen          = 0x27
dev_pi = pigpio.pi()
dev_tmp = dev_pi.i2c_open(i2c_bus, tmp_sensor_addr , 0)
register_n          = 0
#setup lcd
mylcd = I2C_LCD_driver.lcd()

# setup gpio ports
GPIO.setwarnings(False)
GPIO.setmode(GPIO.BOARD)
GPIO.setup(pir_sensor, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
GPIO.setup(led_device, GPIO.OUT)
GPIO.setup(led_heater, GPIO.OUT)
GPIO.output(led_heater, GPIO.LOW)

# get camera instance
camera  = picamera.PiCamera()

# define IoT mqtt topics
topic_iot           = "mytopic/iot"
topic_led           = "mytopic/iot/led"
topic_heat          = "mytopic/iot/heat"
topic_tmp2          = "mytopic/iot/temp_read2"


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
# calculate temperature based on the first word and the first byte
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
            millis = time.time()

            print(' Temperature: {} C   Date: {} '. format(temperature, timestamp))
            mylcd.lcd_clear()
            mylcd.lcd_display_string("Temp: %.2f%% C" % temperature, 2)
            #msg = '"Date": "{}", "Device": "{:s}", "Temperature": "{}", "Loop": "{}"'.format(timestamp, sn_number, temperature, count)
            msg = '"Millis": "{}", "Temperature": "{}"'.format(millis, temperature)
            msg = '{'+msg+'}'
            #return temperature
            c.publish(topic_tmp2, msg, 1)
            time.sleep(delay_temp)

    except KeyboardInterrupt:
        pass


# on connection send a message to console
def onc(c, userdfata, flags, rc):
    print("successfully connected to Amazon with RC ", rc)
    c.subscribe(topic_iot)
    c.subscribe(topic_led)
    c.subscribe(topic_tmp2)
    c.subscribe(topic_heat)


# wait for a message from aws console topic.
def onm(c, userdata, msg):
    m = msg.payload.decode()
    print(m)
    if m.startswith("temperaturetoset"):
        parse_temp = m.split(" ")[1]
        temp_tresh = int(parse_temp)
        print(temp_tresh)
        heating_as_thread = Thread(target=tmp_reading2, args=[temp_tresh])
        heating_as_thread.daemon = True
        heating_as_thread.start()

    elif m == 'on':
        GPIO.output(led_device, GPIO.HIGH)
    elif m == 'off':
        GPIO.output(led_device, GPIO.LOW)

# run temperature reading on separate thread to enable heating controller
def tmp_reading2(arg1):
    try:
        while True:
            max_temp = int(arg1)

            t_byte = dev_pi.i2c_read_byte_data(dev_tmp, 0)
            t_word = dev_pi.i2c_read_word_data(dev_tmp, 0)
            l4b = ( t_word & 0b1111000000000000)>>12
            temperature = ((t_byte<<4) | l4b) * 0.0625
            temp_int = int(temperature)

            if temp_int <= max_temp:
                GPIO.output(led_heater, GPIO.HIGH)
            else:
                GPIO.output(led_heater, GPIO.LOW)
            time.sleep(heater_delay)
    except KeyboardInterrupt:
        print("Exitting")

# function to detect interrupt event.
def my_callback(channel):
    print("Event detected on pir sensor")
    take_snap()

# function to take a snapshot and save in specific folder.
# date_string is used to take a picture and add current date as a name to prevent image duplication.
def take_snap():
    print("Taking snap\n")
    date_string = time.strftime("%m-%d-%H-%M-%S")
    path        = '/home/pi/Desktop/Camera_test_python/pictures/'
    date        = 'image'+date_string
    ext         = '.jpg'
    full_path   = path+date+ext

    # save camera picture locally and pass location to store2bucket function
    camera.capture(full_path)

    # create new thread
    try:
        thread.start_new_thread(store_to_bucket, (full_path, date,))
    except:
        print("Error: unable to start thread")

# setup interrupt service routine when pir sensor state changed detected.
GPIO.add_event_detect(pir_sensor, GPIO.FALLING, callback=my_callback)

c.connect(hostName.read(), 8883)
sleep(2)

c.loop_start()
c.on_connect = onc
c.on_message = onm

# start temperature read thread
background_thread = Thread(target=tmp_reading, args=())
background_thread.daemon = True
background_thread.start()

# main function
try:

    while True:
        # run this loop forever
        sleep(1)

# if CTRL-C is pressed the main loop will break.
except KeyboardInterrupt:
    print("Exitting")

finally:
    GPIO.remove_event_detect(pir_sensor)    # turn off event detect interrupt
    GPIO.cleanup()                          # reset ports
    c.loop_stop()                           # start connection loop
    c.disconnect()
    r = dev_pi.i2c_close(dev_tmp)           # close i2c devices
    print("Connection terminated")
    mylcd.lcd_clear()
