from classozone import *
import time

mq131 = MQ131();
def getozone():
    perc = mq131.MQpercentage()
    return perc["gasozone"]
#print(getozone())

def testloop():
    for i in range(20):
        print(getozone(), ' ppb ozone')
        print(automationhat.analog.three.read())
        time.sleep(1)

#testloop()