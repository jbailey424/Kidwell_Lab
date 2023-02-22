from classpm import *
import time

sensor = SDS011("/dev/ttyUSB0")
def getpm():
    pm25, pm10 = sensor.query()
    return pm25, pm10

#print(getpm())

def testloop():
    for i in range(10):
        print(getpm())
        time.sleep(1)

#testloop()