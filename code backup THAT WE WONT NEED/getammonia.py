from classammonia import *
import time

mq137 = MQ137();
def getammonia():
    perc = mq137.MQpercentage()
    return perc["gasammonia"]

#print(getvoc())

def testloop():
    for i in range(15):
        print(getammonia())
        time.sleep(1)

#testloop()