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
            readings['pm25'] += [pm25]
            readings['pm10'] += [pm10]
            readings['ozone'] += [ozone]
            readings['V-ozone'] += [automationhat.analog.three.read()]
            readings['voc'] += [voc]
            readings['V-voc'] += [automationhat.analog.two.read()]
            log = readings
            automationhat.light.power.on() #blinking green light means we are polling
            time.sleep(0.05)
            automationhat.light.power.off()
        if signal.value == 0:
            break
    print('polling stopped')