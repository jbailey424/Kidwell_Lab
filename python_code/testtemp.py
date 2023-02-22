import Adafruit_DHT
import automationhat
import time
read = 1
while read == 1:
    hum, temp = Adafruit_DHT.read(Adafruit_DHT.DHT22, 14)
    if (hum != None) and (temp != None):
        print(round(hum, 2), round(temp, 2))
    else:
        print(hum, temp)
    time.sleep(0)


