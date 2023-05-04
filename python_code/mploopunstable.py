'''
This script is made to be ran during startup of the pi. It has multiple runnings modes, which can be adjusted manually in the last section. It initiates a csv file and, when active, regularly polls each sensor and write the measurements to the csv. When it gets an 'off' signal, it saves the csv file and ends the script. After turning off, it must be restarted manually, and it will begin a new csv.
'''

import Adafruit_DHT
import automationhat
import time
import multiprocessing as mp
import random
import numpy as np
import shutil
from functions import *
from getozone import *
from getpm import *
from getvoc import *
from getammonia import *
automationhat.enable_auto_lights(False) #gives us manual control over all the lights

timestamp = time.strftime("%b%d", time.localtime()) + '-' + time.strftime("%H%M", time.localtime())
trynumber = 1
for i in range(10): #if you somehow are trying to save make than 10 files a minute, something is wrong!
    path = str(timestamp + 'data-' + str(trynumber) + '.csv')
    try:
        file = open('/home/pi/newproject/V8/backups/' + path, 'x') #the pi's directory is hard-coded here, currently the backup of version 8
        file.write('time, temperature, humidity, pm25, pm10, ozone, V-ozone, voc, V-voc, ammonia, V-ammonia \n') #put your measurements here
        file.flush()
        file.close()
        break
    except FileExistsError:
        trynumber += 1

def mainloop(mode, start, tout):  #starts 3 processes that run at the same time, and keeps each one running until they all finish their functions. It then joins each processe's states, prints, and shuts down the whole script. 
    with mp.Manager() as manager:
        sample = manager.dict({'temp': [], 'humidity': [], 'pm25': [], 'pm10': [], 'ozone': [], 'V-ozone': [], 'voc': [],'V-voc': [], 'ammonia': [], 'V-ammonia': []}) #put your measurements here again
        gotime = mp.Value('i', start)
        p1 = mp.Process(target = sensorpoll, args = (sample, gotime))
        p2 = mp.Process(target = recorder, args = (sample, gotime))
        p3 = mp.Process(target = control, args = (gotime, mode, tout))      
        automationhat.light.comms.on() #blue light means were processing
        p1.start()
        p2.start()
        p3.start()
        p1.join()
        p2.join()
        p3.join()
        print('no processes running')
        
def sensorpoll(log, signal): #this loops through the following functions until a different process switches the global signal.value to 0
    while True:
        if signal.value != 0: #if signal is 1, print and go into the next loop
            print('starting to poll')
        while signal.value != 0: #every 0.05 seconds, run the functions poll each sensor. While some sensors' firmware updates their reading slower than 0.05 seconds, polling the current measurement happens independently
            readings = log
            if signal.value == 2: #dont stack up infinite data while in standby, keep sensors going but the log clean
                readings['pm25'], readings['pm10'], readings['ozone'], readings['V-ozone'], readings ['voc'], readings['V-voc'] = [], [], [], [], [], []
            pm25, pm10 = getpm()
            ozone = getozone()
            voc = getvoc()['methanol']
            ammonia = getammonia()
            readings['pm25'] += [pm25]
            readings['pm10'] += [pm10]
            readings['ozone'] += [ozone]
            readings['V-ozone'] += [automationhat.analog.three.read()]
            readings['voc'] += [voc]
            readings['V-voc'] += [automationhat.analog.two.read()]
            readings['ammonia'] += [ammonia]
            readings['V-ammonia'] += [automationhat.analog.one.read()]
            log = readings
            automationhat.light.power.on() #fast blinking green light means we are polling and the sensors are running and good
            time.sleep(0.05)
            automationhat.light.power.off()
        if signal.value == 0:
            break
    print('polling stopped')
            
