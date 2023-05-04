'''
This file implements functions for polling the MQ138 sensor and turning the class function output into measurements.
'''

from classvoc import *
import time
import automationhat
#(automationhat.analog.two.read())
mq138 = MQ138();
def getvoc():
    perc = mq138.MQpercentage()
    return perc

#print(mq138.MQread())
#print(getvoc()['formaldehyde'])
def getraw():
    return mq138.MQread()

def testloop():
    for i in range(20):
        print(getvoc()['methanol'])
        print(automationhat.analog.two.read())
        time.sleep(1)

#testloop()