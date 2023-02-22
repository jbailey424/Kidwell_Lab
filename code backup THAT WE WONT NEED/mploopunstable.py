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
for i in range(10):
    path = str(timestamp + 'data-' + str(trynumber) + '.csv')
    try:
        file = open('/home/pi/newproject/V8/backups/' + path, 'x')
        file.write('time, temperature, humidity, pm25, pm10, ozone, V-ozone, voc, V-voc, ammonia, V-ammonia \n')
        file.flush()
        file.close()
        break
    except FileExistsError:
        trynumber += 1

def mainloop(mode, start, tout): 
    with mp.Manager() as manager:
        sample = manager.dict({'temp': [], 'humidity': [], 'pm25': [], 'pm10': [], 'ozone': [], 'V-ozone': [], 'voc': [],'V-voc': [], 'ammonia': [], 'V-ammonia': []})
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
        
def sensorpoll(log, signal):
    while True:
        if signal.value != 0:
            print('starting to poll') #at the start print you're going
        while signal.value != 0: #go into operating loop
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
            automationhat.light.power.on() #blinking green light means we are polling
            time.sleep(0.05)
            automationhat.light.power.off()
        if signal.value == 0:
            break
    print('polling stopped')
            
def recorder(log, signal):
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
            recording = [t, temp, hum, round(np.mean(readings['pm25']), 1), round(np.mean(readings['pm10']), 1), round(np.mean(readings['ozone']), 3), round(np.mean(readings['V-ozone']), 3), round(np.mean(readings['voc']), 3), round(np.mean(readings['V-voc']), 3), round(np.mean(readings['ammonia']), 3), round(np.mean(readings['V-ammonia']), 3)]
            print(recording)
            print(len(readings['pm25']), len(readings['ozone']))
            file = open('/home/pi/newproject/V8/backups/' + path, 'a')
            file.write(', '.join([str(x) for x in recording]) + '\n')
            file.flush()
            file.close()
            
            readings['pm25'], readings['pm10'], readings['ozone'], readings['V-ozone'], readings['voc'], readings['V-voc'], readings['ammonia'], readings['V-ammonia'] = [], [], [], [], [], [], [], []

            if (time.time() - loopstart) <= 1.5:
                automationhat.light.warn.on()
                time.sleep(1.5 - (time.time() - loopstart))

        if signal.value == 2:
            print('standby')
            time.sleep(1)
        if signal.value == 0:
            break
    print('recording stopped')

#controls other processes by changing signal, has different operation modes
def control(signal, mode, timeout):
    starttime = time.time()
    if mode == 'goseconds': #go for the designated number of seconds, reseting signal to 1 a few times in case usb was replaced
        signal.value = 1
        print('going for x seconds')
        time.sleep(timeout/3)
        signal.value = 1
        time.sleep(timeout/3)
        signal.value = 1
    
    elif mode == 'toggle': #starts in standby, button switches between on and standby, holding for 3 shuts down
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
    
    elif mode == 'marker': #starts in standby, first button starts, subsequent buttons writes a mark in the data, holding turns off
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

mainloop('marker', 2, 1200)

try:
    shutil.copy('/home/pi/newproject/V8/backups/' + path, '/media/pi/ClickUSB/' + path)
except:
    pass

automationhat.light.power.off()
automationhat.light.warn.off()
automationhat.light.comms.off()