def recorder(log, signal): #this function, when active, collects a measurement from the sensors and writes it in the file every 1.5 seconds. 
    firstrun = 1
    print('starting to record')
    if signal.value != 0:
        print('starting to record')
    while True:
        if signal.value == 1:
            loopstart = time.time()
            if firstrun == 1:
                starttime = time.time()
                firstrun = 0
            readings = log
            t = round((time.time() - starttime), 2)
            hum, temp = Adafruit_DHT.read_retry(Adafruit_DHT.DHT22, 14, 10, 0.01)
            hum, temp = round(hum, 1), round(temp, 1)
            # the measurement for each 1.5 second interval is an average of any 0.05-interval recordings from the sensor polling process
            recording = [t, temp, hum, round(np.mean(readings['pm25']), 1), round(np.mean(readings['pm10']), 1), round(np.mean(readings['ozone']), 3), round(np.mean(readings['V-ozone']), 3), round(np.mean(readings['voc']), 3), round(np.mean(readings['V-voc']), 3), round(np.mean(readings['ammonia']), 3), round(np.mean(readings['V-ammonia']), 3)] 
            print(recording)
            print(len(readings['pm25']), len(readings['ozone'])) #prints each measurement and the number of polls it averaged from
            file = open('/home/pi/newproject/V8/backups/' + path, 'a')
            file.write(', '.join([str(x) for x in recording]) + '\n')
            file.flush()
            file.close()
            # reset the polling log for the other process
            readings['pm25'], readings['pm10'], readings['ozone'], readings['V-ozone'], readings['voc'], readings['V-voc'], readings['ammonia'], readings['V-ammonia'] = [], [], [], [], [], [], [], []

            if (time.time() - loopstart) <= 1.5:
                automationhat.light.warn.on()
                time.sleep(1.5 - (time.time() - loopstart))

        if signal.value == 2:
            print('standby')
            time.sleep(1)
        if signal.value == 0:
            #breaks the standby/measuring loop, and the function prints and then ends.
            break
    print('recording stopped')

#controls other processes by changing signal, has different operation modes
def control(signal, mode, timeout):
    starttime = time.time()
    if mode == 'goseconds': #go for the designated number of seconds, reseting signal to 1 a few times in case usb was replaced (creates a polling error which forces active recording loops into standby)
        signal.value = 1
        print('going for x seconds')
        time.sleep(timeout/3)
        signal.value = 1
        time.sleep(timeout/3)
        signal.value = 1
    
    elif mode == 'toggle': #starts in standby, button press switches between on and standby, holding the button for 3 shuts down
        # in headless mode, I wired from a 5v power pin, through a button on a breadboard, to "input 1" on the automation hat. 
        # on the drone, Professor Frey would configure a wire from the drone that gives an electrical signal with a remote-control button press. This would plug directly into "input 1"
        signal.value = 2
        last = 0
        lasttime = time.time()
        while ((time.time() - starttime) < timeout):
            input = automationhat.input.one.read()
            if input == 1:
                if last == 0:
                    print('button!')
                    if signal.value == 1:
                        signal.value = 2
                    elif signal.value == 2:
                        signal.value = 1
                    print('you are now in setting: ', signal.value)
                if last == 1:
                    if (time.time() - lasttime) >= 3:
                        break
                last = 1
            else:
                lasttime = time.time()
                last = 0
            time.sleep(0.05)
    
    elif mode == 'marker': #starts in standby, button press starts the processes, subsequent presses writes a 'mark' line in the csv, holding the button for 3 shuts down
        # in headless mode, I wired from a 5v power pin, through a button on a breadboard, to "input 1" on the automation hat. 
        # on the drone, Professor Frey would configure a wire from the drone that gives an electrical signal with a remote-control button press. This would plug directly into "input 1"
        # for trials and drone flights, the pi was in this mode. Mark at takeoff and landing times to map on the drone's altitude readings.
        signal.value = 2
        last = 0
        lasttime = time.time()
        while ((time.time() - starttime) < timeout):
            input = automationhat.input.one.read()
            if input == 1:
                if last == 0:
                    signal.value = 1
                    print('button!')
                    try:
                        file = open('/home/pi/newproject/V8/backups/' + path, 'a')
                        file.write('marked \n')
                        file.flush()
                        file.close()
                        print('mark')
                    except:
                        print('marker didnt work')

                if last == 1:
                    if (time.time() - lasttime) >= 5:
                        break
                last = 1
            else:
                lasttime = time.time()
                last = 0
            time.sleep(0.05)
            
    print('initiating shutdown')
    signal.value = 0    

#after defining all those functions and loops, finally run the mainloop function in marker mode, starting in standby mode, timing out after 20 minutes
mainloop('marker', 2, 1200)

try:
    shutil.copy('/home/pi/newproject/V8/backups/' + path, '/media/pi/ClickUSB/' + path)
except:
    pass

automationhat.light.power.off()
automationhat.light.warn.off()
automationhat.light.comms.off()




